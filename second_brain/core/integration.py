import json
import os
import argparse
from typing import Dict, List, Tuple, Any
import numpy as np
from openai import OpenAI
import re
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI()

# Configuration
BASE_DIR = Path(__file__).parent.parent
EMBEDDINGS_FILE = BASE_DIR / "data" / "embeddings" / "embeddings.json"
MARKDOWN_DIR = str(BASE_DIR / "data" / "vaults" / "recomms_20250416_173815" / "markdown")  # Directory containing existing markdown files
SIMILARITY_THRESHOLD = 0.85  # Minimum similarity score to consider updating

# Set this to your blueprints directory
BLUEPRINTS_DIR = BASE_DIR / "data" / "vaults" / "recomms_20250416_171813" / "blueprints"

def load_document_embeddings() -> Dict[str, List[float]]:
    """Load document embeddings from storage."""
    metadata_file = BASE_DIR / "data" / "embeddings" / "metadata.json"
    embeddings_file = EMBEDDINGS_FILE
    
    result = {}
    
    logger.info(f"Loading document embeddings from {embeddings_file}")
    logger.info(f"Using metadata from {metadata_file}")
    
    if embeddings_file.exists() and metadata_file.exists():
        with open(metadata_file, 'r') as mf:
            metadata = json.load(mf)
        
        with open(embeddings_file, 'r') as ef:
            embeddings = json.load(ef)
        
        logger.info(f"Found {len(metadata.get('files', {}))} files in metadata")
        logger.info(f"Found {len(embeddings)} embeddings")
        
        for file_path, file_info in metadata.get("files", {}).items():
            doc_id = file_info["id"]
            if doc_id in embeddings:
                result[file_path] = embeddings[doc_id]
    
    logger.info(f"Loaded {len(result)} document embeddings")
    return result

def save_document_embeddings(embeddings: Dict[str, List[float]]):
    """Save document embeddings to storage."""
    logger.info(f"Saving {len(embeddings)} document embeddings to {EMBEDDINGS_FILE}")
    with open(EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings, f)

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI API."""
    logger.info(f"Generating embedding for text of length {len(text)}")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    logger.info(f"Generated embedding with {len(response.data[0].embedding)} dimensions")
    return response.data[0].embedding

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_array = np.array(a)
    b_array = np.array(b)
    return np.dot(a_array, b_array) / (np.linalg.norm(a_array) * np.linalg.norm(b_array))

def find_similar_documents(embedding: List[float], 
                          doc_embeddings: Dict[str, List[float]], 
                          threshold: float = SIMILARITY_THRESHOLD) -> List[Tuple[str, float]]:
    """Find similar documents based on embedding similarity."""
    similar_docs = []
    
    logger.info(f"Finding similar documents among {len(doc_embeddings)} documents with threshold {threshold}")
    
    for doc_path, doc_embedding in doc_embeddings.items():
        similarity = cosine_similarity(embedding, doc_embedding)
        logger.info(f"Document: {doc_path} - Similarity: {similarity:.4f}")
        if similarity >= threshold:
            similar_docs.append((doc_path, similarity))
            logger.info(f"  ✓ Match found above threshold: {doc_path} - {similarity:.4f}")
    
    # Sort by similarity (highest first)
    similar_docs.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"Found {len(similar_docs)} similar documents above threshold {threshold}")
    
    # Print top matches for debugging
    for i, (doc_path, similarity) in enumerate(similar_docs[:5]):
        logger.info(f"  Top match #{i+1}: {doc_path} - Similarity: {similarity:.4f}")
    
    return similar_docs

def get_document_content(doc_path: str) -> str:
    """Get the content of a document."""
    # Convert relative path to absolute path
    full_path = os.path.join(MARKDOWN_DIR, doc_path)
    
    logger.info(f"Getting content for document: {doc_path}")
    logger.info(f"Full path: {full_path}")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Successfully read document of length {len(content)}")
            # Log a preview of the content
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"Content preview: {preview}")
            return content
    except FileNotFoundError:
        logger.error(f"Warning: Could not find file at {full_path}")
        logger.error(f"Relative path was: {doc_path}")
        logger.error(f"Markdown directory is: {MARKDOWN_DIR}")
        return ""

def blueprint_to_text(blueprint: Dict[str, Any]) -> str:
    """Convert blueprint to text for embedding generation."""
    title = blueprint.get("content", {}).get("title", "")
    body = blueprint.get("content", {}).get("body", "")
    tags = blueprint.get("frontmatter", {}).get("tags", [])
    
    result = f"Title: {title}\n\nTags: {', '.join(tags)}\n\nContent: {body}"
    logger.info(f"Converted blueprint to text of length {len(result)}")
    logger.info(f"Blueprint title: {title}")
    logger.info(f"Blueprint tags: {tags}")
    return result

def determine_integration_strategy(blueprint: Dict[str, Any], 
                                  similar_docs: List[Tuple[str, float]]) -> Dict[str, Any]:
    """Use LLM to determine integration strategy."""
    # Prepare context with blueprint and similar documents
    blueprint_text = blueprint_to_text(blueprint)
    
    logger.info(f"Determining integration strategy for blueprint")
    logger.info(f"Blueprint title: {blueprint.get('content', {}).get('title', 'Untitled')}")
    logger.info(f"Similar documents count: {len(similar_docs)}")
    
    similar_docs_context = ""
    for doc_path, similarity in similar_docs[:3]:  # Limit to top 3 for simplicity
        logger.info(f"Getting content for similar document: {doc_path} (Similarity: {similarity:.4f})")
        doc_content = get_document_content(doc_path)
        similar_docs_context += f"\n\n--- Document: {doc_path} (Similarity: {similarity:.2f}) ---\n{doc_content}"
    
    # Simple prompt for the LLM
    prompt = f"""
    I need to determine how to integrate a new document into my knowledge base.
    
    NEW DOCUMENT:
    {blueprint_text}
    
    SIMILAR EXISTING DOCUMENTS:
    {similar_docs_context if similar_docs_context else "No similar documents found."}
    
    Please analyze and determine the best integration approach:
    1. Should I create a new document? (If the content is sufficiently distinct)
    2. Should I update an existing document? (If the content is related and adds new information)
    3. Should I merge with an existing document? (If the content overlaps significantly)
    
    Provide your decision in JSON format:
    {{
      "decision": "new|update|merge",
      "target_document": "path/to/document.md or null if new",
      "reason": "brief explanation",
      "integration_instructions": "specific instructions for how to integrate"
    }}
    """
    
    logger.info("Sending prompt to LLM for integration strategy decision")
    
    # Call LLM API
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # Extract and parse JSON response
    try:
        result = json.loads(response.choices[0].message.content)
        logger.info(f"LLM decision: {result['decision']}")
        logger.info(f"Target document: {result['target_document']}")
        logger.info(f"Reason: {result['reason']}")
        return result
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        logger.error("Failed to parse LLM response as JSON")
        logger.error(f"Raw response: {response.choices[0].message.content}")
        return {
            "decision": "new",
            "target_document": None,
            "reason": "Failed to parse LLM response",
            "integration_instructions": "Create new document"
        }

def execute_integration(blueprint: Dict[str, Any], 
                       integration_strategy: Dict[str, Any]) -> str:
    """Execute the integration strategy using LLM to perform the actual integration."""
    decision = integration_strategy["decision"]
    target_document = integration_strategy["target_document"]
    
    logger.info(f"Executing integration with decision: {decision}")
    logger.info(f"Target document: {target_document}")
    
    if decision == "new":
        # Create new document from blueprint
        directory = blueprint.get("file_info", {}).get("directory", "")
        filename = blueprint.get("file_info", {}).get("filename", "")
        os.makedirs(os.path.join(MARKDOWN_DIR, directory), exist_ok=True)
        new_file_path = os.path.join(MARKDOWN_DIR, directory, filename)
        
        logger.info(f"Creating new document at: {new_file_path}")
        
        # Use LLM to format the document
        prompt = f"""
        I need to create a new markdown document from this blueprint:
        
        {json.dumps(blueprint, indent=2)}
        
        Please format this as a complete markdown document with frontmatter.
        The frontmatter should be enclosed in triple dashes (---) and include all the fields from the frontmatter section of the blueprint.
        The body should include the title as a level 1 heading, followed by the content.
        """
        
        logger.info("Sending prompt to LLM for new document creation")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        markdown_content = response.choices[0].message.content
        
        # Log a preview of the generated content
        preview = markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content
        logger.info(f"Generated markdown content preview: {preview}")
        
        # Write to file
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Created new document: {new_file_path}")
        return new_file_path
    
    elif decision == "update" or decision == "merge":
        # Get existing document content
        existing_content = get_document_content(target_document)
        
        # IMPORTANT: Convert target_document to full path for writing
        full_target_path = os.path.join(MARKDOWN_DIR, target_document)
        
        logger.info(f"Updating/merging document at: {full_target_path}")
        logger.info(f"Existing content length: {len(existing_content)}")
        
        # Use LLM to perform the update/merge
        prompt = f"""
        I need to {decision} content from a new blueprint into an existing document.
        
        EXISTING DOCUMENT:
        {existing_content}
        
        NEW BLUEPRINT:
        {json.dumps(blueprint, indent=2)}
        
        INTEGRATION INSTRUCTIONS:
        {integration_strategy["integration_instructions"]}
        
        Please provide the complete updated markdown document that incorporates the new content according to the integration instructions.
        Make sure to:
        1. Preserve the document structure
        2. Merge frontmatter appropriately (especially tags and record_ids)
        3. Integrate the content in a coherent way
        4. Resolve any conflicts or redundancies
        """
        
        logger.info("Sending prompt to LLM for document update/merge")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        updated_content = response.choices[0].message.content
        
        # Log a preview of the updated content
        preview = updated_content[:200] + "..." if len(updated_content) > 200 else updated_content
        logger.info(f"Updated content preview: {preview}")
        
        # Write updated content to file using the FULL PATH
        with open(full_target_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"Updated document: {full_target_path}")
        return target_document
    
    else:
        logger.error(f"Unknown decision: {decision}")
        return None

def process_blueprint(blueprint_path: str) -> str:
    """Process a single blueprint file for smart integration."""
    logger.info(f"Processing blueprint: {blueprint_path}")
    
    # Load blueprint
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    # Log blueprint details
    logger.info(f"Blueprint title: {blueprint.get('content', {}).get('title', 'Untitled')}")
    logger.info(f"Blueprint directory: {blueprint.get('file_info', {}).get('directory', '')}")
    logger.info(f"Blueprint filename: {blueprint.get('file_info', {}).get('filename', '')}")
    
    # Load existing document embeddings
    doc_embeddings = load_document_embeddings()
    
    # Generate embedding for blueprint
    blueprint_text = blueprint_to_text(blueprint)
    blueprint_embedding = generate_embedding(blueprint_text)
    
    # Find similar documents
    similar_docs = find_similar_documents(blueprint_embedding, doc_embeddings)
    
    # Determine integration strategy
    integration_strategy = determine_integration_strategy(blueprint, similar_docs)
    
    # Execute integration
    result_path = execute_integration(blueprint, integration_strategy)
    
    # Update embeddings if needed
    if integration_strategy["decision"] == "new":
        # Add new document embedding
        logger.info(f"Adding new document embedding for: {result_path}")
        doc_embeddings[result_path] = blueprint_embedding
        save_document_embeddings(doc_embeddings)
    
    logger.info(f"Blueprint processing complete. Result: {result_path}")
    return result_path

def process_all_blueprints():
    """Process all blueprint files in the BLUEPRINTS_DIR."""
    if not BLUEPRINTS_DIR.exists():
        logger.error(f"Blueprint directory not found: {BLUEPRINTS_DIR}")
        return
    
    blueprint_files = list(BLUEPRINTS_DIR.glob("*.json"))
    logger.info(f"Found {len(blueprint_files)} blueprint files")
    
    for blueprint_path in blueprint_files:
        logger.info(f"\nProcessing blueprint: {blueprint_path.name}")
        result = process_blueprint(str(blueprint_path))
        logger.info(f"Integration result: {result}")

def main():
    parser = argparse.ArgumentParser(description='Smart Blueprint Integration')
    parser.add_argument('--blueprint', help='Path to blueprint JSON file')
    parser.add_argument('--all', action='store_true', help='Process all blueprints in the BLUEPRINTS_DIR')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    
    if args.all:
        process_all_blueprints()
    elif args.blueprint:
        result = process_blueprint(args.blueprint)
        logger.info(f"Integration complete. Result: {result}")
    else:
        logger.error("Please specify either --blueprint or --all")
        parser.print_help()

if __name__ == "__main__":
    main()