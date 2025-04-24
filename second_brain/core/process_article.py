#!/usr/bin/env python3
"""
Process articles and other text inputs into Obsidian markdown files.

This script:
1. Takes the full text as input (which may contain instructions within it)
2. Sends the entire text to an LLM for processing
3. Creates blueprints for Obsidian markdown files
4. Generates markdown files in the vault

Usage:
  python -m second_brain.core.process_article --input path/to/article.txt --output-dir path/to/vault
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
import requests
from typing import Dict, List, Any, Optional
import logging
import glob

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer
from second_brain.core.blueprint_to_markdown import process_blueprint_files, create_index_file
from second_brain.utils.date_utils import get_current_datetime_str
from second_brain.utils.simple_file_index import create_vault_index

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_article(text: str, vault_path: str = None, tracer=None) -> Dict:
    """
    Process an article using LLM, handling any instructions within the text.
    
    Args:
        text: The complete text (which may include instructions)
        vault_path: Path to the Obsidian vault for context
        tracer: Optional tracer for langsmith
    
    Returns:
        Blueprint dict ready for conversion to markdown
    """
    logger.info("Processing article with LLM")
    
    # Load vault structure for context if vault path is provided
    vault_structure = None
    if vault_path and os.path.exists(vault_path):
        try:
            index_path = create_vault_index(vault_path)
            with open(index_path, 'r', encoding='utf-8') as f:
                vault_structure = json.load(f)
            logger.info(f"Loaded vault structure with {len(vault_structure)} entries")
        except Exception as e:
            logger.warning(f"Could not load vault structure: {str(e)}")
    
    # Add current date and time
    date_str = get_current_datetime_str()
    
    # Create the prompt for the LLM
    prompt = f"""You are a knowledge management assistant. The current date and time is: {date_str}

I have provided text that I want to process into my Obsidian knowledge base. 

IMPORTANT GUIDELINES:
1. The text might contain instructions at the beginning (like "summarize this" or "extract key concepts").
2. If there are instructions, follow them exactly.
3. If no instructions are found, DEFAULT TO SUMMARIZING the content and extracting key concepts.
4. ALWAYS place the note in a "Research/" directory structure.

TEXT:
{text}

Please convert this into a blueprint for an Obsidian markdown file. The blueprint should:

1. Include appropriate frontmatter with tags
2. Have a well-structured body with headings
3. Extract key concepts and insights
4. Link to related topics when appropriate
5. Organize the content logically

Return a SINGLE blueprint in this JSON format:

{{
  "file_info": {{
    "directory": "Research/[appropriate subdirectory]",
    "filename": "Descriptive filename with spaces",
    "record_id": "Generated unique ID"
  }},
  "frontmatter": {{
    "tags": ["research", "other-relevant-tags"],
    "description": "Concise description of the note's purpose"
  }},
  "content": {{
    "title": "Note title",
    "body": "Well-structured markdown with headings, lists, and formatting"
  }}
}}

DIRECTORY STRUCTURE REQUIREMENTS:
- ALL notes MUST be placed in the "Research/" directory or a subdirectory of Research
- Choose an appropriate subdirectory based on content topic (e.g., Research/AI, Research/Economics)
- Always include "research" as the first tag in the frontmatter
"""

    # Add vault structure context if available
    if vault_structure:
        prompt += f"\n\nEXISTING VAULT STRUCTURE:\n{json.dumps(vault_structure, indent=2)}\n\nTry to fit the new note into existing Research subdirectories when possible."
    
    # Call the LLM API
    logger.info("Calling LLM via OpenRouter")
    try:
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
                    {"role": "system", "content": "You are a knowledge management assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            raise Exception(f"API call failed: {response.text}")
        
        result = response.json()
        blueprint_text = result["choices"][0]["message"]["content"]
        
        # Trace the API call if tracer is provided
        if tracer:
            metadata = {
                "stage": "article_to_blueprint",
                "content_length": len(text),
                "model": Config.MODEL
            }
            tracer.trace_openrouter_call(
                "article_to_blueprint", 
                prompt, 
                blueprint_text, 
                metadata
            )
        
        # Extract JSON from the response
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```|(\{[\s\S]*\})', blueprint_text)
        if json_match:
            json_str = json_match.group(1) or json_match.group(2)
            blueprint = json.loads(json_str)
            
            # Enforce the Research directory requirement
            directory = blueprint.get("file_info", {}).get("directory", "")
            if not directory.startswith("Research"):
                blueprint["file_info"]["directory"] = f"Research/{directory}" if directory else "Research"
            
            # Ensure "research" tag is included
            tags = blueprint.get("frontmatter", {}).get("tags", [])
            if "research" not in tags:
                tags.insert(0, "research")
                blueprint["frontmatter"]["tags"] = tags
            
            logger.info(f"Successfully created blueprint for '{blueprint.get('content', {}).get('title', 'Untitled')}'")
            return blueprint
        else:
            logger.error("Failed to extract JSON from LLM response")
            raise Exception("Failed to extract JSON from LLM response")
    
    except Exception as e:
        logger.error(f"Error in process_article: {str(e)}")
        # Create a basic blueprint for error case
        return {
            "file_info": {
                "directory": "Research/Errors",
                "filename": "Error Processing Article",
                "record_id": "error"
            },
            "frontmatter": {
                "tags": ["research", "error"],
                "description": "Error occurred while processing article"
            },
            "content": {
                "title": "Error Processing Article",
                "body": f"# Error Processing Article\n\nAn error occurred while processing the article:\n\n```\n{str(e)}\n```\n\n## Original Content\n\n{text[:500]}...\n"
            }
        }

def process_input_file(file_path, vault_path, tracer):
    """Process a single input file and create markdown."""
    logger.info(f"Processing input file: {file_path}")
    # Read the input file
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        logger.info(f"Read {len(text)} characters from {file_path}")
    
    # Process the article to get blueprint
    blueprint = process_article(text, vault_path, tracer)
    
    # Convert blueprint to markdown
    created_files = process_blueprint_files(blueprint, vault_path)
    
    # Log results
    logger.info(f"Created {len(created_files)} markdown file(s) from {file_path}")
    for file_path in created_files:
        logger.info(f"  - {file_path}")
    
    return created_files

def main():
    """Main function to process article files and create markdown output."""
    parser = argparse.ArgumentParser(description="Process article text into Obsidian markdown")
    parser.add_argument("--file", "-f", help="Specific file to process from second_brain/data/input")
    parser.add_argument("--all", "-a", action="store_true", help="Process all files in second_brain/data/input")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize configuration
    Config.initialize()
    
    # Get the input directory path
    input_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data" / "input"
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created input directory: {input_dir}")
    
    # Determine the vault path
    vault_path = Config.OBSIDIAN_VAULT_PATH
    if not vault_path:
        logger.error("No vault path configured. Please set OBSIDIAN_VAULT_PATH in your .env file.")
        return
    
    # Initialize tracer
    tracer = SecondBrainTracer()
    
    # Process files
    created_files = []
    
    if args.file:
        # Process a specific file
        file_path = input_dir / args.file
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        
        created_files.extend(process_input_file(file_path, vault_path, tracer))
    
    elif args.all:
        # Process all files in the input directory
        file_count = 0
        for file_path in glob.glob(str(input_dir / "*.txt")):
            created_files.extend(process_input_file(file_path, vault_path, tracer))
            file_count += 1
        
        logger.info(f"Processed {file_count} files from {input_dir}")
    
    else:
        logger.error("No action specified. Use --file or --all.")
        parser.print_help()
        return
    
    # Create an index file if multiple files were created
    if len(created_files) > 1:
        index_file = create_index_file(created_files, vault_path)
        logger.info(f"Created index file: {index_file}")
    
    logger.info(f"Processing complete. Created {len(created_files)} markdown files.")

if __name__ == "__main__":
    main() 