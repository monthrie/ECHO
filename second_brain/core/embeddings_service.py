import os
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from openai import OpenAI

# Get the base directory from utils.config if possible
try:
    from second_brain.utils.config import Config
    BASE_DIR = Config.BASE_DIR
    # Override INPUT_DIR for testing
    INPUT_DIR = "/Users/wilmon/Documents/projects/ECHO/second_brain/data/vaults/recomms_20250416_171813/markdown/Resources/Recommendations"
except ImportError:
    # Fallback if config import fails
    BASE_DIR = Path(__file__).parent.parent
    # Override INPUT_DIR for testing
    INPUT_DIR = "/Users/wilmon/Documents/projects/ECHO/second_brain/data/vaults/recomms_20250416_171813/markdown/Resources/Recommendations"

# Create embeddings directory under data
EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"
# Replace separate files with a single consolidated file
CONSOLIDATED_FILE = EMBEDDINGS_DIR / "consolidated_embeddings.json"
EMBEDDING_MODEL = "text-embedding-3-small"

# Initialize OpenAI client
client = OpenAI()

def extract_markdown_content(file_path: Path) -> Tuple[Dict, str]:
    """Extract frontmatter and content from a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for YAML frontmatter between --- markers
    frontmatter = {}
    main_content = content
    
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            main_content = match.group(2)
        except yaml.YAMLError:
            pass
    
    return frontmatter, main_content.strip()

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI API."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def prepare_text_for_embedding(frontmatter: Dict, content: str) -> str:
    """Prepare text for embedding by combining relevant frontmatter and content."""
    title = frontmatter.get("title", "")
    tags = frontmatter.get("tags", [])
    tags_text = ", ".join(tags) if isinstance(tags, list) else str(tags)
    
    return f"Title: {title}\n\nTags: {tags_text}\n\nContent: {content}"

def process_markdown_files() -> Dict:
    """Process all markdown files in the input directory and store in consolidated format."""
    # Create output directory if it doesn't exist
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing consolidated data if it exists
    consolidated_data = {"documents": {}}
    
    if CONSOLIDATED_FILE.exists():
        with open(CONSOLIDATED_FILE, 'r') as f:
            consolidated_data = json.load(f)
            if "documents" not in consolidated_data:
                consolidated_data["documents"] = {}
    
    # Scan input directory for markdown files
    input_dir = Path(INPUT_DIR)
    for file_path in input_dir.glob("**/*.md"):
        # Get relative path for storage
        relative_path = str(file_path.relative_to(input_dir))
        
        # Get file modification time
        mod_time = os.path.getmtime(file_path)
        
        # Check if file exists in consolidated data and has been modified
        file_data = consolidated_data["documents"].get(relative_path, {})
        last_mod_time = file_data.get("last_modified", 0)
        
        if not file_data or mod_time > last_mod_time:
            print(f"Processing: {relative_path}")
            
            # Extract content and frontmatter
            frontmatter, content = extract_markdown_content(file_path)
            
            # Generate a unique ID if needed
            file_id = file_data.get("id")
            if not file_id:
                file_id = f"doc_{len(consolidated_data['documents']) + 1}"
            
            # Prepare text for embedding
            full_text = prepare_text_for_embedding(frontmatter, content)
            
            # Generate embedding
            embedding = generate_embedding(full_text)
            
            # Update consolidated data
            consolidated_data["documents"][relative_path] = {
                "id": file_id,
                "last_modified": mod_time,
                "title": frontmatter.get("title", relative_path),
                "tags": frontmatter.get("tags", []),
                "content": content,  # Store the actual content
                "embedding": embedding
            }
            
            print(f"Generated embedding for: {relative_path}")
        else:
            print(f"Skipping unchanged file: {relative_path}")
    
    # Save consolidated data
    with open(CONSOLIDATED_FILE, 'w') as f:
        json.dump(consolidated_data, f, indent=2)
    
    print(f"Saved {len(consolidated_data['documents'])} documents with embeddings to {CONSOLIDATED_FILE}")
    
    return consolidated_data

if __name__ == "__main__":
    print(f"Processing markdown files in: {INPUT_DIR}")
    start_time = time.time()
    
    consolidated_data = process_markdown_files()
    
    elapsed = time.time() - start_time
    print(f"Processing completed in {elapsed:.2f} seconds")
