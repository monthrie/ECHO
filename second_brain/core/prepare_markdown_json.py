import json
import os
import uuid
from pathlib import Path
from datetime import datetime
import requests
from second_brain.utils.config import Config
from second_brain.prompts.blueprint_prompt import get_blueprint_conversion_prompt
from second_brain.prompts.prompts import get_structuring_prompt
import re
from second_brain.core.research import research_query

def convert_json_to_blueprints(json_data, tracer=None):
    """Convert JSON data to blueprints using LLM."""
    try:
        print(f"convert_json_to_blueprints received data of type: {type(json_data)}")
        
        # Prepare the prompt for the LLM
        prompt = get_blueprint_conversion_prompt(json_data)
        
        # Save the prompt to a file for inspection
        with open("llm_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"Saved prompt ({len(prompt)} chars) to llm_prompt.txt")
        
        # Save the payload to a file for inspection
        payload = {
            "model": Config.MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that converts structured JSON data into markdown blueprint format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        with open("llm_payload.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Saved complete payload to llm_payload.json")
        
        # Add tracing metadata
        metadata = {
            "stage": "json_to_blueprints",
            "json_size": len(str(json_data)),
            "model": Config.MODEL
        }
        
        # Call the LLM API
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8000"
        }
        
        print("Sending request to LLM API")
        response = requests.post(api_url, headers=headers, json=payload)
        
        # Log the response status and headers
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.text}")
        
        # Extract the response content
        blueprint_text = response.json()["choices"][0]["message"]["content"]
        
        # Trace the API call if tracer is provided
        if tracer:
            tracer.trace_openrouter_call(
                "json_to_blueprints", 
                prompt, 
                blueprint_text, 
                metadata
            )
        
        # Parse the blueprint text
        # This depends on your expected format - adjust as needed
        try:
            # Try to parse as JSON first
            blueprints = json.loads(blueprint_text)
            if not isinstance(blueprints, list):
                blueprints = [blueprints]
        except json.JSONDecodeError:
            # If not valid JSON, use a fallback parsing method
            print("Response is not valid JSON, using fallback parsing")
            blueprints = create_basic_blueprints(json_data, blueprint_text)
        
        return blueprints
    except Exception as e:
        print(f"Error in convert_json_to_blueprints: {str(e)}")
        # Fall back to basic blueprint creation
        return create_basic_blueprints(json_data)

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

def process_json_to_blueprints(json_data, tracer=None):
    """Process JSON data to blueprint files."""
    try:
        # Create blueprints directory if it doesn't exist
        blueprints_dir = Path(Config.BLUEPRINTS_DIR)
        blueprints_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert JSON to blueprints
        blueprints = convert_json_to_blueprints(json_data, tracer)
        
        # Save each blueprint to a file
        blueprint_files = []
        for blueprint in blueprints:
            # Generate a unique ID for the blueprint
            blueprint_id = str(uuid.uuid4())
            
            # Create the blueprint file path
            blueprint_file = blueprints_dir / f"{blueprint_id}_blueprint.json"
            
            # Save the blueprint to a file
            with open(blueprint_file, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=2)
            
            blueprint_files.append(blueprint_file)
        
        print(f"Created {len(blueprint_files)} blueprint files")
        return blueprints
    except Exception as e:
        print(f"Error in process_json_to_blueprints: {str(e)}")
        return []

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

def process_research_requests(json_data, tracer=None):
    """
    Process any research tool instructions in the JSON data.
    Only processes very specialized or real-time data needs.
    """
    # Make a copy of the JSON data to avoid modifying the original
    enriched_json = json_data.copy()
    
    # Check if we have system_instructions and records
    if not isinstance(enriched_json, dict) or "system_instructions" not in enriched_json:
        return enriched_json
    
    # Filter out research instructions - we're not processing them anymore
    # Keep only structural instructions
    enriched_json["system_instructions"] = [
        instruction for instruction in enriched_json.get("system_instructions", [])
        if instruction.get("instruction_type") != "tool" or 
        "research" not in instruction.get("command_type", "").lower()
    ]
    
    return enriched_json

def call_llm_for_records(prompt, tracer=None):
    """
    Call the LLM to structure content into records.
    Similar to how the main transcript processing works.
    """
    try:
        # Make the API call
        print(f"Calling LLM using OpenRouter with model: {Config.MODEL}")
        
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
                    {"role": "system", "content": "You structure content into PARA methodology records."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
        )
        
        if response.status_code != 200:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
        
        response_json = response.json()
        result = response_json["choices"][0]["message"]["content"].strip()
        
        # Trace the call if tracer is available
        if tracer:
            metadata = {
                "model": Config.MODEL,
                "temperature": 0.2,
                "source": "research_to_records"
            }
            tracer.trace_openrouter_call("research_to_records", prompt, result, metadata)
        
        # Extract JSON from the result
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code block markers
            json_str = result
        
        # Clean and parse the JSON
        records_data = clean_json_string(json_str)
        records = json.loads(records_data)
        
        return records
    
    except Exception as e:
        print(f"Error calling LLM for records: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    Config.initialize()
    num_processed = process_json_to_blueprints()
    print(f"Processed {num_processed} JSON files into markdown blueprints") 