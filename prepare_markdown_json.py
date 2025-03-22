import json
import os
import uuid
from pathlib import Path
from datetime import datetime
import requests
from config import Config

def get_blueprint_conversion_prompt(json_data):
    """
    Output JSON blueprints instead of markdown.
    Based on the sophisticated logic in conversion_prompt.py.
    """
    json_str = json.dumps(json_data, indent=2)
    
    prompt = f"""
# Instructions for Converting Second Brain JSON to Markdown Blueprints

## JSON Data to Convert
{json_str}

## Hierarchical Organization Requirements
1. Group ALL related notes under appropriate subdirectories
2. NEVER place notes directly in root PARA folders without a subdirectory
3. Files related to the same project, area, or topic MUST be placed in a dedicated subdirectory
4. Example hierarchy:
   - Projects/Investigation/Overview.md
   - Projects/Investigation/Plan.md
   - Projects/Investigation/MVP.md

## Directory Organization
- Projects must use: "Projects/<Project Name>/<filename>.md"
- Areas must use: "Areas/<Area Name>/<filename>.md"
- Resources must use: "Resources/<Topic Name>/<filename>.md"
- Archives must use: "Archives/<Original Category>/<filename>.md"

## Organizational Files
For any collection with multiple files, create:
1. A "Contents.md" file that serves as a Map of Contents (MOC)
2. A "Tasks.md" file if there are multiple tasks or action items

Example structure:
- Projects/Investigation/Contents.md
- Projects/Investigation/Tasks.md
- Projects/Investigation/Overview.md
- Projects/Investigation/Plan.md
- Projects/Investigation/MVP.md

## Naming and Formatting Requirements
1. Use descriptive, concise filenames with spaces between words
2. Ensure filenames match the content they contain
3. Structure content with appropriate headings, lists, and formatting
4. Preserve all important information from the original records

## Note Types and Content Structure

### Project Notes
For each project:
- Create a comprehensive main project note with overview, status, and key details
- Include "Related Notes" section with links
- Extract associated tasks into a checklist section or link to tasks file
- Add context about the project's purpose, goals, and timeline
- Include any dependencies or requirements

### Implementation/Technical Notes
For technical details:
- Create separate notes focusing on architecture and technical aspects
- Include diagrams for system relationships when appropriate
- Use code blocks with appropriate syntax highlighting
- Maintain technical accuracy while improving readability
- Link to relevant external resources or documentation

### Entity Notes
For important entities (people, concepts, organizations):
- Create dedicated notes for significant entities referenced across multiple records
- Describe relationships to projects and other entities
- Include relevant background information
- Establish bidirectional links to related notes

## Special Instructions
1. Preserve ALL detailed information while reorganizing presentation
2. For complex projects, suggest canvas files to visualize relationships
3. Include direct quotes or critical content verbatim to maintain accuracy
4. Look for narrative connections between JSON records and combine logically related content

## OUTPUT FORMAT
Instead of directly creating markdown files, you must output a JSON array of blueprint objects.
Each blueprint should have this structure:

{{
  "file_info": {{
    "directory": "The appropriate directory path (e.g., Projects/FTFM)",
    "filename": "A descriptive filename (e.g., Technical Architecture)",
    "record_id": "The original record_id from the source"
  }},
  "frontmatter": {{
    "tags": ["tag1", "tag2"],
    "record_ids": ["record_id1", "record_id2"],
    "goal": "The project goal (only for projects)"
  }},
  "content": {{
    "title": "The title for the note",
    "body": "The fully formatted markdown content (without the title or frontmatter)"
  }}
}}

Your response must be a valid JSON array of these blueprint objects, with no additional text or explanation.
"""
    return prompt

def convert_json_to_blueprints(json_data):
    """
    Use the LLM with our sophisticated conversion prompt to transform JSON data into markdown blueprints.
    """
    prompt = get_blueprint_conversion_prompt(json_data)
    
    try:
        # Make API call to OpenRouter
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
                    {"role": "system", "content": "You convert structured JSON data into markdown blueprints. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.text}")
        
        json_text = response.json()["choices"][0]["message"]["content"].strip()
        
        # Remove markdown code block markers if present
        if json_text.startswith("```"):
            parts = json_text.split("```")
            if len(parts) >= 3:  # Proper code block with start and end markers
                json_text = parts[1]
            else:
                json_text = parts[-1]  # Take the last part if splitting is weird
                
            # Remove the "json" language identifier if present
            if json_text.startswith("json"):
                json_text = json_text[4:].strip()
        
        # Parse the JSON response
        try:
            blueprints = json.loads(json_text)
            return blueprints
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Problematic JSON text: {json_text}")
            # Fall back to basic blueprints if parsing fails
            return create_basic_blueprints(json_data)
            
    except Exception as e:
        print(f"Error in convert_json_to_blueprints: {str(e)}")
        # Fall back to basic blueprints if API call fails
        return create_basic_blueprints(json_data)

def create_basic_blueprints(json_data):
    """
    Create basic blueprints without using LLM (fallback).
    """
    blueprints = []
    
    for record in json_data.get('records', []):
        # Extract record details
        title = record.get('details', {}).get('title', 'Untitled')
        content = record.get('content', '')
        tags = record.get('tags', [])
        para_type = record.get('para_type', 'resource')
        record_id = record.get('record_id', str(uuid.uuid4()))
        
        # Get parent entity if available
        parent_entity = record.get('details', {}).get('parent_entity', '')
        
        # Determine the appropriate directory based on PARA type
        if para_type == 'project':
            directory = 'Projects'
        elif para_type == 'area':
            directory = 'Areas'
        elif para_type == 'archive':
            directory = 'Archives'
        else:
            directory = 'Resources'
        
        # If parent entity exists, use it as a subdirectory
        if parent_entity:
            directory = f"{directory}/{parent_entity}"
        
        # Prepare the markdown blueprint
        blueprint = {
            "file_info": {
                "directory": directory,
                "filename": title,
                "record_id": record_id
            },
            "frontmatter": {
                "tags": tags,
                "record_ids": [record_id]
            },
            "content": {
                "title": title,
                "body": content
            }
        }
        
        # Add goal if available (only for projects)
        if para_type == 'project':
            project_meta = record.get('para_metadata', {}).get('project', {})
            if project_meta and 'goal' in project_meta:
                blueprint["frontmatter"]["goal"] = project_meta.get('goal')
        
        blueprints.append(blueprint)
    
    return blueprints

def process_json_to_blueprints(json_dir=None):
    """
    Process all JSON files in the specified directory and convert them to markdown blueprints
    using the sophisticated conversion logic from conversion_prompt.py.
    """
    if json_dir is None:
        json_dir = Config.JSON_OUTPUT_DIR
    
    json_dir = Path(json_dir)
    blueprint_dir = json_dir / "blueprints"
    blueprint_dir.mkdir(exist_ok=True)
    
    # Find all JSON files
    json_files = list(json_dir.glob('*.json'))
    print(f"Found {len(json_files)} JSON files to process")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            print(f"Converting {json_file.name} to blueprints...")
            blueprints = convert_json_to_blueprints(data)
            
            # Save blueprints to a new JSON file
            blueprint_file = blueprint_dir / f"{json_file.stem}_blueprint.json"
            with open(blueprint_file, 'w') as f:
                json.dump({"blueprints": blueprints}, f, indent=2)
            
            print(f"Created blueprint file: {blueprint_file}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
    
    return len(json_files)

if __name__ == "__main__":
    Config.initialize()
    num_processed = process_json_to_blueprints()
    print(f"Processed {num_processed} JSON files into markdown blueprints") 