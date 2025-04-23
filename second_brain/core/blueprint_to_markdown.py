import json
import os
import re
from pathlib import Path
import yaml
from second_brain.utils.config import Config
import shutil
from datetime import datetime
import logging

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

def process_blueprint_files(blueprint, output_dir=None, config=None):
    """
    Process a single blueprint file and convert it to markdown files.
    
    Args:
        blueprint: Blueprint object or a string path to a JSON file
        output_dir: Explicit output directory (overrides config settings)
        config: Configuration object (optional)
    
    Returns:
        List of created markdown files
    """
    logger = logging.getLogger("second_brain")
    logger.info("Starting process_blueprint_files")
    created_files = []
    
    # If output_dir is explicitly provided, use it
    if output_dir:
        logger.info(f"Using explicitly provided output directory: {output_dir}")
    # Otherwise use config
    else:
        # Use provided config or import the global one
        if config is None:
            from second_brain.utils.config import Config
            config = Config
            
            # Ensure config is initialized
            if not hasattr(config, 'VAULT_PATH') and not hasattr(config, 'MARKDOWN_OUTPUT_DIR'):
                config.initialize()
        
        # Determine output directory from config
        if hasattr(config, 'VAULT_PATH') and config.VAULT_PATH:
            output_dir = config.VAULT_PATH
            logger.info(f"Using Config.VAULT_PATH as output directory: {output_dir}")
        elif hasattr(config, 'MARKDOWN_OUTPUT_DIR') and config.MARKDOWN_OUTPUT_DIR:
            output_dir = config.MARKDOWN_OUTPUT_DIR
            logger.info(f"Using Config.MARKDOWN_OUTPUT_DIR as output directory: {output_dir}")
    
    # If we still don't have an output directory, use current directory
    if not output_dir:
        output_dir = os.getcwd()
        logger.warning(f"No output directory configured, using current directory: {output_dir}")
    
    # Check if blueprint is a string (file path)
    if isinstance(blueprint, str):
        logger.info(f"Blueprint is a file path: {blueprint}")
        try:
            with open(blueprint, 'r') as f:
                blueprint = json.load(f)
            logger.info(f"Loaded blueprint JSON from file, containing {len(blueprint) if isinstance(blueprint, list) else 1} entries")
        except Exception as e:
            logger.error(f"Error loading blueprint from file: {e}")
            return []
    
    # Ensure blueprint is a list
    if not isinstance(blueprint, list):
        blueprint = [blueprint]
        logger.info("Converted blueprint to list format")
    
    logger.info(f"Processing {len(blueprint)} blueprint entries")
    
    # Process each blueprint
    for idx, bp in enumerate(blueprint):
        try:
            # Extract file info
            file_info = bp.get("file_info", {})
            directory = file_info.get("directory", "")
            filename = file_info.get("filename", "Untitled")
            
            logger.info(f"Blueprint #{idx+1}: directory='{directory}', filename='{filename}'")
            
            # Ensure filename has .md extension
            if not filename.endswith(".md"):
                filename += ".md"
                logger.info(f"Added .md extension to filename: {filename}")
            
            # Create directory path
            directory_path = os.path.join(output_dir, directory)
            logger.info(f"Full directory path: {directory_path}")
            
            # Create directory if it doesn't exist
            if not os.path.exists(directory_path):
                logger.info(f"Creating directory: {directory_path}")
                os.makedirs(directory_path, exist_ok=True)
            
            # Create full file path
            file_path = os.path.join(directory_path, filename)
            logger.info(f"Full file path: {file_path}")
            
            # Generate markdown content
            logger.info("Generating markdown content")
            file_path = convert_blueprint_to_markdown(bp, output_dir)
            
            # Just add the created file path to our list if it was created successfully
            if file_path:
                created_files.append(file_path)
                logger.info(f"Added file to created_files list: {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing blueprint entry #{idx+1}: {str(e)}", exc_info=True)
    
    logger.info(f"Completed process_blueprint_files with {len(created_files)} files created")
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

def save_run_logs(original_input, json_output, blueprints, created_files, config):
    """Save artifacts from this run for debugging/reference."""
    # Create a log file with run information
    log_file = config.RUN_LOG_DIR / "run_summary.json"
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(original_input) if isinstance(original_input, Path) else "direct_input",
        "json_file": str(json_output) if isinstance(json_output, Path) else None,
        "blueprints": [str(b) if isinstance(b, Path) else b.get("file_info", {}) for b in blueprints],
        "created_files": [str(f) for f in created_files]
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
        
    # Copy the original input if it's a file
    if isinstance(original_input, Path) and original_input.exists():
        shutil.copy(original_input, config.RUN_LOG_DIR / original_input.name)
    
    return str(log_file)

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