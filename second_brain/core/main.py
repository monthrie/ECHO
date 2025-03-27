import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import csv
import requests
from second_brain.prompts.prompts import get_structuring_prompt
from second_brain.utils.config import Config

# --- Prompt & Schema ---
def get_structured_json(transcript, user_id="default_user", tracer=None):
    prompt = get_structuring_prompt(transcript)
    try:
        # Prepare API call payload
        payload = {
            "model": Config.MODEL,
            "messages": [
                {"role": "system", "content": "You structure transcripts into valid JSON. Always respond with properly formatted JSON only."},
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add tracing metadata
        metadata = {
            "stage": "transcript_to_json",
            "transcript_length": len(transcript),
            "model": Config.MODEL
        }
        
        # OpenRouter API call
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "Content-Type": "application/json"
            },
            json=payload
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
        
        # Trace the API call if tracer is provided
        if tracer:
            tracer.trace_openrouter_call(
                "transcript_to_json", 
                prompt, 
                json_text, 
                metadata
            )
        
        # Parse the JSON
        return json.loads(json_text)
    except Exception as e:
        print(f"Error in get_structured_json: {str(e)}")
        # Return a basic structure if JSON parsing fails
        return {"error": str(e), "partial_text": json_text[:500] if 'json_text' in locals() else "No response"}

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

def process_transcripts(tracer=None):
    """Process transcript files and convert to structured JSON."""
    try:
        # Read the transcript file
        transcript_path = Config.TRANSCRIPTS_PATH
        print(f"Reading transcript from: {transcript_path}")
        
        with open(transcript_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if present
            header = next(reader, None)
            # Get first row of content
            first_row = next(reader, None)
            
            if first_row:
                # Extract content (assuming it's in the last column)
                transcript_content = first_row[-1]
                print(f"Extracted transcript content ({len(transcript_content)} chars)")
                
                # Get structured JSON
                structured_json = get_structured_json(transcript_content, tracer=tracer)
                
                # Save to file
                json_output_path = Path(Config.JSON_OUTPUT_DIR) / "structured.json"
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    if isinstance(structured_json, str):
                        f.write(structured_json)
                    else:
                        json.dump(structured_json, f, indent=2)
                
                print(f"Saved structured JSON to {json_output_path}")
                return structured_json
            else:
                print("No content found in transcript file")
                return None
    except Exception as e:
        print(f"Error processing transcript: {str(e)}")
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