import os
import csv
import json
import glob
import uuid
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
import yaml
import re
from dotenv import load_dotenv
from update_prompts import get_integration_decision_prompt, get_content_update_prompt, get_summary_prompt
from config import Config

# Setup logging
logger = Config.setup_logging()
logger.info(f"OBSIDIAN_VAULT_PATH: {Config.OBSIDIAN_VAULT_PATH}")
logger.info(f"Current working directory: {os.getcwd()}")


# --- File Indexing ---

def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    # Look for YAML frontmatter between --- markers
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return {}
    return {}

def extract_tags_from_frontmatter(frontmatter):
    """Extract tags from frontmatter."""
    if not frontmatter or 'tags' not in frontmatter:
        return []
    
    tags = frontmatter['tags']
    if isinstance(tags, list):
        return tags
    elif isinstance(tags, str):
        return [tag.strip() for tag in tags.split(',')]
    return []

def get_para_type_from_path(file_path):
    """Determine PARA type from file path."""
    path_parts = Path(file_path).parts
    if len(path_parts) >= 1:
        if path_parts[0].lower() == 'projects':
            return 'project'
        elif path_parts[0].lower() == 'areas':
            return 'area'
        elif path_parts[0].lower() == 'resources':
            return 'resource'
        elif path_parts[0].lower() == 'archives':
            return 'archive'
    return 'unknown'

def generate_file_summary(file_path, content):
    """Generate a summary of file content using the LLM."""
    prompt = get_summary_prompt(content)
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "Content-Type": "application/json"
            },
            json={
                "model": Config.MODEL,
                "messages": [
                    {"role": "system", "content": "You summarize markdown content concisely."},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if response.status_code != 200:
            print(f"Error generating summary: {response.text}")
            return "Error generating summary"
        
        summary = response.json()["choices"][0]["message"]["content"].strip()
        return summary
        
    except Exception as e:
        print(f"Error in generate_file_summary: {str(e)}")
        return "Error generating summary"

def extract_file_metadata(file_path):
    """Extract metadata from a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        frontmatter = extract_frontmatter(content)
        
        # Extract tags from frontmatter
        tags = extract_tags_from_frontmatter(frontmatter)
        tags_str = ','.join(tags)
        
        # Determine PARA type from path
        para_type = get_para_type_from_path(str(file_path))
        
        # Generate summary
        summary = generate_file_summary(file_path, content)
        
        # Extract record IDs if present
        record_ids = frontmatter.get('record_ids', '')
        if isinstance(record_ids, list):
            record_ids = ','.join(record_ids)
        
        return summary, tags_str, para_type, record_ids
    
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return "", "", "unknown", ""

def build_file_index():
    """Build or update the file index for all markdown files in the vault."""
    # Connect to SQLite database
    db_path = Path(Config.DB_PATH)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_index (
        file_path TEXT PRIMARY KEY,
        summary TEXT,
        tags TEXT,
        para_type TEXT,
        last_modified TEXT,
        record_ids TEXT
    )
    ''')
    
    # Find all markdown files in vault
    vault_path = Path(Config.OBSIDIAN_VAULT_PATH)
    print(f"Config.OBSIDIAN_VAULT_PATH = {Config.OBSIDIAN_VAULT_PATH}")
    print(f"Environment variable value: {os.getenv('OBSIDIAN_VAULT_PATH')}")
    print(f"Searching for markdown files in: {vault_path.absolute()}")
    md_files = list(vault_path.glob('**/*.md'))
    print(f"Found {len(md_files)} markdown files")
    
    # Process each markdown file
    updated_count = 0
    for md_file in md_files:
        rel_path = md_file.relative_to(vault_path)
        file_path = str(rel_path)
        
        # Get file modification time
        last_modified = datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
        
        # Check if file exists in database and get its last_modified time
        cursor.execute("SELECT last_modified FROM file_index WHERE file_path = ?", (file_path,))
        result = cursor.fetchone()
        
        # Only update if file is new or modified
        if not result or result[0] != last_modified:
            # Extract metadata
            summary, tags, para_type, record_ids = extract_file_metadata(md_file)
            
            # Insert or update the record
            cursor.execute('''
            INSERT OR REPLACE INTO file_index 
            (file_path, summary, tags, para_type, last_modified, record_ids)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_path, summary, tags, para_type, last_modified, record_ids))
            
            updated_count += 1
    
    # Commit changes and close connection
    conn.commit()
    
    # Get all entries to return
    cursor.execute("SELECT * FROM file_index")
    columns = [description[0] for description in cursor.description]
    entries = {}
    for row in cursor.fetchall():
        entry = dict(zip(columns, row))
        entries[entry['file_path']] = entry
    
    conn.close()
    
    print(f"Updated file index with {updated_count} entries")
    return entries

def get_file_index():
    """Get the current file index from the database."""
    db_path = Path(Config.DB_PATH)
    
    # If database doesn't exist, build it
    if not db_path.exists():
        return build_file_index()
    
    # Connect to database and get all entries
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM file_index")
    entries = {}
    for row in cursor:
        entry = dict(row)
        entries[entry['file_path']] = entry
    
    conn.close()
    return entries

def find_matching_files(record):
    """Find existing files that might match a given record."""
    # Get file index from database
    file_index = get_file_index()
    
    matches = []
    
    for file_path, row in file_index.items():
        score = 0
        
        # Match by PARA type
        if record['para_type'] == row['para_type']:
            score += 3
        
        # Check if record's parent_entity is in the file path
        parent_entity = record.get('details', {}).get('parent_entity', '')
        if parent_entity and parent_entity.lower() in file_path.lower():
            score += 5
        
        # Match by tags
        record_tags = set(record.get('tags', []))
        file_tags = set(row['tags'].split(',') if row['tags'] else [])
        tag_matches = record_tags.intersection(file_tags)
        score += len(tag_matches) * 2
        
        # Simple text matching
        record_title = record.get('details', {}).get('title', '').lower()
        record_content = record.get('content', '').lower()
        summary = row['summary'].lower() if row['summary'] else ''
        
        if record_title and record_title in summary:
            score += 4
            
        # Add as a potential match if score is above threshold
        if score >= 3:
            matches.append({
                'file_path': file_path,
                'summary': row['summary'],
                'score': score,
                'tags': row['tags']
            })
    
    # Sort matches by score (highest first)
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:5]  # Return top 5 matches

# --- Integration Decision ---

def decide_integration_action(record, matching_files):
    """Use LLM to decide how to integrate the record with existing files."""
    prompt = get_integration_decision_prompt(record, matching_files)
    print("\n--- INTEGRATION DECISION DEBUGGING ---")
    print(f"Record: {record.get('details', {}).get('title', 'Untitled')}")
    print(f"Matching files count: {len(matching_files)}")
    if matching_files:
        print(f"First matching file: {matching_files[0]}")
    
    try:
        print("Sending request to OpenRouter API...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "Content-Type": "application/json"
            },
            json={
                "model": Config.MODEL,
                "messages": [
                    {"role": "system", "content": "You are a knowledge management assistant."},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        print(f"API response status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error deciding integration: {response.text}")
            return {"action": "create", "files": [], "reason": "API error, defaulting to create new file"}
        
        response_json = response.json()
        print(f"API response JSON: {response_json}")
        
        decision_text = response_json["choices"][0]["message"]["content"].strip()
        print(f"Raw decision text: {decision_text}")
        
        # Parse the decision
        action = "create"  # Default
        files = []
        reason = ""
        
        print("Parsing decision text...")
        
        # Look for decision indicators
        if "DECISION: UPDATE" in decision_text:
            action = "update"
            print("Found UPDATE decision")
        elif "DECISION: MERGE" in decision_text:
            action = "merge"
            print("Found MERGE decision")
        elif "DECISION: CREATE" in decision_text:
            action = "create"
            print("Found CREATE decision")
        else:
            print(f"No clear decision found, defaulting to CREATE")
        
        # Extract file paths
        print("Extracting file paths...")
        file_section_match = re.search(r'FILE\(S\):\s*(.*?)(?:\n|$)', decision_text)
        if file_section_match:
            file_section = file_section_match.group(1).strip()
            print(f"File section found: '{file_section}'")
            
            if file_section and file_section.lower() != "none" and file_section != "-":
                # Split by commas or newlines with possible bullet points
                file_candidates = re.split(r',|\n-\s*', file_section)
                files = [f.strip() for f in file_candidates if f.strip()]
                print(f"Extracted file paths: {files}")
            else:
                print("No file paths specified")
        else:
            print("No FILE(S) section found")
        
        # Extract reason
        print("Extracting reason...")
        reason_match = re.search(r'REASON:\s*(.*?)(?:\n|$)', decision_text, re.DOTALL)
        if reason_match:
            reason = reason_match.group(1).strip()
            print(f"Reason found: '{reason}'")
        else:
            print("No REASON section found")
        
        result = {
            "action": action,
            "files": files,
            "reason": reason,
            "raw_decision": decision_text
        }
        
        print(f"Final decision: {result}")
        return result
        
    except Exception as e:
        import traceback
        print(f"Exception in decide_integration_action: {str(e)}")
        print(traceback.format_exc())
        return {"action": "create", "files": [], "reason": f"Error: {str(e)}, defaulting to create new file"}

# --- Content Integration ---

def update_existing_file(file_path, record):
    """Update an existing file with new content."""
    full_path = Path(Config.OBSIDIAN_VAULT_PATH) / file_path
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        prompt = get_content_update_prompt(existing_content, record)
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "Content-Type": "application/json"
            },
            json={
                "model": Config.MODEL,
                "messages": [
                    {"role": "system", "content": "You update markdown content with new information."},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if response.status_code != 200:
            print(f"Error updating file: {response.text}")
            return False
        
        updated_content = response.json()["choices"][0]["message"]["content"].strip()
        
        # Write updated content back to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        # Update the index entry to include this record ID
        update_index_record_id(file_path, record["record_id"])
        
        print(f"Updated file: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error in update_existing_file: {str(e)}")
        return False

def merge_files(file_paths, record):
    """Merge multiple files with new content."""
    # This would be a more complex implementation
    # For the POC, we'll just update the first file
    if file_paths:
        return update_existing_file(file_paths[0], record)
    return False

def update_index_record_id(file_path, record_id):
    """Update the index entry to add a record ID."""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    # Get current record_ids
    cursor.execute("SELECT record_ids FROM file_index WHERE file_path = ?", (file_path,))
    result = cursor.fetchone()
    
    if result:
        record_ids = result[0].split(',') if result[0] else []
        if record_id not in record_ids:
            record_ids.append(record_id)
            new_record_ids = ','.join(record_ids)
            
            # Update the record
            cursor.execute(
                "UPDATE file_index SET record_ids = ? WHERE file_path = ?", 
                (new_record_ids, file_path)
            )
            conn.commit()
            print(f"Updated record_ids for {file_path}")
    else:
        print(f"File {file_path} not found in index")
    
    conn.close()

# --- Main Process ---

def process_json_records():
    """Process JSON records and integrate them with existing files."""
    # Make sure index is up to date
    db_path = Path(Config.DB_PATH)
    if not db_path.exists():
        build_file_index()
    
    # Find all JSON files
    json_dir = Path(Config.JSON_OUTPUT_DIR)
    json_files = list(json_dir.glob('*.json'))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Process each record
            for record in data.get('records', []):
                # Find potential matching files
                matching_files = find_matching_files(record)
                
                # Decide how to integrate
                decision = decide_integration_action(record, matching_files)
                print(f"Decision for record '{record.get('details', {}).get('title', 'Untitled')}': {decision['action']}")
                
                # Integrate based on decision
                if decision['action'] == 'update':
                    update_existing_file(decision['files'][0], record)
                elif decision['action'] == 'merge':
                    merge_files(decision['files'], record)
                else:  # create
                    # This would use your existing file creation logic
                    # For POC, we'll just print a message
                    print(f"Would create new file for record: {record.get('details', {}).get('title', 'Untitled')}")
                    
                    # In a full implementation, you would:
                    # 1. Create the new file
                    # 2. Update the index with the new file info
                    
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")

# --- Command Line Interface ---

def main():
    """Main function to run the program."""
    Config.initialize()
    
    print("Second Brain AI - Smart Update System")
    print("1. Build/Update File Index")
    print("2. Process JSON Files for Smart Integration")
    print("3. Do Both")
    print("q. Quit")
    
    choice = input("Enter your choice: ")
    
    if choice == '1':
        build_file_index()
    elif choice == '2':
        process_json_records()
    elif choice == '3':
        build_file_index()
        process_json_records()
    elif choice.lower() == 'q':
        return
    else:
        print("Invalid choice")

def get_file_by_path(file_path):
    """Get file metadata by path."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM file_index WHERE file_path = ?", (file_path,))
    result = cursor.fetchone()
    
    conn.close()
    return dict(result) if result else None

def search_files(query, tags=None):
    """Search files by query and tags."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = "SELECT * FROM file_index WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (summary LIKE ? OR file_path LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    
    if tags:
        for tag in tags:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")
    
    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return results

if __name__ == "__main__":
    main()