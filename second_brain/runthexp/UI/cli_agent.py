#!/usr/bin/env python3
"""
Simple RAG (Retrieval-Augmented Generation) system for a personal digital notebook.
Creates embeddings for markdown notes and allows querying them using an LLM.
"""

import json
import os
import argparse
import requests
import glob
from pathlib import Path
import datetime
import logging
from tqdm import tqdm
import sys

# Fix the import path to use absolute imports
project_root = str(Path(__file__).parent.parent.parent)  # Go up to the project root
if project_root not in sys.path:
    sys.path.append(project_root)

from second_brain.utils.config import Config
from second_brain.utils.simple_file_index import create_vault_index

# Constants
EMBEDDINGS_FILE = "note_embeddings.json"
DEFAULT_TOP_K = 5

def get_current_datetime_str():
    """Get current date and time as a formatted string."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_file_content(filepath):
    """Read and return the content of a file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def estimate_token_count(text):
    """Estimate the number of tokens in a text.
    
    This is a simple estimation - approximately 4 characters per token for English text.
    For more accurate counts, consider using a proper tokenizer like tiktoken.
    """
    return len(text) // 4

def chunk_text(text, max_tokens=8000):
    """Split text into chunks if it exceeds the token limit."""
    estimated_tokens = estimate_token_count(text)
    
    # If text is within token limit, return it as a single chunk
    if estimated_tokens <= max_tokens:
        return [text]
    
    # Otherwise, split into chunks
    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""
    current_tokens = 0
    
    for paragraph in paragraphs:
        paragraph_tokens = estimate_token_count(paragraph)
        
        # If a single paragraph exceeds token limit, split it by sentences
        if paragraph_tokens > max_tokens:
            sentences = paragraph.replace(". ", ".\n").split("\n")
            for sentence in sentences:
                sentence_tokens = estimate_token_count(sentence)
                if current_tokens + sentence_tokens > max_tokens:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                    current_tokens = sentence_tokens
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
                    current_tokens += sentence_tokens
        # Otherwise, try to add the paragraph to the current chunk
        elif current_tokens + paragraph_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = paragraph
            current_tokens = paragraph_tokens
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            current_tokens += paragraph_tokens
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def get_embedding(text):
    """Get embedding for a text using the OpenAI API."""
    try:
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "text-embedding-ada-002",
                "input": text
            }
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        logging.error(f"Error getting embedding: {e}")
        return None

def cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings."""
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    norm1 = sum(a * a for a in embedding1) ** 0.5
    norm2 = sum(b * b for b in embedding2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0
    
    return dot_product / (norm1 * norm2)

def create_note_embeddings(force_rebuild=False):
    """Create embeddings for all markdown files in the vault directory."""
    notes_dir = Config.OBSIDIAN_VAULT_PATH
    embeddings_path = Path(notes_dir) / EMBEDDINGS_FILE
    
    # Check if embeddings already exist
    if embeddings_path.exists() and not force_rebuild:
        with open(embeddings_path, 'r', encoding='utf-8') as f:
            print(f"Loading existing embeddings from {embeddings_path}")
            return json.load(f)
    
    # Find all markdown files
    md_files = sorted(glob.glob(str(Path(notes_dir) / "**" / "*.md"), recursive=True))
    
    if not md_files:
        print(f"No markdown files found in {notes_dir}")
        return []
    
    # Create embeddings for each file
    note_embeddings = []
    
    print(f"Creating embeddings for {len(md_files)} files...")
    for filepath in tqdm(md_files):
        try:
            relative_path = str(Path(filepath).relative_to(notes_dir))
            content = get_file_content(filepath)
            
            # Skip empty files
            if not content.strip():
                continue
            
            # Check if content needs to be chunked
            chunks = chunk_text(content)
            
            # Process each chunk
            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{relative_path}"
                if len(chunks) > 1:
                    chunk_id = f"{relative_path}#chunk{i+1}"
                
                # Get embedding for the chunk
                embedding = get_embedding(chunk_content)
                
                if embedding:
                    note_embeddings.append({
                        "filepath": chunk_id,
                        "embedding": embedding,
                        "preview": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content,
                        "original_path": relative_path
                    })
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    # Save embeddings to file
    with open(embeddings_path, 'w', encoding='utf-8') as f:
        json.dump(note_embeddings, f)
    
    print(f"Created embeddings for {len(note_embeddings)} chunks from {len(md_files)} files, saved to {embeddings_path}")
    return note_embeddings

def find_relevant_notes(query, note_embeddings, top_k=DEFAULT_TOP_K):
    """Find notes relevant to a query using embeddings."""
    if not note_embeddings:
        return []
    
    # Get embedding for the query
    query_embedding = get_embedding(query)
    
    if not query_embedding:
        return []
    
    # Calculate similarity scores
    scores = []
    for note in note_embeddings:
        similarity = cosine_similarity(query_embedding, note["embedding"])
        # Include original_path if available
        original_path = note.get("original_path", None)
        scores.append((note["filepath"], similarity, note["preview"], original_path))
    
    # Sort by similarity score (highest first)
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return top_k results
    return [
        {
            "filepath": filepath,
            "relevance": round(score, 3),
            "preview": preview,
            "original_path": original_path
        }
        for filepath, score, preview, original_path in scores[:top_k]
    ]

def query_llm(query, relevant_notes):
    """Query the LLM with the user's question and relevant notes using OpenRouter."""
    # Load the vault index
    vault_path = Config.OBSIDIAN_VAULT_PATH
    index_file = vault_path / "vault_index.json"
    
    # Create the index if it doesn't exist
    if not index_file.exists():
        create_vault_index(vault_path)
    
    # Load the vault index
    with open(index_file, 'r', encoding='utf-8') as f:
        vault_index = json.load(f)
    
    # Prepare the context from relevant notes
    context = ""
    for i, note in enumerate(relevant_notes, 1):
        # Use original_path if available (for proper citation), otherwise use filepath
        filepath = note.get('original_path', note['filepath'])
        context += f"\nNOTE {i}: {filepath}\n{note['preview']}\n"
    
    # Prepare the prompt
    date_str = get_current_datetime_str()
    prompt = f"""You are an AI assistant helping a user query their personal knowledge base.
The current date and time is: {date_str}

The user asked: "{query}"

VAULT STRUCTURE:
The entire notebook contains {len(vault_index)} notes with the following structure:
{json.dumps(vault_index, indent=2)}

I've found {len(relevant_notes)} potentially relevant notes from their knowledge base:
{context}

Based on these notes and the overall vault structure, please provide a comprehensive answer to the user's question.
If the user is asking about the structure or metadata of their vault (like number of notes, tags, directories),
use the VAULT STRUCTURE information to answer.
If the user is asking about specific content, use the relevant notes.
Include references to specific notes where appropriate using their file paths.

it might be that the user asks things that are outside of the scope of the vault - thats fine, just use your own knowledge to answer and say that you didnt find much relevant information in the vault...
"""

    # Call LLM API via OpenRouter
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": Config.MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": Config.TEMPERATURE
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error querying LLM: {e}"

def interactive_mode():
    """Run an interactive CLI for querying notes."""
    print(f"Loading embeddings from {Config.OBSIDIAN_VAULT_PATH}...")
    note_embeddings = create_note_embeddings()
    
    if not note_embeddings:
        print("No embeddings available. Please create embeddings first.")
        return
    
    print(f"\nLoaded {len(note_embeddings)} note embeddings")
    print("Enter your questions (type 'exit' or 'quit' to end):")
    
    while True:
        query = input("\n> ")
        if query.lower() in ('exit', 'quit'):
            break
        
        if not query.strip():
            continue
        
        print("\nFinding relevant notes...")
        relevant_notes = find_relevant_notes(query, note_embeddings)
        
        if not relevant_notes:
            print("No relevant notes found.")
            continue
        
        print(f"Found {len(relevant_notes)} relevant notes:")
        for i, note in enumerate(relevant_notes, 1):
            print(f"{i}. {note['filepath']} (relevance: {note['relevance']})")
        
        print("\nQuerying LLM...")
        response = query_llm(query, relevant_notes)
        
        print("\nResponse:")
        print(response)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Simple RAG system for personal notes")
    parser.add_argument("--rebuild", "-r", action="store_true", help="Force rebuild of embeddings")
    parser.add_argument("--query", "-q", help="Query to run (if not provided, enters interactive mode)")
    
    args = parser.parse_args()
    
    # Initialize the config first to create OBSIDIAN_VAULT_PATH
    Config.initialize()
    
    # Initialize the logger
    logger = Config.setup_logging()
    
    # Now OBSIDIAN_VAULT_PATH is available
    if not os.path.exists(Config.OBSIDIAN_VAULT_PATH):
        logger.error(f"Vault directory not found: {Config.OBSIDIAN_VAULT_PATH}")
        print(f"Error: Vault directory not found: {Config.OBSIDIAN_VAULT_PATH}")
        return
    
    # Create or load embeddings
    note_embeddings = create_note_embeddings(args.rebuild)
    
    if args.query:
        # Run a single query
        relevant_notes = find_relevant_notes(args.query, note_embeddings)
        if relevant_notes:
            print(f"Found {len(relevant_notes)} relevant notes:")
            for i, note in enumerate(relevant_notes, 1):
                print(f"{i}. {note['filepath']} (relevance: {note['relevance']})")
            
            response = query_llm(args.query, relevant_notes)
            print("\nResponse:")
            print(response)
        else:
            print("No relevant notes found.")
    else:
        # Run in interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()