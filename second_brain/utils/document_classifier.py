from pathlib import Path
import sys
import argparse
import json
from typing import Dict, Any
import requests
import logging

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer
from second_brain.utils.date_utils import get_current_datetime_str


def _classify_document(content, document_type_descriptions):
    """
    Classify a document based on its content.
    
    Args:
        content: The document content to classify
        document_type_descriptions: Dictionary mapping document types to descriptions
        
    Returns:
        Document type as a string
    """
    # Initialize Config and tracer
    Config.initialize()
    tracer = SecondBrainTracer()
    
    # Format the document type descriptions for the prompt
    formatted_descriptions = "\n".join([f"- {doc_type}: {description}" for doc_type, description in document_type_descriptions.items()])
    
    # Add current date and time
    date_str = get_current_datetime_str()
    
    # Create the prompt
    prompt = f"""The current date and time is: {date_str}

I need to classify a document into one of the following types:

{formatted_descriptions}

Here is the document content:
{content}

Please respond with ONLY the document type (one of the options above) that best matches the content.
"""
    
    # Call OpenRouter API
    try:
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
                    {"role": "system", "content": "You are a document classification assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
        )
        
        if response.status_code != 200:
            logging.error(f"Error from OpenRouter API: {response.status_code} {response.text}")
            return "unknown"
            
        response_json = response.json()
        result = response_json["choices"][0]["message"]["content"].strip()
        
        # Trace the call
        metadata = {
            "model": Config.MODEL,
            "temperature": 0.2,
            "source": "document_classifier.py"
        }
        tracer.trace_openrouter_call("document_classification", prompt, result, metadata)
        
        # Ensure the result is one of the expected document types
        if result in document_type_descriptions:
            return result
        else:
            logging.warning(f"Unexpected document type: {result}. Using 'unknown' instead.")
            return "unknown"
        
    except Exception as e:
        logging.error(f"Error calling OpenRouter API: {str(e)}")
        return "unknown"


def classify_document(document_path: str) -> Dict[str, Any]:
    """
    Classify a document as either a transcript or an article using an LLM.
    
    Args:
        document_path: Path to the document to classify
        
    Returns:
        A dictionary with the classification result
    """
    # Initialize config
    if not hasattr(Config, 'MODEL'):
        Config.initialize()
    
    # Read the document content
    try:
        with open(document_path, 'r', encoding='utf-8') as f:
            document_content = f.read()
    except Exception as e:
        print(f"Error reading document: {e}")
        return {"error": str(e)}
    
    # Prepare sample for classification
    # If document is long, only use the first ~2000 chars for classification
    sample = document_content[:2000]
    
    # Create the prompt for classification
    classification_prompt = f"""
    Your task is to classify the following document as either a "transcript" or an "article".
    
    if its an article it might have a bit of instructions at the beginning like "summarize this" or "extract key concepts" etc. this should still be classified as an article. if its more like personal notes or a journal entry it should be classified as a transcript.
    
    Document sample to classify:
    ```
    {sample}
    ```
    
    Respond ONLY with a valid JSON object containing a single key "document_type" 
    with a value of either "transcript" or "article".
    """
    
    # Initialize the language model
    model = Config.MODEL
    
    # Make the classification request
    result = _classify_document(sample, {"transcript": "A transcript is a personal note or journal entry.", "article": "An article is a written piece with instructions or a summary."})
    
    # Parse the JSON response
    try:
        print(f"Document classified as: {result}")
        return {"document_type": result}
    except Exception as e:
        # If any error occurs, return a generic error message
        print(f"Error classifying document: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Hardcoded document path
    document_path = "/Users/wilmon/Documents/projects/ECHO/second_brain/data/input/substack_article.txt"
    print(f"Classifying document: {document_path}")
    
    result = classify_document(document_path)
    
    # Print the result
    print(json.dumps(result, indent=2))
    
    # Optionally save to file
    output_path = "classification_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"Classification result saved to {output_path}")