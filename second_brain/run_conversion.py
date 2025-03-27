from pathlib import Path
import os
import sys
import argparse

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from second_brain.core.main import process_transcripts
from second_brain.core.prepare_markdown_json import process_json_to_blueprints
from second_brain.core.blueprint_to_markdown import process_blueprint_files
from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer


def run_pipeline(transcript_file=None):
    """Run the full pipeline from transcript to markdown."""
    # Initialize configuration - MUST be called first
    logger = Config.initialize(transcript_file)
    logger.info("Starting pipeline...")
    
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
            
            # Convert JSON to blueprints
            print("Converting JSON to blueprints...")
            blueprints = process_json_to_blueprints(structured_json, tracer)
            
            # Convert blueprints to markdown
            print("Converting blueprints to markdown...")
            markdown_files = process_blueprint_files(blueprints)
            
            print(f"Pipeline complete. Created {len(markdown_files)} markdown files.")
            return True
        else:
            print("No structured JSON was generated. Pipeline halted.")
            return False
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        print(f"Error in pipeline: {str(e)}")
        return False


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Convert transcripts to markdown knowledge base")
    parser.add_argument("--transcript", "-t", help="Path to transcript CSV file")
    args = parser.parse_args()
    
    # Run the pipeline
    run_pipeline(args.transcript) 