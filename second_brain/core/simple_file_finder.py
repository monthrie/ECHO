#!/usr/bin/env python3
"""
Simple file finder that uses LLM to recommend relevant files for a blueprint.
Sends the raw blueprint and vault index to the LLM and gets recommendations.
"""

import json
import os
import argparse
import requests
from pathlib import Path
from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer
from second_brain.utils.simple_file_index import create_vault_index

def find_relevant_files(blueprint_path, vault_path=None):
    """Send the blueprint and vault index to LLM and get relevant file recommendations."""
    # Initialize config
    Config.initialize()
    
    # Initialize tracer
    tracer = SecondBrainTracer()
    
    # Use configured vault path if not provided
    vault_path = vault_path or Config.OBSIDIAN_VAULT_PATH
    
    # Load the blueprint
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    # Get or create the vault index
    index_path = create_vault_index(vault_path, output_file="temp_vault_index.json")
    with open(index_path, 'r', encoding='utf-8') as f:
        vault_index = json.load(f)
    
    # Prepare the prompt
    prompt = f"""You are a smart file finder. I have a new document (blueprint) and I want to know which existing files in my vault might be relevant to it.

BLUEPRINT:
{json.dumps(blueprint, indent=2)}

VAULT INDEX:
{json.dumps(vault_index, indent=2)}

Based on the content, tags, and descriptions, tell me which existing files from the vault index might be related to this blueprint.
Return a simple JSON array of the most relevant filepaths, with a relevance score and brief reason for each.

Example format:
```json
[
  {{
    "filepath": "path/to/file.md",
    "relevance": 0.87,
    "reason": "Short explanation"
  }}
]
```

If no files seem relevant, return an empty array.
"""

    # Call LLM API
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": Config.MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    
    # Trace the call
    result = response.json()
    llm_response = result["choices"][0]["message"]["content"]
    tracer.trace_openrouter_call(
        "find_relevant_files", 
        prompt, 
        llm_response, 
        {"model": Config.MODEL}
    )
    
    # Extract JSON from response (handle both code blocks and raw JSON)
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```|(\[[\s\S]*\])', llm_response)
    if json_match:
        json_str = json_match.group(1) or json_match.group(2)
        try:
            return json.loads(json_str)
        except:
            return {"error": "Failed to parse JSON", "raw_response": llm_response}
    else:
        return {"error": "No JSON found", "raw_response": llm_response}

def main():
    parser = argparse.ArgumentParser(description="Find relevant files for a blueprint")
    parser.add_argument("--blueprint", "-b", required=True, help="Path to blueprint file")
    parser.add_argument("--vault", "-v", help="Path to Obsidian vault (defaults to configured vault)")
    parser.add_argument("--output", "-o", help="Output file (optional, defaults to stdout)")
    
    args = parser.parse_args()
    
    # Find relevant files
    results = find_relevant_files(args.blueprint, args.vault)
    
    # Output results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main() 