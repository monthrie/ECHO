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
    # Use vault path from config if available
    if hasattr(Config, 'CURRENT_VAULT_DIR') and Config.CURRENT_VAULT_DIR:
        INPUT_DIR = Config.CURRENT_VAULT_DIR
    else:
        INPUT_DIR = str(BASE_DIR / "data" / "vaults" / "recomms_20250416_173815" / "markdown")
except ImportError:
    # Fallback if config import fails
    BASE_DIR = Path(__file__).parent.parent
    INPUT_DIR = str(BASE_DIR / "data" / "vaults" / "recomms_20250416_173815" / "markdown")

# Create embeddings directory under data
EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"
METADATA_FILE = EMBEDDINGS_DIR / "metadata.json"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.json"
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

def process_markdown_files() -> Tuple[Dict, Dict]:
    """Process all markdown files in the input directory."""
    # Create output directory if it doesn't exist
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing metadata and embeddings if they exist
    metadata = {}
    embeddings = {}
    
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    
    if EMBEDDINGS_FILE.exists():
        with open(EMBEDDINGS_FILE, 'r') as f:
            embeddings = json.load(f)
    
    # Scan input directory for markdown files
    input_dir = Path(INPUT_DIR)
    for file_path in input_dir.glob("**/*.md"):
        # Get relative path for storage
        relative_path = str(file_path.relative_to(input_dir))
        
        # Get file modification time
        mod_time = os.path.getmtime(file_path)
        
        # Check if file exists in metadata and has been modified
        file_metadata = metadata.get("files", {}).get(relative_path, {})
        file_id = file_metadata.get("id")
        last_mod_time = file_metadata.get("last_modified", 0)
        
        if not file_id or mod_time > last_mod_time:
            print(f"Processing: {relative_path}")
            
            # Extract content and frontmatter
            frontmatter, content = extract_markdown_content(file_path)
            
            # Generate a unique ID if needed
            if not file_id:
                file_id = f"doc_{len(metadata.get('files', {})) + 1}"
            
            # Prepare text for embedding
            full_text = prepare_text_for_embedding(frontmatter, content)
            
            # Generate embedding
            embedding = generate_embedding(full_text)
            
            # Update metadata
            if "files" not in metadata:
                metadata["files"] = {}
                
            metadata["files"][relative_path] = {
                "id": file_id,
                "last_modified": mod_time,
                "title": frontmatter.get("title", relative_path),
                "tags": frontmatter.get("tags", [])
            }
            
            # Update embeddings
            embeddings[file_id] = embedding
            
            print(f"Generated embedding for: {relative_path}")
        else:
            print(f"Skipping unchanged file: {relative_path}")
    
    # Save metadata and embeddings
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    with open(EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings, f, indent=2)
    
    print(f"Saved {len(metadata.get('files', {}))} file metadata entries and {len(embeddings)} embeddings")
    
    return metadata, embeddings

def find_similar_documents(query_text: str, metadata: Dict, embeddings: Dict, threshold: float = 0.85) -> List[Dict]:
    """Find similar documents to the query text."""
    import numpy as np
    
    # Generate embedding for query text
    query_embedding = generate_embedding(query_text)
    
    similar_docs = []
    
    # Calculate similarity with all stored embeddings
    for file_path, file_info in metadata.get("files", {}).items():
        doc_id = file_info["id"]
        doc_embedding = embeddings.get(doc_id)
        
        if doc_embedding:
            # Calculate cosine similarity
            a = np.array(query_embedding)
            b = np.array(doc_embedding)
            similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            if similarity >= threshold:
                similar_docs.append({
                    "file_path": file_path,
                    "title": file_info.get("title", ""),
                    "similarity": similarity,
                    "id": doc_id
                })
    
    # Sort by similarity (highest first)
    similar_docs.sort(key=lambda x: x["similarity"], reverse=True)
    
    return similar_docs

if __name__ == "__main__":
    print(f"Processing markdown files in: {INPUT_DIR}")
    start_time = time.time()
    
    metadata, embeddings = process_markdown_files()
    
    elapsed = time.time() - start_time
    print(f"Processing completed in {elapsed:.2f} seconds")
    
    # Optional: Test similarity search
    # If you want to test a search, uncomment the following lines:
    """
    test_query = "Your search query here"
    similar = find_similar_documents(test_query, metadata, embeddings)
    print("\nSimilar documents:")
    for doc in similar[:5]:  # Top 5 results
        print(f"- {doc['title']} ({doc['file_path']}): {doc['similarity']:.4f}")
    """
