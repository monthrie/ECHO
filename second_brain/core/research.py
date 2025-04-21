import argparse
import json
import os
import re
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

from second_brain.utils.config import Config
from second_brain.utils.langsmith_tracer import SecondBrainTracer

# Initialize tracer
tracer = SecondBrainTracer()

def search_duckduckgo(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo for a query and return results.
    Uses the duckduckgo-search library.
    """
    try:
        # Try to import the library
        from duckduckgo_search import DDGS
    except ImportError:
        print("Error: duckduckgo-search package not found.")
        print("Please install it with: pip install duckduckgo-search")
        return []
    
    print(f"Searching DuckDuckGo for: {query}")
    
    try:
        # Create the DDGS client
        ddgs = DDGS()
        
        # Perform the search
        raw_results = ddgs.text(query, max_results=num_results)
        print(f"Found {len(raw_results)} raw results")
        
        # Format results
        results = []
        for result in raw_results:
            results.append({
                "title": result.get("title", "No Title"),
                "content": result.get("body", "No Content Available"),
                "source": result.get("href", "")
            })
        
        print(f"Processed {len(results)} search results")
        return results
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
        import traceback
        traceback.print_exc()
        return []

def call_llm(prompt: str, tracer=None) -> str:
    """Call LLM using OpenRouter API with LangSmith tracing."""
    print(f"Calling LLM using OpenRouter with model: {Config.MODEL}")
    
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
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
        )
        
        if response.status_code != 200:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return "ERROR: Failed to get response from LLM"
        
        response_json = response.json()
        result = response_json["choices"][0]["message"]["content"].strip()
        
        # Trace the call if tracer is available
        if tracer:
            metadata = {
                "model": Config.MODEL,
                "temperature": 0.3,
                "source": "research_query.py"
            }
            trace_result = tracer.trace_openrouter_call("research_answer", prompt, result, metadata)
            print(f"Traced research query with LangSmith")
        
        return result
    
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return f"ERROR: {str(e)}"

def get_answer_from_llm(query: str, search_results: List[Dict[str, str]], tracer=None) -> str:
    """
    Send the search results to the LLM model to get a parsed answer.
    """
    # Format the search results for the prompt
    formatted_results = ""
    for i, result in enumerate(search_results, 1):
        formatted_results += f"Source {i}: {result['title']}\n"
        formatted_results += f"Content: {result['content']}\n"
        formatted_results += f"URL: {result['source']}\n\n"
    
    # Create the prompt for the LLM
    prompt = f"""
    Research Question: {query}
    
    Search Results:
    {formatted_results}
    
    Based on the search results above, please provide a clear, concise answer to the research question.
    If the information is not sufficient, please indicate what's missing.
    Include sources where appropriate.
    """
    
    # Get the answer from the LLM
    return call_llm(prompt, tracer)

def evaluate_query_needs_search(query: str, tracer=None) -> bool:
    """
    Have the LLM evaluate whether the query requires a web search
    or can be answered from its existing knowledge.
    """
    prompt = f"""
    Consider the following research question:
    
    "{query}"
    
    Determine whether this question:
    1. Can be answered using your existing knowledge (general knowledge, facts, concepts, etc.)
    2. Requires a web search for up-to-date information, specific data, recent events, etc.
    
    Reply with ONLY "NEEDS_SEARCH" or "CAN_ANSWER_DIRECTLY".
    """
    
    print(f"Evaluating if query needs web search: {query}")
    response = call_llm(prompt, tracer)
    
    # Look for the decision in the response
    needs_search = "NEEDS_SEARCH" in response.upper()
    print(f"Evaluation result: {'Needs search' if needs_search else 'Can answer directly'}")
    
    return needs_search

def get_direct_answer_from_llm(query: str, tracer=None) -> str:
    """
    Get an answer directly from the LLM without performing a web search.
    """
    prompt = f"""
    Research Question: {query}
    
    Please provide a comprehensive answer to this question based on your knowledge.
    If you're unsure about any specific details, please indicate that.
    """
    
    print(f"Getting direct answer from LLM for: {query}")
    return call_llm(prompt, tracer)

def research_query(query: str, tracer=None) -> str:
    """
    Main function to handle the research process.
    Takes a query, evaluates if it needs searching, and gets an answer from the LLM.
    """
    print(f"Researching: {query}")
    
    # First, evaluate if this query requires a web search
    needs_search = evaluate_query_needs_search(query, tracer)
    
    if not needs_search:
        # Get answer directly from LLM if no search is needed
        print("Query can be answered directly, skipping web search")
        return get_direct_answer_from_llm(query, tracer)
    
    # If we get here, we need to search
    print("Query requires web search for accurate information")
    search_results = search_duckduckgo(query)
    
    if not search_results:
        return "Sorry, I couldn't find any relevant information for your query."
    
    # Get the answer from the LLM
    answer = get_answer_from_llm(query, search_results, tracer)
    
    return answer

def save_result_to_markdown(query: str, answer: str, output_dir: str = None) -> str:
    """
    Save the research results to a markdown file.
    """
    # Use the configured vault directory if available, or fall back to current directory
    if output_dir is None:
        if hasattr(Config, 'MARKDOWN_OUTPUT_DIR') and Config.MARKDOWN_OUTPUT_DIR:
            output_dir = Config.MARKDOWN_OUTPUT_DIR
        else:
            output_dir = "research_results"
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a filename based on the query
    sanitized_query = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')
    filename = f"research_{sanitized_query[:40]}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Create the markdown content
    content = f"""---
title: "Research: {query}"
tags: [research, query]
created: {datetime.now().strftime('%Y-%m-%d')}
---

## Research Question
{query}

## Answer
{answer}
"""
    
    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Saved research results to: {filepath}")
    return filepath

def main():
    # Import datetime only when needed to avoid circular import issues
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Research Query Tool")
    parser.add_argument("query", type=str, help="The research query to look up")
    parser.add_argument("--save", action="store_true", help="Save the result to a markdown file")
    parser.add_argument("--output-dir", type=str, help="Directory to save the markdown file (if --save is used)")
    args = parser.parse_args()
    
    # Get the answer
    answer = research_query(args.query, tracer)
    
    # Print the answer
    print("\nAnswer:")
    print(answer)
    
    # Save the result if requested
    if args.save:
        filepath = save_result_to_markdown(args.query, answer, args.output_dir)
        print(f"\nResults saved to: {filepath}")

if __name__ == "__main__":
    main()
