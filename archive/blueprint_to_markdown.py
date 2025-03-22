import json
import os
import re
from pathlib import Path
import yaml
from archive.config import Config

def sanitize_filename(filename):
    """
    Sanitize a filename to ensure it's valid for the file system.
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()
    # Ensure we have a valid filename
    if not sanitized:
        sanitized = "Untitled"
    return sanitized

def ensure_directory_exists(directory_path):
    """
    Ensure that a directory exists, creating it if necessary.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def convert_blueprint_to_markdown(blueprint, base_path):
    """
    Convert a single blueprint to a markdown file.
    """
    try:
        # Extract file information
        directory = blueprint.get('file_info', {}).get('directory', 'Uncategorized')
        filename = blueprint.get('file_info', {}).get('filename', 'Untitled')
        record_id = blueprint.get('file_info', {}).get('record_id', '')
        
        # Extract content
        title = blueprint.get('content', {}).get('title', 'Untitled')
        body = blueprint.get('content', {}).get('body', '')
        
        # Extract frontmatter
        frontmatter = blueprint.get('frontmatter', {})
        
        # Move record_ids to a hidden property with underscore prefix
        if 'record_ids' in frontmatter:
            frontmatter['_record_ids'] = frontmatter.pop('record_ids')
        
        # Sanitize filename and ensure it has .md extension
        sanitized_filename = sanitize_filename(filename)
        if not sanitized_filename.endswith('.md'):
            sanitized_filename += '.md'
        
        # Create full directory path
        full_dir_path = Path(base_path) / directory
        ensure_directory_exists(full_dir_path)
        
        # Create full file path
        full_file_path = full_dir_path / sanitized_filename
        
        # Convert frontmatter to YAML
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False)
        
        # Combine frontmatter and body into a complete markdown document
        # Do NOT add the title as an H1 heading - the body should already include it
        markdown_content = f"---\n{frontmatter_yaml}---\n\n{body}"
        
        # Write to file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Created markdown file: {full_file_path}")
        return str(full_file_path)
    
    except Exception as e:
        print(f"Error converting blueprint to markdown: {str(e)}")
        return None

def process_blueprint_files(blueprint_dir=None, output_dir=None):
    """
    Process all blueprint files in the specified directory and convert them to markdown files.
    """
    if blueprint_dir is None:
        blueprint_dir = Path(Config.JSON_OUTPUT_DIR) / "blueprints"
    
    if output_dir is None:
        output_dir = Config.OBSIDIAN_VAULT_PATH
    
    # Ensure output directory exists
    ensure_directory_exists(output_dir)
    
    # Find all blueprint JSON files
    blueprint_files = list(Path(blueprint_dir).glob('*_blueprint.json'))
    print(f"Found {len(blueprint_files)} blueprint files to process")
    
    created_files = []
    
    for blueprint_file in blueprint_files:
        try:
            with open(blueprint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            blueprints = data.get('blueprints', [])
            print(f"Processing {len(blueprints)} blueprints from {blueprint_file.name}")
            
            # Process each blueprint
            for blueprint in blueprints:
                file_path = convert_blueprint_to_markdown(blueprint, output_dir)
                if file_path:
                    created_files.append(file_path)
            
        except Exception as e:
            print(f"Error processing {blueprint_file}: {str(e)}")
    
    print(f"Created {len(created_files)} markdown files")
    return created_files

def create_index_file(created_files, output_dir=None):
    """
    Create an index file listing all created markdown files.
    """
    if output_dir is None:
        output_dir = Config.OBSIDIAN_VAULT_PATH
    
    index_path = Path(output_dir) / "index.md"
    
    # Group files by directory
    files_by_dir = {}
    for file_path in created_files:
        path = Path(file_path)
        dir_name = str(path.parent.relative_to(output_dir))
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append(path.name)
    
    # Create index content
    index_content = "# Index of Generated Markdown Files\n\n"
    
    for dir_name, files in sorted(files_by_dir.items()):
        index_content += f"## {dir_name}\n\n"
        for file_name in sorted(files):
            # Create a relative link to the file
            link_path = f"{dir_name}/{file_name}".replace("\\", "/")
            file_title = file_name.replace('.md', '')
            index_content += f"- [{file_title}]({link_path})\n"
        index_content += "\n"
    
    # Write index file
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"Created index file: {index_path}")
    return str(index_path)

if __name__ == "__main__":
    Config.initialize()
    created_files = process_blueprint_files()
    if created_files:
        create_index_file(created_files)
    print("Conversion complete!") 