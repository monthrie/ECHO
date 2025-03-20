import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import csv
import requests  # We'll need this for OpenRouter
from prompts import get_structuring_prompt
from json_to_obsidian import convert_all_json_files

# Load environment variables
load_dotenv()

# --- Configuration ---
class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    DB_PATH = os.getenv("DB_PATH", "second_brain.db")
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", 
        "/Users/wilmon/Documents/projects/FTFM/notes/")
    MODEL = os.getenv("MODEL", "deepseek/deepseek-chat:free")  # changed default
    JSON_OUTPUT_DIR = "output_jsons"  # New setting for JSON output
    
    @classmethod
    def validate(cls):
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        if not Path(cls.OBSIDIAN_VAULT_PATH).exists():
            raise ValueError(f"Obsidian vault path does not exist: {cls.OBSIDIAN_VAULT_PATH}")
        # Create JSON output directory if it doesn't exist
        Path(cls.JSON_OUTPUT_DIR).mkdir(exist_ok=True)

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
                    {"role": "system", "content": "You structure transcripts into JSON."},
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
            json_text = json_text.split("```")[1]
            # Remove the "json" language identifier if present
            if json_text.startswith("json"):
                json_text = json_text[4:].strip()
        
        # Add debug logging
        print("Cleaned JSON text:", json_text)
        
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

# SQLite settings: a local file "second_brain.db"
DB_PATH = "second_brain.db"

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
def load_transcripts_from_csv(filename="transcripts.csv"):
    """Load transcripts from a CSV file."""
    transcripts = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            transcripts.append(row)
    
    print(f"Loaded {len(transcripts)} transcripts from {filename}")
    return transcripts

def save_json_output(data, transcript_id):
    """Save the structured JSON to a file for inspection."""
    output_path = Path(Config.JSON_OUTPUT_DIR) / f"{transcript_id}.json"
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved JSON output to {output_path}")

def process_transcripts(transcripts, conn, cursor):
    """Process multiple transcripts and store them in the database."""
    for transcript in transcripts:
        print(f"\nProcessing transcript {transcript['transcript_id']}...")
        structured_data = get_structured_json(
            transcript['content'], 
            user_id=transcript['user_id']
        )
        
        # Save JSON to file for inspection
        save_json_output(structured_data, transcript['transcript_id'])
        
        # Store in database
        insert_session_data(cursor, conn, structured_data)
        
        # Print a sample of the structured data
        print("\nExtracted records:")
        for record in structured_data['records']:
            print(f"- Type: {record['type']}")
            print(f"  Content: {record['content'][:100]}...")

# --- Main Pipeline ---
def main():
    # Validate configuration
    Config.validate()
    
    # Initialize the local SQLite database
    conn, cursor = init_db()

    try:
        # Load and process transcripts
        transcripts = load_transcripts_from_csv()
        process_transcripts(transcripts, conn, cursor)
        
        # Convert JSON files to markdown (stored in markdown_output directory)
        convert_all_json_files(Config)
        
    finally:
        # Ensure database connection is closed
        conn.close()

if __name__ == "__main__":
    main()