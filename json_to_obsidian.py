import json
import os
from pathlib import Path
import requests
from datetime import datetime

class ObsidianConverter:
    def __init__(self, config):
        self.config = config
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.MODEL
        
        # Create output directory for markdown files
        self.output_dir = Path("markdown_output")
        self.output_dir.mkdir(exist_ok=True)
        print(f"Created output directory: {self.output_dir}")
        
        # Create necessary directories in the output folder
        self.create_directory_structure()
    
    def create_directory_structure(self):
        """Create the basic folder structure for markdown output."""
        directories = [
            "Projects",
            "Areas",
            "Resources",
            "Archives",
            "Entities",
            "Daily Notes"
        ]
        
        for directory in directories:
            dir_path = self.output_dir / directory
            dir_path.mkdir(exist_ok=True)
            print(f"Created directory: {dir_path}")
    
    def get_directory_for_para_type(self, para_type):
        """Map PARA type to appropriate directory."""
        mapping = {
            "project": "Projects",
            "area": "Areas",
            "resource": "Resources",
            "archive": "Archives"
        }
        return mapping.get(para_type, "Resources")  # Default to Resources
    
    def convert_json_to_markdown(self, json_data):
        """Convert JSON data to markdown using the OpenRouter API."""
        # Import the prompt
        from conversion_prompt import get_conversion_prompt
        
        # Prepare the prompt
        prompt = get_conversion_prompt(json_data)
        
        # Debug: Print API key info (first 5 chars) and model being used
        print(f"Using API key starting with: {self.api_key[:5]}...")
        print(f"Using model: {self.model}")
        
        # Setup headers and payload
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000", 
            "X-Title": "ECHO Conversion",  # Added for OpenRouter tracking
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You convert structured JSON data into organized Obsidian markdown files."},
                {"role": "user", "content": prompt}
            ],
            # Add API key directly in the payload as a fallback
            "api_key": self.api_key
        }
        
        # Debug: Print request info
        print(f"API URL: https://openrouter.ai/api/v1/chat/completions")
        print(f"Headers: {headers}")
        print(f"Using payload with model: {payload['model']}")
        
        # Make API call
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Debug: Print response status
        print(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            # Try alternative endpoint
            print("Trying alternative endpoint...")
            response = requests.post(
                "https://api.openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            print(f"Alternative response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Alternative endpoint error: {response.text}")
                raise Exception(f"API call failed: {response.text}")
        
        # Extract the markdown content from the response
        result = response.json()["choices"][0]["message"]["content"].strip()
        
        # Process the result to create markdown files
        self._process_markdown_instructions(result, json_data)
        
        return True
    
    def _process_markdown_instructions(self, llm_response, original_json):
        """Process the LLM response to create markdown files."""
        # Split the response into file sections
        file_sections = llm_response.split("FILE: ")
        
        # Skip the first element if it's empty or contains preamble
        if not file_sections[0].strip().startswith("```"):
            file_sections = file_sections[1:]
        
        # Process each file section
        for section in file_sections:
            if not section.strip():
                continue
                
            # Extract file path and content
            lines = section.strip().split("\n")
            file_path = lines[0].strip()
            
            # Find the markdown content between triple backticks
            content_start = section.find("```")
            content_end = section.rfind("```")
            
            if content_start != -1 and content_end != -1:
                # Extract the content without the markdown code block markers
                content_start = section.find("\n", content_start) + 1
                markdown_content = section[content_start:content_end].strip()
                
                # Create the file
                self._create_markdown_file(file_path, markdown_content)
            else:
                print(f"Could not extract markdown content for {file_path}")
    
    def _create_markdown_file(self, relative_path, content):
        """Create a markdown file in the output directory."""
        full_path = self.output_dir / relative_path
        
        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created markdown file: {full_path}")
    
    def process_json_file(self, json_file_path):
        """Process a JSON file and convert it to markdown."""
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
        
        print(f"Converting JSON file: {json_file_path}")
        return self.convert_json_to_markdown(json_data)

def convert_all_json_files(config):
    """Convert all JSON files in the output directory to markdown."""
    converter = ObsidianConverter(config)
    
    json_dir = Path(config.JSON_OUTPUT_DIR)
    for json_file in json_dir.glob("*.json"):
        try:
            converter.process_json_file(json_file)
            print(f"Successfully converted {json_file}")
        except Exception as e:
            print(f"Error converting {json_file}: {str(e)}")