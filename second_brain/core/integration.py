import json
import os
import argparse
from typing import Dict, List, Tuple, Any
import numpy as np
from openai import OpenAI
import re

# Initialize OpenAI client
client = OpenAI()

# Configuration
EMBEDDINGS_FILE = "document_embeddings.json"  # Placeholder for embeddings storage
MARKDOWN_DIR = "output/markdown"  # Directory containing existing markdown files
SIMILARITY_THRESHOLD = 0.85  # Minimum similarity score to consider updating

def load_document_embeddings() -> Dict[str, List[float]]:
    """Load document embeddings from storage."""
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_document_embeddings(embeddings: Dict[str, List[float]]):
    """Save document embeddings to storage."""
    with open(EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings, f)

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI API."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
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
    
    for doc_path, doc_embedding in doc_embeddings.items():
        similarity = cosine_similarity(embedding, doc_embedding)
        if similarity >= threshold:
            similar_docs.append((doc_path, similarity))
    
    # Sort by similarity (highest first)
    similar_docs.sort(key=lambda x: x[1], reverse=True)
    return similar_docs

def get_document_content(doc_path: str) -> str:
    """Get the content of a document."""
    with open(doc_path, 'r', encoding='utf-8') as f:
        return f.read()

def blueprint_to_text(blueprint: Dict[str, Any]) -> str:
    """Convert blueprint to text for embedding generation."""
    title = blueprint.get("content", {}).get("title", "")
    body = blueprint.get("content", {}).get("body", "")
    tags = blueprint.get("frontmatter", {}).get("tags", [])
    
    return f"Title: {title}\n\nTags: {', '.join(tags)}\n\nContent: {body}"

def determine_integration_strategy(blueprint: Dict[str, Any], 
                                  similar_docs: List[Tuple[str, float]]) -> Dict[str, Any]:
    """Use LLM to determine integration strategy."""
    # Prepare context with blueprint and similar documents
    blueprint_text = blueprint_to_text(blueprint)
    
    similar_docs_context = ""
    for doc_path, similarity in similar_docs[:3]:  # Limit to top 3 for simplicity
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
    
    # Call LLM API
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # Extract and parse JSON response
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
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
    
    if decision == "new":
        # Create new document from blueprint
        directory = blueprint.get("file_info", {}).get("directory", "")
        filename = blueprint.get("file_info", {}).get("filename", "")
        os.makedirs(os.path.join(MARKDOWN_DIR, directory), exist_ok=True)
        new_file_path = os.path.join(MARKDOWN_DIR, directory, filename)
        
        # Use LLM to format the document
        prompt = f"""
        I need to create a new markdown document from this blueprint:
        
        {json.dumps(blueprint, indent=2)}
        
        Please format this as a complete markdown document with frontmatter.
        The frontmatter should be enclosed in triple dashes (---) and include all the fields from the frontmatter section of the blueprint.
        The body should include the title as a level 1 heading, followed by the content.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        markdown_content = response.choices[0].message.content
        
        # Write to file
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Created new document: {new_file_path}")
        return new_file_path
    
    elif decision == "update" or decision == "merge":
        # Get existing document content
        existing_content = get_document_content(target_document)
        
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
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        updated_content = response.choices[0].message.content
        
        # Write updated content to file
        with open(target_document, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated document: {target_document}")
        return target_document
    
    else:
        print(f"Unknown decision: {decision}")
        return None

def process_blueprint(blueprint_path: str) -> str:
    """Process a single blueprint file for smart integration."""
    # Load blueprint
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
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
        doc_embeddings[result_path] = blueprint_embedding
        save_document_embeddings(doc_embeddings)
    
    return result_path

def main():
    parser = argparse.ArgumentParser(description='Smart Blueprint Integration')
    parser.add_argument('blueprint_path', help='Path to blueprint JSON file')
    args = parser.parse_args()
    
    result = process_blueprint(args.blueprint_path)
    print(f"Integration complete. Result: {result}")

if __name__ == "__main__":
    main()