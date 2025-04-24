#!/usr/bin/env python3
"""
Blueprint integration script that:
1. Takes blueprints from prepare_markdown_json.py
2. Uses LLM to find relevant existing files
3. Makes decisions about integrating new content
4. Outputs markdown files (new or modified)
"""

import json
import os
import re
import argparse
from pathlib import Path
import requests
import logging
from typing import List, Dict, Any

from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer
from second_brain.utils.simple_file_index import create_vault_index
from second_brain.core.simple_file_finder import find_relevant_files
from second_brain.utils.date_utils import get_current_datetime_str

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Similarity threshold - files with relevance below this won't be considered
RELEVANCE_THRESHOLD = 0.70

def integrate_blueprint(blueprint_path: str, vault_path: str, tracer=None) -> List[str]:
    """
    Integrate a blueprint with existing content in the vault.
    
    Args:
        blueprint_path: Path to the blueprint JSON file
        vault_path: Path to the Obsidian vault
        tracer: Optional tracer for LangSmith
        
    Returns:
        List of paths to created/updated markdown files
    """
    logger.info(f"Integrating blueprint: {blueprint_path}")
    
    # Load the blueprint
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
        
    # Find relevant files using LLM
    relevant_files = find_relevant_files(blueprint_path, vault_path)
    
    # Filter by relevance threshold
    high_relevance_files = []
    for file in relevant_files:
        if isinstance(file, dict) and file.get('relevance', 0) >= RELEVANCE_THRESHOLD:
            high_relevance_files.append(file)
            logger.info(f"High relevance file: {file['filepath']} ({file['relevance']:.2f})")
    
    # If no high relevance files found, just convert the blueprint to markdown
    if not high_relevance_files:
        logger.info("No high relevance files found. Creating new file.")
        return create_new_file(blueprint, vault_path)
    
    # Otherwise, send blueprint and existing files to LLM for integration
    return integrate_with_existing(blueprint, high_relevance_files, vault_path, tracer)

def create_new_file(blueprint: Dict[str, Any], vault_path: str) -> List[str]:
    """Create a new markdown file from a blueprint."""
    logger.info("Creating new file from blueprint")
    
    # Extract file info
    directory = blueprint.get('file_info', {}).get('directory', '')
    filename = blueprint.get('file_info', {}).get('filename', 'Untitled')
    if not filename.endswith('.md'):
        filename += '.md'
    
    # Create full directory path
    full_dir = os.path.join(vault_path, directory)
    os.makedirs(full_dir, exist_ok=True)
    
    # Create full file path
    file_path = os.path.join(full_dir, filename)
    
    # Generate markdown content
    frontmatter = blueprint.get('frontmatter', {})
    title = blueprint.get('content', {}).get('title', '')
    body = blueprint.get('content', {}).get('body', '')
    
    # Format frontmatter as YAML
    frontmatter_yaml = "---\n"
    for key, value in frontmatter.items():
        if isinstance(value, list):
            frontmatter_yaml += f"{key}:\n"
            for item in value:
                frontmatter_yaml += f"  - {item}\n"
        else:
            frontmatter_yaml += f"{key}: {value}\n"
    frontmatter_yaml += "---\n\n"
    
    # Combine frontmatter and body
    markdown_content = frontmatter_yaml + body
    
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    logger.info(f"Created new file: {file_path}")
    return [file_path]

def integrate_with_existing(blueprint: Dict[str, Any], relevant_files: List[Dict], 
                         vault_path: str, tracer=None) -> List[str]:
    """
    Integrate blueprint with existing files using LLM.
    
    Args:
        blueprint: The blueprint to integrate
        relevant_files: List of relevant existing files
        vault_path: Path to the Obsidian vault
        tracer: Optional tracer for LangSmith
        
    Returns:
        List of paths to created/updated markdown files
    """
    logger.info(f"Integrating blueprint with {len(relevant_files)} existing files")
    
    # Load content of relevant files
    for file in relevant_files:
        filepath = file['filepath']
        full_path = os.path.join(vault_path, filepath)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                file['content'] = f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            file['content'] = f"ERROR: Could not read file: {e}"
    
    # Prepare prompt for LLM
    date_str = get_current_datetime_str()
    prompt = f"""You are a knowledge management assistant. The current date and time is: {date_str}
Your task is to integrate new content with existing files.

NEW CONTENT (BLUEPRINT):
{json.dumps(blueprint, indent=2)}

RELEVANT EXISTING FILES:
"""

    for i, file in enumerate(relevant_files):
        prompt += f"""
FILE {i+1}: {file['filepath']} (Relevance: {file['relevance']:.2f})
REASON: {file.get('reason', 'No reason provided')}

CONTENT:
{file['content']}
---

"""

    prompt += """
Based on the semantic relationships, determine how to best integrate the new content:
1. Update one or more existing files by adding/modifying content
2. Create a new file if the content is sufficiently distinct

For any file that should be modified or created, provide the complete updated content.

FORMAT YOUR RESPONSE AS JSON:
```json
{
  "actions": [
    {
      "action": "update",  // or "create"
      "filepath": "path/to/file.md",
      "content": "// Complete markdown content including frontmatter"
    }
    // Additional actions if needed
  ]
}
```

Make smart decisions about how to merge content. Don't duplicate information.
Maintain appropriate Markdown structure with headings, lists, etc.
"""

    # Call LLM API
    logger.info("Calling LLM to determine integration approach")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": Config.MODEL,
                "messages": [
                    {"role": "system", "content": "You are a knowledge management assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error from API: {response.status_code} {response.text}")
            return create_new_file(blueprint, vault_path)  # Fall back to creating new file
        
        result = response.json()
        llm_response = result["choices"][0]["message"]["content"]
        
        # Trace the call if tracer provided
        if tracer:
            tracer.trace_openrouter_call(
                "blueprint_integration", 
                prompt, 
                llm_response, 
                {"model": Config.MODEL, "temperature": 0.2}
            )
        
        # Process LLM response to extract JSON
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```|(\{[\s\S]*\})', llm_response)
        if not json_match:
            logger.error("LLM response did not contain valid JSON")
            return create_new_file(blueprint, vault_path)  # Fall back to creating new file
        
        json_str = json_match.group(1) or json_match.group(2)
        integration_plan = json.loads(json_str)
        
        # Process the integration plan
        return execute_integration_plan(integration_plan, vault_path)
        
    except Exception as e:
        logger.error(f"Error in LLM integration: {e}")
        import traceback
        traceback.print_exc()
        return create_new_file(blueprint, vault_path)  # Fall back to creating new file

def execute_integration_plan(integration_plan: Dict, vault_path: str) -> List[str]:
    """Execute the integration plan by creating or updating files."""
    updated_files = []
    
    actions = integration_plan.get('actions', [])
    logger.info(f"Executing integration plan with {len(actions)} actions")
    
    for action in actions:
        action_type = action.get('action')
        filepath = action.get('filepath')
        content = action.get('content')
        
        if not filepath or not content:
            logger.warning(f"Skipping action missing filepath or content: {action}")
            continue
        
        # Create full path
        full_path = os.path.join(vault_path, filepath)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write the content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"{action_type.capitalize()}d file: {full_path}")
        updated_files.append(full_path)
    
    return updated_files

def process_blueprints(blueprint_dir: str, vault_path: str, tracer=None) -> List[str]:
    """Process all blueprint files in the given directory."""
    logger.info(f"Processing blueprints from: {blueprint_dir}")
    
    # Find all JSON files in the directory
    blueprint_files = list(Path(blueprint_dir).glob('*.json'))
    logger.info(f"Found {len(blueprint_files)} blueprint files")
    
    all_processed_files = []
    
    # Process each blueprint
    for blueprint_path in blueprint_files:
        try:
            processed_files = integrate_blueprint(str(blueprint_path), vault_path, tracer)
            all_processed_files.extend(processed_files)
        except Exception as e:
            logger.error(f"Error processing blueprint {blueprint_path}: {e}")
            import traceback
            traceback.print_exc()
    
    return all_processed_files

def main():
    global RELEVANCE_THRESHOLD  # Declare that we're using the global variable
    
    parser = argparse.ArgumentParser(description="Blueprint integration")
    parser.add_argument("--blueprint", "-b", help="Path to single blueprint file")
    parser.add_argument("--blueprint-dir", "-d", help="Directory containing blueprint files")
    parser.add_argument("--vault", "-v", help="Path to Obsidian vault")
    parser.add_argument("--threshold", "-t", type=float, default=RELEVANCE_THRESHOLD,
                      help=f"Relevance threshold (default: {RELEVANCE_THRESHOLD})")
    
    args = parser.parse_args()
    
    # Initialize config and tracer
    Config.initialize()
    tracer = SecondBrainTracer()
    
    # Set vault path
    vault_path = args.vault or Config.OBSIDIAN_VAULT_PATH
    
    # Set threshold
    RELEVANCE_THRESHOLD = args.threshold
    
    processed_files = []
    
    if args.blueprint:
        processed_files = integrate_blueprint(args.blueprint, vault_path, tracer)
    elif args.blueprint_dir:
        processed_files = process_blueprints(args.blueprint_dir, vault_path, tracer)
    else:
        logger.error("Either --blueprint or --blueprint-dir must be specified")
        parser.print_help()
        return
    
    logger.info(f"Integration complete. Created/updated {len(processed_files)} files:")
    for file in processed_files:
        logger.info(f"  - {file}")

if __name__ == "__main__":
    main() 