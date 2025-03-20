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
        
        # Debug: Print a sample of the response
        print("\n===== RESPONSE SAMPLE (first 500 chars) =====")
        print(result[:500])
        print("=====")
        
        # Debug: Show how the response is split
        file_sections = result.split("FILE: ")
        print(f"\nFound {len(file_sections)} file sections")
        if len(file_sections) > 1:
            print("\n===== FIRST FILE SECTION SAMPLE =====")
            print(file_sections[1][:200] if len(file_sections[1]) > 200 else file_sections[1])
            print("=====")
        
        # Process the result to create markdown files
        self._process_markdown_instructions(result, json_data)
        
        return True
    
    def _process_markdown_instructions(self, llm_response, original_json):
        """Process the LLM response to create markdown files."""
        # Split the response into file sections
        file_sections = llm_response.split("FILE: ")
        
        # Skip the first element if it's empty or contains preamble
        if not file_sections[0].strip():
            file_sections = file_sections[1:]
        
        # Extract category and entity names from the original JSON if available
        entity_name = None
        category_type = None
        
        # Try to extract both from meta data
        if "meta" in original_json:
            if "project" in original_json["meta"]:
                entity_name = original_json["meta"]["project"]
                category_type = "Projects"
            elif "area" in original_json["meta"]:
                entity_name = original_json["meta"]["area"]
                category_type = "Areas"
            elif "resource" in original_json["meta"]:
                entity_name = original_json["meta"]["resource"]
                category_type = "Resources"
            elif "archive" in original_json["meta"]:
                entity_name = original_json["meta"]["archive"]
                category_type = "Archives"
        
        # If not found in meta, try to extract from title
        if not entity_name and "title" in original_json:
            title = original_json["title"]
            if " - " in title:
                entity_name = title.split(" - ")[0].strip()
        
        print(f"Detected entity: {entity_name}, category: {category_type}")
        
        # Process each file section
        for i, section in enumerate(file_sections):
            if not section.strip():
                continue
                
            # Extract file path and content
            lines = section.strip().split("\n")
            file_path = lines[0].strip()
            
            # Debug: Show current section parsing
            print(f"\n----- Processing section {i+1} -----")
            print(f"File path: {file_path}")
            
            # Get content (everything after the first line)
            markdown_content = "\n".join(lines[1:]).strip()
            
            # DEBUG: Print the first 200 characters of content
            print(f"Content starts with: {markdown_content[:200]}")
            print(f"Content starts with '# ': {markdown_content.startswith('# ')}")
            print(f"Content starts with '---': {markdown_content.startswith('---')}")
            
            # Normalize file path - remove underscores from special files
            if file_path.endswith("/_Contents.md"):
                file_path = file_path.replace("/_Contents.md", "/Contents.md")
            elif file_path.endswith("/_Tasks.md"):
                file_path = file_path.replace("/_Tasks.md", "/Tasks.md")
            
            # Organize files hierarchically if we have an entity name
            if entity_name and "/" in file_path:
                path_parts = file_path.split("/")
                if len(path_parts) >= 2 and path_parts[0] in ["Projects", "Areas", "Resources", "Archives"]:
                    # Only modify paths that don't already have a subdirectory
                    if len(path_parts) == 2:  # Direct child of PARA directory
                        # Insert entity name as subdirectory
                        path_parts.insert(1, self._sanitize_filename(entity_name))
                        file_path = "/".join(path_parts)
                        print(f"Organized file into subdirectory: {file_path}")
            
            # DEBUG: Print content before title check
            print(f"Before title check - content starts with: {markdown_content[:50]}")
            
            # Check if content starts with YAML frontmatter (either directly or in a code block)
            if markdown_content.startswith("# "):
                print("Did not add title - content already has a title")
            elif markdown_content.startswith("---"):
                print("Did not add title - content already has YAML frontmatter")
            elif "yaml" in markdown_content[:20].lower() and "---" in markdown_content[:50]:
                # This handles both ```yaml and the word "yaml" appearing at the start
                print("Found YAML block - extracting and reformatting")
                
                # Get everything after the first occurrence of "---"
                first_delimiter = markdown_content.find("---")
                if first_delimiter >= 0:
                    # Find the second "---" delimiter
                    second_delimiter = markdown_content.find("---", first_delimiter + 3)
                    if second_delimiter >= 0:
                        # Extract the YAML content between the delimiters
                        yaml_content = markdown_content[first_delimiter:second_delimiter + 3]
                        
                        # Get the content after the YAML block, skipping any duplicate content
                        remaining_content = markdown_content[second_delimiter + 3:].strip()
                        
                        # Remove any code block markers
                        yaml_content = yaml_content.replace("```yaml", "").replace("```", "")
                        
                        # Reconstruct the content with proper frontmatter
                        markdown_content = yaml_content + "\n\n" + remaining_content
                        print("Reformatted YAML frontmatter")
            else:
                # Add title based on filename
                filename = file_path.split("/")[-1].replace(".md", "")
                title = filename.replace("-", " ")
                markdown_content = f"# {title}\n\n{markdown_content}"
                print(f"Added title: '# {title}'")
            
            # DEBUG: Print final content
            print(f"Final content starts with: {markdown_content[:200]}")
            
            # Before creating the file, check for standalone trailing backticks (not part of a code block)
            lines = markdown_content.strip().split('\n')
            if lines and lines[-1].strip() == "```":
                # Only remove if it's a standalone line of backticks
                lines.pop()
                markdown_content = '\n'.join(lines).strip()
                print("Removed trailing backticks")
            
            # Create the file if content exists
            if markdown_content:
                self._create_markdown_file(file_path, markdown_content)
            else:
                print(f"No content found for {file_path}")
    
    def _create_markdown_file(self, relative_path, content):
        """Create a markdown file in the output directory."""
        full_path = self.output_dir / relative_path
        
        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created markdown file: {full_path}")
    
    def _sanitize_filename(self, name):
        """Sanitize a string to be used as a filename or directory name."""
        # Replace invalid characters with underscores
        import re
        return re.sub(r'[\\/*?:"<>|]', "_", name)
    
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