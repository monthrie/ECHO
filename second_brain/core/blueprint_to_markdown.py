import json
import os
import re
from pathlib import Path
import yaml
from second_brain.utils.config import Config

def sanitize_filename(name):
    """Sanitize a string to be used as a filename or directory name."""
    # Replace only truly invalid characters with underscores
    # Keep spaces intact for better Obsidian titles
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    
    # Ensure we have a valid filename
    sanitized = sanitized.strip()
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
        
        # Remove any H1 heading that duplicates the title
        import re
        title_pattern = re.compile(f"^# {re.escape(title)}\\s*\n", re.MULTILINE)
        body = title_pattern.sub("", body)
        
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
        # Do NOT add the title as an H1 heading since Obsidian shows the filename as title
        markdown_content = f"---\n{frontmatter_yaml}---\n\n{body}"
        
        # Write to file
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Created markdown file: {full_file_path}")
        return str(full_file_path)
    
    except Exception as e:
        print(f"Error converting blueprint to markdown: {str(e)}")
        return None

def process_blueprint_files(blueprint, config=None):
    """
    Process a single blueprint file and convert it to markdown files.
    
    Args:
        blueprint: Blueprint object or a string path to a JSON file
        config: Configuration object (optional)
    
    Returns:
        List of created markdown files
    """
    created_files = []
    
    # Use provided config or import the global one
    if config is None:
        from second_brain.utils.config import Config
        config = Config
        
        # Ensure config is initialized
        if not hasattr(config, 'VAULT_PATH') and not hasattr(config, 'MARKDOWN_OUTPUT_DIR'):
            config.initialize()
    
    # Check if blueprint is a string (file path)
    if isinstance(blueprint, str):
        try:
            with open(blueprint, 'r') as f:
                blueprint = json.load(f)
        except Exception as e:
            print(f"Error loading blueprint from file: {e}")
            return []
    
    # Now process the blueprint
    for blueprint in blueprint:
        # Extract file info
        directory = blueprint.get("file_info", {}).get("directory", "")
        filename = blueprint.get("file_info", {}).get("filename", "")
        
        # Ensure filename has .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        # Extract frontmatter
        frontmatter = blueprint.get("frontmatter", {})
        
        # Move record_ids to a hidden property with underscore prefix
        if 'record_ids' in frontmatter:
            frontmatter['_record_ids'] = frontmatter.pop('record_ids')
        
        # Extract content
        title = blueprint.get("content", {}).get("title", "")
        body = blueprint.get("content", {}).get("body", "")
        
        # Remove any H1 heading that duplicates the title
        # This pattern matches "# Title" at the beginning of the content
        import re
        title_pattern = re.compile(f"^# {re.escape(title)}\\s*\n", re.MULTILINE)
        body = title_pattern.sub("", body)
        
        # Use VAULT_PATH as the primary output directory
        if hasattr(config, 'VAULT_PATH'):
            output_dir = config.VAULT_PATH
        elif hasattr(config, 'MARKDOWN_OUTPUT_DIR'):
            output_dir = config.MARKDOWN_OUTPUT_DIR
        else:
            print("Warning: Neither Config.VAULT_PATH nor Config.MARKDOWN_OUTPUT_DIR found, using current directory")
            output_dir = "."
            
        file_path = os.path.join(output_dir, directory, filename)
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create the markdown content with frontmatter
        markdown_content = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, list):
                markdown_content += f"{key}: {json.dumps(value)}\n"
            else:
                markdown_content += f"{key}: {value}\n"
        markdown_content += "---\n\n"
        
        # Add the body without duplicating the title
        markdown_content += body
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write(markdown_content)
        
        created_files.append(file_path)
        print(f"Created markdown file: {file_path}")
    
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
    from second_brain.utils.config import Config
    Config.initialize()
    
    # Load blueprints from the configured directory
    blueprint_files = []
    try:
        blueprint_dir = Config.BLUEPRINTS_DIR
        if os.path.exists(blueprint_dir):
            for file in os.listdir(blueprint_dir):
                if file.endswith('.json'):
                    blueprint_files.append(os.path.join(blueprint_dir, file))
    except AttributeError:
        print("Warning: Config.BLUEPRINTS_DIR not found, looking in current directory")
        # Fallback to current directory
        for file in os.listdir('.'):
            if file.endswith('.json'):
                blueprint_files.append(file)
    
    # Process each blueprint file
    all_created_files = []
    for blueprint_file in blueprint_files:
        print(f"Processing blueprint file: {blueprint_file}")
        created_files = process_blueprint_files(blueprint_file, Config)
        all_created_files.extend(created_files)
    
    # Create index if files were created
    if all_created_files:
        create_index_file(all_created_files, Config)
    
    print(f"Conversion complete! Created {len(all_created_files)} files.") 