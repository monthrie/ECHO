import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_anonymization():
    """
    Simple test function to verify the anonymization works with OpenRouter.
    """
    # Test text with PII
    test_text = """
    My name is John Smith and I live at 123 Main St, New York, NY 10001.
    My email is john.smith@example.com and my phone number is (555) 123-4567.
    I have a meeting with Dr. Sarah Johnson on 05/20/2023 at Memorial Hospital.
    """
    
    # Choose a model (you can change this)
    model = "meta-llama/llama-3.2-1b-instruct:free"
    
    print(f"Testing anonymization with model: {model}")
    print("Original text:")
    print(test_text)
    print("-" * 50)
    
    # Call the anonymization function
    result = anonymize_text(test_text, model)
    
    # Display results
    print("Anonymized text:")
    print(result["anonymized_text"])
    print("\nEntity mapping:")
    print(json.dumps(result["entity_mapping"], indent=2))

def anonymize_text(text, model="anthropic/claude-3.7-sonnet"):
    """
    Anonymize text using OpenRouter API with the specified model.
    
    Args:
        text (str): The text to anonymize
        model (str): The model to use
    
    Returns:
        dict: Contains anonymized text and entity mapping
    """
    prompt = f"""
    Identify all personally identifiable information (PII) in the following text and replace each instance with a suitable alias. 
    Preserve the context and relationships between entities. Return the anonymized text and a JSON mapping of original entities to aliases.

    Text:
    {text}

    Output format:
    {{
        "anonymized_text": "...",
        "entity_mapping": {{"original entity": "alias", ...}}
    }}
    """

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/your-repo",
        "X-Title": "PII Anonymizer Test"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Error from OpenRouter API: {response.text}")
    
    # Get the raw response content
    response_data = response.json()
    
    # Debug: Print the full response structure
    print("API Response structure:")
    print(json.dumps(response_data, indent=2))
    
    # Extract the content from the response
    output = response_data["choices"][0]["message"]["content"]
    
    print("\nRaw output from model:")
    print(output)
    
    # Try to parse the JSON from the output
    try:
        # First, try to find JSON in the output (it might be wrapped in markdown code blocks)
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find any JSON-like structure
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = output
        
        # Parse the JSON
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print("Attempting to extract information manually...")
        
        # Fallback: Try to extract information manually
        anonymized_text = output
        entity_mapping = {}
        
        # Look for patterns like "Original: X, Alias: Y"
        import re
        mapping_pattern = r'Original:\s*([^,]+),\s*Alias:\s*([^\n]+)'
        mappings = re.findall(mapping_pattern, output)
        
        for original, alias in mappings:
            entity_mapping[original.strip()] = alias.strip()
        
        return {
            "anonymized_text": anonymized_text,
            "entity_mapping": entity_mapping
        }

if __name__ == "__main__":
    test_anonymization() 