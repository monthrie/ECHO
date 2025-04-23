import os
import yaml
import json
import re
from pathlib import Path
from second_brain.utils.config import Config

def extract_frontmatter(file_path):
    """Extract frontmatter from a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for YAML frontmatter between --- markers
    frontmatter = {}
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            print(f"Warning: Could not parse frontmatter in {file_path}")
    
    return frontmatter

def create_vault_index(vault_path, output_file="vault_index.json"):
    """
    Create an index of all markdown files in the vault, extracting
    frontmatter data for organization purposes.
    """
    vault_path = Path(vault_path)
    index_data = []
    
    # Walk through all markdown files in the vault
    for file_path in vault_path.glob("**/*.md"):
        # Get relative path for readability
        relative_path = str(file_path.relative_to(vault_path))
        
        # Extract frontmatter
        try:
            frontmatter = extract_frontmatter(file_path)
            
            # Get description and tags
            description = frontmatter.get("description", "")
            tags = frontmatter.get("tags", [])
            
            # Store info in our index
            index_data.append({
                "filepath": relative_path,
                "description": description,
                "tags": tags,
                "directory": str(file_path.parent.relative_to(vault_path))
            })
            
            print(f"Processed: {relative_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Write the index to a JSON file
    output_path = vault_path / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"Created vault index with {len(index_data)} entries at {output_path}")
    return output_path

if __name__ == "__main__":
    # Initialize config to get vault path
    Config.initialize()
    
    # Use the vault path from config
    vault_path = Config.VAULT_PATH if hasattr(Config, 'VAULT_PATH') else Config.OBSIDIAN_VAULT_PATH
    
    # Create the index
    index_file = create_vault_index(vault_path)
    print(f"Index created at: {index_file}")
