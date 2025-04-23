from pathlib import Path
import os
import sys
import argparse
from dotenv import load_dotenv
import json

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from second_brain.core.main import process_transcripts
from second_brain.core.prepare_markdown_json import process_json_to_blueprints
from second_brain.core.blueprint_to_markdown import process_blueprint_files, create_index_file
from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer
from second_brain.utils.simple_file_index import create_vault_index
from second_brain.prompts.blueprint_prompt import get_blueprint_conversion_prompt


def run_conversion(json_data_file, output_dir=None):
    """
    Run the conversion process with awareness of existing vault structure.
    
    Args:
        json_data_file: Path to the JSON data file to process
        output_dir: Optional output directory (defaults to configured vault path)
    
    Returns:
        List of created markdown files
    """
    # Initialize config if needed
    if not hasattr(Config, 'OBSIDIAN_VAULT_PATH'):
        Config.initialize()
    
    # Determine the vault path
    vault_path = output_dir if output_dir else Config.OBSIDIAN_VAULT_PATH
    
    # Create vault index to understand current structure
    print(f"Creating vault index from: {vault_path}")
    index_path = create_vault_index(vault_path, output_file="temp_vault_index.json")
    
    # Load the index data
    vault_structure = None
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            vault_structure = json.load(f)
        print(f"Loaded vault structure with {len(vault_structure)} entries")
    except Exception as e:
        print(f"Warning: Could not load vault structure: {e}")
    
    # Load the JSON data
    with open(json_data_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Generate the blueprint using the enhanced prompt with vault structure
    prompt = get_blueprint_conversion_prompt(json_data, vault_structure)
    
    # Add immediate model debugging
    print("\n===== MODEL CONFIGURATION DEBUG =====")
    # Check what's in environment before any initialization
    load_dotenv(override=True)
    env_model = os.getenv("MODEL", "Not set in environment")
    print(f"MODEL from environment: {env_model}")
    
    # Initialize configuration
    logger = Config.initialize()
    logger.info("Starting pipeline...")
    
    # Log model after initialization
    print(f"MODEL after Config.initialize(): {Config.MODEL}")
    
    # Try refreshing model settings and log the result
    refreshed_model = Config.refresh_model_settings()
    print(f"MODEL after Config.refresh_model_settings(): {refreshed_model}")
    print("===== END MODEL DEBUG =====\n")
    
    # Initialize LangSmith tracer
    tracer = SecondBrainTracer()
    
    try:
        # Process transcripts
        print("Starting transcript processing...")
        structured_json = process_transcripts(tracer)
        
        if structured_json:
            # Add debugging output
            print(f"Type of structured_json: {type(structured_json)}")
            if isinstance(structured_json, dict):
                print(f"Keys in structured_json: {structured_json.keys()}")
            else:
                print(f"structured_json is not a dictionary: {structured_json[:100]}...")
            
            # Skip directly to blueprint conversion
            print("Converting JSON to blueprints...")
            # Pass vault_structure to process_json_to_blueprints
            blueprints = process_json_to_blueprints(structured_json, tracer, vault_structure)
            
            # Convert blueprints to markdown
            print("Converting blueprints to markdown...")
            markdown_files = process_blueprint_files(blueprints, vault_path)
            
            # Create index file for the new markdown files
            if markdown_files:
                create_index_file(markdown_files, vault_path)
            
            print(f"Pipeline complete. Created {len(markdown_files)} markdown files.")
            return markdown_files
        else:
            print("No structured JSON was generated. Pipeline halted.")
            return []
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        print(f"Error in pipeline: {str(e)}")
        return []
    
    # Clean up temporary index file
    try:
        os.remove(index_path)
    except Exception as e:
        print(f"Warning: Could not delete temporary index file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert transcripts or JSON to markdown files")
    parser.add_argument("--transcript", "-t", help="Path to transcript file")
    parser.add_argument("--json", "-j", help="Path to JSON data file")
    parser.add_argument("--output", "-o", help="Output directory for markdown files")
    
    args = parser.parse_args()
    
    if args.json:
        # If JSON file is provided, use it directly
        run_conversion(args.json, args.output)
    else:
        # If no JSON file, process the transcript first
        from second_brain.core.main import process_transcripts
        
        # Initialize config with transcript if provided
        Config.initialize(args.transcript)
        
        # Initialize LangSmith tracer
        tracer = SecondBrainTracer()
        
        # Process the transcript to get JSON
        structured_json = process_transcripts(tracer)
        
        if structured_json:
            # Save the structured JSON to a file
            json_path = Path(Config.JSON_OUTPUT_DIR) / "structured_data.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(structured_json, f, indent=2)
            
            # Now run conversion with the JSON file
            run_conversion(str(json_path), args.output)
        else:
            print("No structured JSON was generated. Pipeline halted.") 