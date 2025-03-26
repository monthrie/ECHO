import json
import os
import uuid
from pathlib import Path
from datetime import datetime
import requests
from archive.config import Config
from second_brain.prompts.blueprint_prompt import get_blueprint_conversion_prompt
import re

def convert_json_to_blueprints(json_data):
    """Convert JSON data to blueprints using LLM."""
    try:
        print(f"convert_json_to_blueprints received data of type: {type(json_data)}")
        
        # Prepare the prompt for the LLM
        prompt = get_blueprint_conversion_prompt(json_data)
        
        # Call the LLM API - use the same API endpoint and key as in main.py
        api_url = "https://openrouter.ai/api/v1/chat/completions"  # Hardcoded URL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8000"
        }
        
        payload = {
            "model": Config.MODEL,  # Use the same model attribute as in main.py
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that converts structured JSON data into markdown blueprint format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        print("Sending request to LLM API")
        response = requests.post(api_url, headers=headers, json=payload)
        
        # Log the response status and headers
        print(f"Response status code: {response.status_code}")
        
        # Save the raw response to a file for inspection
        with open("llm_response_raw.txt", "wb") as f:
            f.write(response.content)
        
        if response.status_code != 200:
            print(f"LLM API error: {response.status_code} - {response.text}")
            return create_basic_blueprints(json_data)
        
        # Parse the LLM response
        try:
            response_data = response.json()
            llm_response = response_data['choices'][0]['message']['content']
            
            # Save the raw LLM response to a file
            with open("llm_content_raw.txt", "w", encoding="utf-8") as f:
                f.write(llm_response)
            print(f"Saved raw LLM content ({len(llm_response)} chars) to llm_content_raw.txt")
            
            # Extract JSON from the LLM response
            print("Extracting blueprints from LLM response")
            cleaned_response = clean_json_string(llm_response)
            
            # Save the cleaned response to a file
            with open("llm_content_cleaned.txt", "w", encoding="utf-8") as f:
                f.write(cleaned_response)
            print(f"Saved cleaned LLM content ({len(cleaned_response)} chars) to llm_content_cleaned.txt")
            
            try:
                blueprints = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Error position: {e.pos}")
                print(f"Cleaned response excerpt around error: {cleaned_response[max(0, e.pos-50):min(len(cleaned_response), e.pos+50)]}")
                raise
            
            # Ensure we have a list of blueprints
            if not isinstance(blueprints, list):
                print(f"LLM returned non-list blueprints: {type(blueprints)}")
                if isinstance(blueprints, dict):
                    # If it's a single blueprint as a dict, wrap it in a list
                    blueprints = [blueprints]
                else:
                    # If it's something else, fall back to basic blueprints
                    return create_basic_blueprints(json_data)
            
            print(f"Successfully created {len(blueprints)} blueprints using LLM")
            return blueprints
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Error position: {e.pos}")
            print(f"Response excerpt around error: {response.text[max(0, e.pos-50):min(len(response.text), e.pos+50)]}")
            raise
            
    except Exception as e:
        print(f"Error in convert_json_to_blueprints: {e}")
        raise

def create_basic_blueprints(json_data):
    """
    Create basic blueprints without using LLM (fallback).
    """
    # Add logging to understand what's being received
    print(f"create_basic_blueprints received data of type: {type(json_data)}")
    if isinstance(json_data, str):
        print(f"WARNING: Expected dict but received string in create_basic_blueprints: {json_data[:100]}...")
        try:
            json_data = json.loads(json_data)
            print("Successfully converted string to dict in create_basic_blueprints")
        except json.JSONDecodeError:
            print("Failed to parse string as JSON in create_basic_blueprints")
            # Create a minimal structure to prevent errors
            return [{"file_info": {"directory": "Resources", "filename": "Error", "record_id": str(uuid.uuid4())},
                    "frontmatter": {"tags": ["error"], "record_ids": []},
                    "content": {"title": "Error", "body": "Failed to process content"}}]
    
    # Check if json_data has the expected structure
    if not isinstance(json_data, dict) or 'records' not in json_data:
        print(f"Invalid json_data structure in create_basic_blueprints: {type(json_data)}, keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'N/A'}")
        # Create a minimal structure to prevent errors
        return [{"file_info": {"directory": "Resources", "filename": "Error", "record_id": str(uuid.uuid4())},
                "frontmatter": {"tags": ["error"], "record_ids": []},
                "content": {"title": "Error", "body": "Invalid data structure"}}]
    
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

def process_json_to_blueprints(structured_json):
    """Process structured JSON into blueprint JSON files."""
    from second_brain.utils.config import Config
    
    # Add logging to understand what's being received
    print(f"process_json_to_blueprints received data of type: {type(structured_json)}")
    if isinstance(structured_json, str):
        print(f"structured_json is a string (first 100 chars): {structured_json[:100]}...")
        try:
            structured_json = json.loads(structured_json)
            print(f"Successfully parsed string to dict with keys: {list(structured_json.keys())}")
        except json.JSONDecodeError as e:
            print(f"Error parsing structured_json string: {e}")
    elif isinstance(structured_json, dict):
        print(f"structured_json is a dict with keys: {list(structured_json.keys())}")
    
    # Create blueprints directory if it doesn't exist
    os.makedirs(Config.BLUEPRINTS_DIR, exist_ok=True)
    
    # Convert JSON to blueprints
    blueprints = convert_json_to_blueprints(structured_json)
    
    # Save blueprints to files
    blueprint_files = []
    for blueprint in blueprints:
        # Generate a filename based on the record ID
        record_id = blueprint.get("file_info", {}).get("record_id", str(uuid.uuid4()))
        blueprint_path = os.path.join(Config.BLUEPRINTS_DIR, f"{record_id}_blueprint.json")
        
        # Save the blueprint to a file
        with open(blueprint_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, indent=2)
        
        blueprint_files.append(blueprint_path)
    
    print(f"Created {len(blueprint_files)} blueprint files in {Config.BLUEPRINTS_DIR}")
    return blueprints

def clean_json_string(json_str):
    """Clean and extract JSON from text using json5."""
    # Remove any leading/trailing whitespace
    json_str = json_str.strip()
    
    # If it starts with a markdown code block, extract the content
    if json_str.startswith("```"):
        # Extract content between code block markers
        pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(pattern, json_str)
        if matches:
            json_str = matches[0].strip()
    
    # Use json5 to parse the relaxed JSON syntax
    import json5
    parsed = json5.loads(json_str)
    
    # Convert back to standard JSON
    return json.dumps(parsed)

if __name__ == "__main__":
    Config.initialize()
    num_processed = process_json_to_blueprints()
    print(f"Processed {num_processed} JSON files into markdown blueprints") 