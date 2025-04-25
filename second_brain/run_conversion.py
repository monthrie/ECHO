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
# Import the document classifier
from second_brain.utils.document_classifier import classify_document
# Import process_article function
from second_brain.utils.process_article import process_article, process_input_file


def run_conversion(input_file, output_dir=None):
    """
    Run the conversion process with document type classification.
    
    Args:
        input_file: Path to the input file to process
        output_dir: Optional output directory (defaults to configured vault path)
    
    Returns:
        List of created markdown files
    """
    # Initialize config if needed
    if not hasattr(Config, 'OBSIDIAN_VAULT_PATH'):
        Config.initialize()
    
    # Determine the vault path
    vault_path = output_dir if output_dir else Config.OBSIDIAN_VAULT_PATH
    
    # Initialize LangSmith tracer
    tracer = SecondBrainTracer()
    
    # First, check if the input file exists and is a file (not JSON or directory)
    if os.path.isfile(input_file) and not input_file.endswith('.json'):
        # Classify the document
        print(f"Classifying document type for: {input_file}")
        classification_result = classify_document(input_file)
        document_type = classification_result.get('document_type')
        
        print(f"Document classified as: {document_type}")
        
        # If it's an article, use the article processing pipeline
        if document_type == "article":
            print("Processing as article...")
            created_files = process_input_file(input_file, vault_path, tracer)
            print(f"Article processing complete. Created {len(created_files)} markdown files.")
            return created_files
    
    # If it's not an article or the check was bypassed, continue with the existing pipeline
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
    
    # If the input is a JSON file, load it directly
    json_data = None
    if input_file.endswith('.json'):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print(f"Loaded JSON data from {input_file}")
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return []
    
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
    
    try:
        # If we don't have JSON data yet (not loaded from file), process the transcript
        if json_data is None:
            print("Starting transcript processing...")
            json_data = process_transcripts(tracer)
        
        if json_data:
            # Add debugging output
            print(f"Type of json_data: {type(json_data)}")
            if isinstance(json_data, dict):
                print(f"Keys in json_data: {json_data.keys()}")
            else:
                print(f"json_data is not a dictionary: {json_data[:100]}...")
            
            # Skip directly to blueprint conversion
            print("Converting JSON to blueprints...")
            # Pass vault_structure to process_json_to_blueprints
            blueprints = process_json_to_blueprints(json_data, tracer, vault_structure)
            
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
    finally:
        # Clean up temporary index file
        try:
            if os.path.exists(index_path):
                os.remove(index_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary index file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert documents to markdown files")
    parser.add_argument("--input", "-i", help="Path to input file (transcript, article, or JSON)")
    parser.add_argument("--output", "-o", help="Output directory for markdown files")
    parser.add_argument("--all", "-a", action="store_true", help="Process all files in the input directory")
    
    args = parser.parse_args()
    
    # Default input directory
    default_input_dir = "/Users/wilmon/Documents/projects/ECHO/second_brain/data/input"
    
    if args.input:
        # Process the specified input file
        created_files = run_conversion(args.input, args.output)
        print(f"Conversion complete. Created {len(created_files)} files.")
    elif args.all:
        # Process all files in the default input directory
        created_files = []
        print(f"Processing all files in {default_input_dir}")
        file_count = 0
        
        for filename in os.listdir(default_input_dir):
            if filename.endswith(('.txt', '.md', '.json')):
                file_path = os.path.join(default_input_dir, filename)
                print(f"\nProcessing file: {filename}")
                try:
                    files = run_conversion(file_path, args.output)
                    created_files.extend(files)
                    file_count += 1
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        
        print(f"\nConversion complete. Processed {file_count} files and created {len(created_files)} markdown files.")
    else:
        # Look for the first suitable file in the input directory
        print(f"No input specified. Looking for files in {default_input_dir}")
        
        for filename in os.listdir(default_input_dir):
            if filename.endswith(('.txt', '.md', '.json')):
                file_path = os.path.join(default_input_dir, filename)
                print(f"Found file: {filename}")
                created_files = run_conversion(file_path, args.output)
                print(f"Conversion complete. Created {len(created_files)} files.")
                break
        else:
            print(f"No suitable files found in {default_input_dir}")
            parser.print_help()