import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import csv
import requests
from archive.prompts import get_structuring_prompt
from archive.config import Config

# --- Prompt & Schema ---
def get_structured_json(transcript, user_id="default_user"):
    prompt = get_structuring_prompt(transcript)
    try:
        # OpenRouter API call
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
                    {"role": "system", "content": "You structure transcripts into valid JSON. Always respond with properly formatted JSON only."},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.text}")
        
        json_text = response.json()["choices"][0]["message"]["content"].strip()
        
        # Remove markdown code block markers if present
        if json_text.startswith("```"):
            # Split by ``` and take the content between the markers
            parts = json_text.split("```")
            if len(parts) >= 3:  # Proper code block with start and end markers
                json_text = parts[1]
            else:
                json_text = parts[-1]  # Take the last part if splitting is weird
                
            # Remove the "json" language identifier if present
            if json_text.startswith("json"):
                json_text = json_text[4:].strip()
        
        # Add debug logging
        print("Cleaned JSON text:", json_text[:200] + "..." if len(json_text) > 200 else json_text)
        
        try:
            parsed_json = json.loads(json_text)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Problematic JSON text: {json_text}")
            raise
            
    except Exception as e:
        print(f"Error in get_structured_json: {str(e)}")
        raise

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_data (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            para_type TEXT NOT NULL,
            para_status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            last_modified TIMESTAMP NOT NULL
        );
    """)
    conn.commit()
    return conn, cursor

# --- Database Insertion ---
def insert_session_data(cursor, conn, data):
    session_id = data["session"]["session_id"]
    cursor.execute(
        """
        INSERT OR REPLACE INTO session_data (id, data)
        VALUES (?, ?)
        """,
        (session_id, json.dumps(data))
    )
    conn.commit()
    print("Inserted session data with session_id:", session_id)

# --- CSV Handling ---
def load_transcripts_from_csv(filename=None):
    """Load transcripts from CSV file."""
    if filename is None:
        filename = Config.TRANSCRIPTS_PATH
    
    transcripts = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            transcripts.append(row)
    
    print(f"Loaded {len(transcripts)} transcripts from {filename}")
    return transcripts

def save_json_output(data, transcript_id):
    """Save JSON output to file."""
    output_path = Path(Config.JSON_OUTPUT_DIR) / f"{transcript_id}.json"
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON output to {output_path}")

def process_transcripts():
    """Process the transcript from the configured CSV file."""
    from second_brain.utils.config import Config
    
    # Load transcript from CSV
    try:
        print(f"Loading transcript from: {Config.TRANSCRIPTS_PATH}")
        with open(Config.TRANSCRIPTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            transcript = next(reader)  # Just get the first row
            
        print(f"Loaded transcript from {Config.TRANSCRIPTS_PATH}")
        
        # Extract transcript details
        transcript_id = transcript.get('transcript_id')
        user_id = transcript.get('user_id', 'default_user')
        content = transcript.get('content', '')
        
        # Process the transcript
        structured_json = get_structured_json(content, user_id)
        
        # Verify structured_json is a dictionary
        if isinstance(structured_json, str):
            try:
                structured_json = json.loads(structured_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                # Log the error and possibly the JSON string for debugging
                return None
        
        # Save JSON to file
        json_output_path = os.path.join(Config.JSON_OUTPUT_DIR, f"{transcript_id}.json")
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_json, f, indent=2)
        
        print(f"Processed transcript {transcript_id}")
        
        # Return the structured JSON for further processing
        return structured_json
        
    except Exception as e:
        print(f"Error processing transcript: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# --- Main Pipeline ---
def main():
    # Validate configuration
    Config.initialize()
    
    # Initialize the local SQLite database
    conn, cursor = init_db()

    try:
        # Load and process transcripts
        transcripts = load_transcripts_from_csv()
        process_transcripts()
        
        # Note: We've removed the markdown conversion step
        print("Processing complete! JSON files saved to the output directory.")
        
    finally:
        # Ensure database connection is closed
        conn.close()

if __name__ == "__main__":
    main()