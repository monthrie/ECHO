import os
import json
import sys
from pathlib import Path
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from second_brain.utils.config import Config
from second_brain.core.main import get_structured_json
from second_brain.core.prepare_markdown_json import convert_json_to_blueprints
from second_brain.prompts.blueprint_prompt import get_blueprint_conversion_prompt


def test_get_structured_json(transcript_text, save_output=True):
    """Test the get_structured_json function with a specific transcript."""
    print(f"Testing get_structured_json with transcript: {transcript_text[:100]}...")
    
    # Initialize config
    Config.initialize()
    
    # Call the function
    result = get_structured_json(transcript_text)
    
    # Save the result to a file
    if save_output and result:
        output_path = Path("test_output") / "structured_json_test.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            if isinstance(result, str):
                f.write(result)
            else:
                json.dump(result, f, indent=2)
        print(f"Saved result to {output_path}")
    
    return result


def test_convert_json_to_blueprints(json_data=None, json_file=None, save_output=True):
    """Test the convert_json_to_blueprints function with specific JSON data."""
    # Initialize config
    Config.initialize()
    
    # Load JSON from file if provided
    if json_file and not json_data:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
    
    if not json_data:
        print("Error: No JSON data provided")
        return None
    
    print(f"Testing convert_json_to_blueprints with JSON data...")
    
    # Show the prompt that would be sent to the LLM
    prompt = get_blueprint_conversion_prompt(json_data)
    print("\n--- PROMPT PREVIEW ---")
    print(f"{prompt[:500]}...\n")
    
    # Call the function
    result = convert_json_to_blueprints(json_data)
    
    # Save the result to a file
    if save_output and result:
        output_path = Path("test_output") / "blueprint_test.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Saved result to {output_path}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Test individual LLM calls")
    parser.add_argument("--function", "-f", choices=["json", "blueprint"], 
                        required=True, help="Which function to test")
    parser.add_argument("--input", "-i", help="Input text or JSON file path")
    args = parser.parse_args()
    
    if args.function == "json":
        # Test get_structured_json
        if args.input:
            if os.path.isfile(args.input):
                with open(args.input, 'r') as f:
                    transcript_text = f.read()
            else:
                transcript_text = args.input
        else:
            transcript_text = input("Enter transcript text: ")
        
        result = test_get_structured_json(transcript_text)
        print("\n--- RESULT PREVIEW ---")
        if isinstance(result, dict):
            print(json.dumps(result, indent=2)[:500] + "...")
        else:
            print(str(result)[:500] + "...")
    
    elif args.function == "blueprint":
        # Test convert_json_to_blueprints
        if args.input and os.path.isfile(args.input):
            result = test_convert_json_to_blueprints(json_file=args.input)
        else:
            print("Please provide a valid JSON file path")
            return
        
        print("\n--- RESULT PREVIEW ---")
        print(json.dumps(result, indent=2)[:500] + "...")


if __name__ == "__main__":
    main() 