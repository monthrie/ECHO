import json
import os
import argparse
from typing import Dict, List, Any
import numpy as np
from openai import OpenAI
from pathlib import Path
import logging
import requests
from second_brain.utils.config import Config
import langsmith
from langsmith import Client as LangSmithClient
from second_brain.utils.langsmith_tracer import SecondBrainTracer

# Set up logging
log_file = "integration.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Keep console output too
    ]
)
logger = logging.getLogger(__name__)
logger.info("Starting integration process with logging to file")

# Initialize OpenAI client
client = OpenAI()

# Initialize LangSmith client if configured
try:
    langsmith_client = LangSmithClient()
    langsmith_tracing_enabled = True
    
    # Log LangSmith configuration details
    logger.info("LangSmith tracing enabled")
    logger.info(f"LangSmith API URL: {os.environ.get('LANGCHAIN_ENDPOINT', 'Not set')}")
    logger.info(f"LangSmith Project: {os.environ.get('LANGCHAIN_PROJECT', 'Not set')}")
    logger.info(f"LangSmith API Key: {'Set (redacted)' if os.environ.get('LANGCHAIN_API_KEY') else 'Not set'}")
    
    # Test LangSmith connection
    try:
        # Try to list projects to verify connection
        projects = langsmith_client.list_projects()
        project_names = [p.name for p in projects]
        logger.info(f"Successfully connected to LangSmith. Available projects: {project_names}")
    except Exception as e:
        logger.error(f"LangSmith connection test failed: {e}")
except Exception as e:
    logger.warning(f"LangSmith client initialization failed: {e}")
    langsmith_tracing_enabled = False

# Initialize SecondBrainTracer
tracer = SecondBrainTracer()

# Configuration
BASE_DIR = Path(__file__).parent.parent
CONSOLIDATED_EMBEDDINGS_FILE = BASE_DIR / "data" / "embeddings" / "consolidated_embeddings_20250420_180619.json"
MARKDOWN_DIR = str(BASE_DIR / "data" / "vaults" / "recomms_20250420_180619" / "markdown")
SIMILARITY_THRESHOLD = 0.50  # Minimum similarity score to consider for comparison
PROMPT_FILE = BASE_DIR / "prompts" / "integration_prompt.txt"

# Set this to your blueprints directory for testing
BLUEPRINTS_DIR = Path("/Users/wilmon/Documents/projects/ECHO/second_brain/data/vaults/recomms_20250416_173815/blueprints")

def load_prompt() -> str:
    """Load the integration prompt from file."""
    if PROMPT_FILE.exists():
        with open(PROMPT_FILE, 'r') as f:
            return f.read()
    else:
        # Fallback prompt if file doesn't exist
        return """
        I need to integrate a new document into my knowledge base.
        
        NEW DOCUMENT:
        {blueprint_text}
        
        SIMILAR EXISTING DOCUMENTS:
        {similar_docs_context}
        
        Please analyze and determine the best integration approach:
        1. Create a new document (if the content is sufficiently distinct)
        2. Update an existing document (if the content is related and adds new information)
        3. Merge with an existing document (if the content overlaps significantly)
        
        For each document that should be created or updated, provide the complete markdown content.
        Include appropriate frontmatter enclosed in triple dashes (---).
        
        IMPORTANT FORMATTING GUIDELINES FOR OBSIDIAN:
        - Do NOT include an H1 heading with the title - Obsidian already displays the title from frontmatter
        - Start document content with H2 headings
        - Maintain consistent heading hierarchy (H2 > H3 > H4)
        - Preserve existing document structure when updating
        - Remove any duplicate headings
        
        FORMAT YOUR RESPONSE AS FOLLOWS:
        
        DECISION: [new|update|merge]
        REASON: [brief explanation of your decision]
        
        DOCUMENT 1:
        Filepath: [path/to/document.md]
        ```markdown
        ---
        [frontmatter]
        ---
        
        [document content starting with H2 headings]
        ```
        
        [Repeat for additional documents if needed]
        """

def load_consolidated_embeddings(tracer) -> Dict:
    """Load consolidated document embeddings from storage."""
    embeddings_file = CONSOLIDATED_EMBEDDINGS_FILE
    
    logger.info(f"Loading consolidated embeddings from {embeddings_file}")
    
    if embeddings_file.exists():
        with open(embeddings_file, 'r') as f:
            consolidated_data = json.load(f)
        
        logger.info(f"Found {len(consolidated_data.get('documents', {}))} documents in consolidated embeddings")
        return consolidated_data
    else:
        logger.warning(f"Consolidated embeddings file not found: {embeddings_file}")
        return {"documents": {}}

def generate_embedding(text: str, tracer) -> List[float]:
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

def find_similar_documents(embedding: List[float], consolidated_data: Dict, tracer, threshold: float = SIMILARITY_THRESHOLD) -> List[Dict]:
    """Find similar documents based on embedding similarity."""
    similar_docs = []
    
    documents = consolidated_data.get("documents", {})
    logger.info(f"Finding similar documents among {len(documents)} documents with threshold {threshold}")
    
    for doc_path, doc_data in documents.items():
        doc_embedding = doc_data.get("embedding")
        if doc_embedding:
            similarity = cosine_similarity(embedding, doc_embedding)
            logger.info(f"Document: {doc_path} - Similarity: {similarity:.4f}")
            if similarity >= threshold:
                similar_docs.append({
                    "path": doc_path,
                    "similarity": similarity,
                    "content": doc_data.get("content", ""),
                    "title": doc_data.get("title", doc_path)
                })
                logger.info(f"  ✓ Match found above threshold: {doc_path} - {similarity:.4f}")
    
    # Sort by similarity (highest first)
    similar_docs.sort(key=lambda x: x["similarity"], reverse=True)
    logger.info(f"Found {len(similar_docs)} similar documents above threshold {threshold}")
    
    # Print top matches for debugging
    for i, doc in enumerate(similar_docs[:3]):
        logger.info(f"  Top match #{i+1}: {doc['path']} - Similarity: {doc['similarity']:.4f}")
    
    return similar_docs[:3]  # Return top 3 similar documents

def blueprint_to_text(blueprint: Dict[str, Any], tracer) -> str:
    """Convert blueprint to text for embedding generation and LLM context."""
    title = blueprint.get("content", {}).get("title", "")
    body = blueprint.get("content", {}).get("body", "")
    tags = blueprint.get("frontmatter", {}).get("tags", [])
    
    # Include file info for context
    directory = blueprint.get("file_info", {}).get("directory", "")
    filename = blueprint.get("file_info", {}).get("filename", "")
    filepath = os.path.join(directory, filename) if directory else filename
    
    result = f"""
    TITLE: {title}
    TAGS: {', '.join(tags)}
    PROPOSED FILEPATH: {filepath}
    
    CONTENT:
    {body}
    """
    
    logger.info(f"Converted blueprint to text of length {len(result)}")
    logger.info(f"Blueprint title: {title}")
    logger.info(f"Blueprint tags: {tags}")
    logger.info(f"Blueprint filepath: {filepath}")
    
    return result

def call_llm(prompt: str, tracer) -> str:
    """Call LLM using OpenRouter API with LangSmith tracing."""
    logger.info(f"Calling LLM using OpenRouter with model: {Config.MODEL}")
    
    try:
        # Make the API call
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
                ]
            }
        )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return "ERROR: Failed to get response from LLM"
        
        response_json = response.json()
        result = response_json["choices"][0]["message"]["content"].strip()
        
        # Trace the call using trace_openrouter_call
        logger.info("Tracing LLM call with tracer.trace_openrouter_call")
        metadata = {
            "model": Config.MODEL,
            "temperature": 0.7,
            "source": "integration_one_call.py"
        }
        trace_result = tracer.trace_openrouter_call("integration_decision", prompt, result, metadata)
        logger.info(f"Trace result: {trace_result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return f"ERROR: {str(e)}"

def process_blueprint(blueprint_path: str, tracer) -> List[str]:
    """Process a single blueprint file for smart integration."""
    logger.info(f"Processing blueprint: {blueprint_path}")
    
    # Load blueprint
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    # Log blueprint details
    logger.info(f"Blueprint title: {blueprint.get('content', {}).get('title', 'Untitled')}")
    logger.info(f"Blueprint directory: {blueprint.get('file_info', {}).get('directory', '')}")
    logger.info(f"Blueprint filename: {blueprint.get('file_info', {}).get('filename', '')}")
    
    # Load consolidated embeddings
    consolidated_data = load_consolidated_embeddings(tracer)
    
    # Generate embedding for blueprint
    blueprint_text = blueprint_to_text(blueprint, tracer)
    blueprint_embedding = generate_embedding(blueprint_text, tracer)
    
    # Find similar documents
    similar_docs = find_similar_documents(blueprint_embedding, consolidated_data, tracer)
    
    # Prepare context for LLM
    similar_docs_context = ""
    for i, doc in enumerate(similar_docs):
        similar_docs_context += f"""
        DOCUMENT {i+1}:
        Filepath: {doc['path']}
        Similarity: {doc['similarity']:.4f}
        
        ```markdown
        {doc['content']}
        ```
        
        """
    
    # Load prompt template
    prompt_template = load_prompt()
    
    # Format prompt with blueprint and similar documents
    prompt = prompt_template.format(
        blueprint_text=blueprint_text,
        similar_docs_context=similar_docs_context if similar_docs else "No similar documents found."
    )
    
    # Log the prompt being sent to the LLM
    logger.info("Sending the following prompt to LLM:")
    logger.info("=" * 80)
    logger.info(prompt)
    logger.info("=" * 80)
    
    # Call LLM API
    logger.info(f"Calling LLM using OpenRouter with model: {Config.MODEL}")
    llm_response = call_llm(prompt, tracer)
    
    # Log LLM response
    logger.info("LLM Response:")
    logger.info("-" * 80)
    logger.info(llm_response)
    logger.info("-" * 80)
    
    # Process LLM response to extract documents
    created_files = []
    
    # Parse the response to extract documents
    # This is a simple parser that looks for markdown code blocks
    import re
    
    # Extract decision and reason
    decision_match = re.search(r'DECISION:\s*(\w+)', llm_response)
    reason_match = re.search(r'REASON:\s*(.+?)(?:\n\n|\n\w+:)', llm_response, re.DOTALL)
    
    decision = decision_match.group(1) if decision_match else "unknown"
    reason = reason_match.group(1).strip() if reason_match else "No reason provided"
    
    logger.info(f"Integration decision: {decision}")
    logger.info(f"Reason: {reason}")
    
    # Extract documents
    filepath_pattern = r'Filepath:\s*([^\n]+)'
    markdown_pattern = r'```markdown\s*([\s\S]*?)\s*```'
    
    filepath_matches = re.finditer(filepath_pattern, llm_response)
    markdown_matches = re.finditer(markdown_pattern, llm_response)
    
    filepaths = [match.group(1).strip() for match in filepath_matches]
    markdown_contents = [match.group(1) for match in markdown_matches]
    
    # Ensure we have matching filepaths and contents
    if len(filepaths) != len(markdown_contents):
        logger.error(f"Mismatch between filepaths ({len(filepaths)}) and markdown contents ({len(markdown_contents)})")
        return []
    
    # Write each document to file
    for filepath, content in zip(filepaths, markdown_contents):
        # Ensure the filepath is valid
        if not filepath:
            logger.error("Empty filepath detected, skipping")
            continue
        
        # Create full path
        full_path = os.path.join(MARKDOWN_DIR, filepath)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write content to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Created/updated document: {full_path}")
        created_files.append(full_path)
    
    return created_files

def process_all_blueprints():
    """Process all blueprint files in the BLUEPRINTS_DIR."""
    if not BLUEPRINTS_DIR.exists():
        logger.error(f"Blueprint directory not found: {BLUEPRINTS_DIR}")
        return
    
    blueprint_files = list(BLUEPRINTS_DIR.glob("*.json"))
    logger.info(f"Found {len(blueprint_files)} blueprint files")
    
    all_created_files = []
    
    for blueprint_path in blueprint_files:
        logger.info(f"\nProcessing blueprint: {blueprint_path.name}")
        created_files = process_blueprint(str(blueprint_path), tracer)
        logger.info(f"Integration result: {created_files}")
        all_created_files.extend(created_files)
    
    logger.info(f"Total files created/updated: {len(all_created_files)}")
    for file in all_created_files:
        logger.info(f"  - {file}")

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
        created_files = process_blueprint(args.blueprint, tracer)
        logger.info(f"Integration complete. Files created/updated: {created_files}")
    else:
        logger.error("Please specify either --blueprint or --all")
        parser.print_help()

if __name__ == "__main__":
    main()
