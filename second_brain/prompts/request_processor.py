import json

def get_request_detection_prompt(transcript):
    """
    Create a prompt to detect if the user is asking for advice, recommendations, or analysis.
    """
    return f"""
# Request Detection and Response System

## Purpose
Analyze the provided text and determine if the user is asking for advice, recommendations, analysis, or other actionable responses. If such requests are detected, generate appropriate responses.

## Input Text
```
{transcript}
```

## Instructions

1. Carefully analyze the text to identify any:
   - Direct questions ("What do you recommend?", "What should I do?")
   - Requests for advice or suggestions
   - Requests for analysis or evaluation
   - Requests for planning or strategizing

2. If no requests are detected:
   - Return a JSON object with "requests_detected": false

3. If requests are detected:
   - Generate thorough, thoughtful responses to each request
   - Consider the full context of the user's situation
   - Provide actionable, specific advice rather than generic statements
   - Structure your response in a clear, organized manner
   - Label your response as "AI Assistant's Response" to distinguish it from the user's original text

4. Return a JSON object with:
   - "requests_detected": true
   - "original_text": the complete original input
   - "identified_requests": array of the specific requests identified
   - "response": your complete response addressing all requests
   - "combined_text": the original text followed by your clearly labeled response

## Output Format
```
{
  "requests_detected": true/false,
  "original_text": "original input text",
  "identified_requests": ["request 1", "request 2", ...],
  "response": "Your complete response addressing all requests",
  "combined_text": "Original text + clearly labeled response"
}
```

Ensure your response is thorough, thoughtful, and specifically tailored to the user's situation.
"""

def process_request(transcript, llm_client):
    """
    Process the transcript to detect requests and generate responses if needed.
    
    Args:
        transcript (str): The user's input text
        llm_client: The LLM client used to generate responses
        
    Returns:
        dict: Result containing detection status and processed text
    """
    # Generate the request detection prompt
    prompt = get_request_detection_prompt(transcript)
    
    # Call the LLM with the prompt
    response = llm_client.complete(prompt=prompt)
    
    # Parse the JSON response from the LLM
    try:
        result = json.loads(response)
        
        # If requests were detected, return the combined text
        if result.get("requests_detected", False):
            return result
        
        # If no requests were detected, return the original text
        return {
            "requests_detected": False,
            "original_text": transcript,
            "combined_text": transcript
        }
    except json.JSONDecodeError:
        # If there's an error parsing the JSON, return the original text
        return {
            "requests_detected": False,
            "original_text": transcript,
            "combined_text": transcript,
            "error": "Failed to parse LLM response"
        }

