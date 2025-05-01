"""
Entity Anonymization System

This script provides a robust entity anonymization system that uses a Small Language Model (SLM) 
to identify, track, and anonymize personally identifiable information (PII) across multiple
interactions. It maintains a persistent database of entities and their aliases.

Usage:
    python entity_anonymizer.py --text "My input text with PII"
    python entity_anonymizer.py --file input.txt
"""

import json
import re
import os
import argparse
import ollama
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configuration
class Config:
    # Default storage location for entity database
    ENTITY_DB_PATH = Path("entity_database.json")
    
    # Default model to use
    DEFAULT_MODEL = "llama3.2:latest"
    
    # Max entities to include in context (to avoid context window limits)
    MAX_ENTITIES_IN_CONTEXT = 50
    
    # Special user entity reference
    USER_SELF_ALIAS = "Self"

class EntityAnonymizer:
    def __init__(self, model: str = Config.DEFAULT_MODEL, db_path: Optional[Path] = None):
        """
        Initialize the entity anonymizer.
        
        Args:
            model: Name of the Ollama model to use
            db_path: Path to the entity database file
        """
        self.model = model
        self.db_path = db_path or Config.ENTITY_DB_PATH
        self.entity_db = self._load_entity_database()
        
    def _load_entity_database(self) -> Dict[str, Any]:
        """Load the entity database from disk or create a new one."""
        if not self.db_path.exists():
            print(f"Creating new entity database at {self.db_path}")
            # Create initial database structure
            return {
                "entities": {},
                "special_entities": {
                    "user": {
                        "alias": Config.USER_SELF_ALIAS,
                        "mentions": ["I", "me", "myself"],
                        "first_seen": datetime.now().isoformat(),
                        "last_seen": datetime.now().isoformat()
                    }
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded entity database with {len(data.get('entities', {}))} entities")
                return data
        except json.JSONDecodeError:
            print(f"Error parsing entity database, creating new one")
            return {"entities": {}, "special_entities": {}, "metadata": {}}
        except Exception as e:
            print(f"Error loading entity database: {e}")
            return {"entities": {}, "special_entities": {}, "metadata": {}}
            
    def _save_entity_database(self, db: Dict[str, Any]) -> None:
        """Save the entity database to disk."""
        # Ensure the parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update metadata
        db["metadata"] = db.get("metadata", {})
        db["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save the database
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2)
            
        print(f"Saved entity database with {len(db.get('entities', {}))} entities")
            
    def _filter_relevant_entities(self, text: str) -> Dict[str, Any]:
        """
        Filter entity database to include only the most relevant entities for the current text.
        This helps avoid context window limitations in the SLM.
        """
        # Simple implementation: include all entities up to the max count
        # A more sophisticated version would prioritize entities mentioned in the text
        
        entities = self.entity_db.get("entities", {})
        if len(entities) <= Config.MAX_ENTITIES_IN_CONTEXT:
            return self.entity_db
            
        # Simple filtering based on recency
        sorted_entities = sorted(
            entities.items(),
            key=lambda x: x[1].get("last_seen", ""),
            reverse=True
        )
        
        # Create a filtered copy of the database
        filtered_db = {
            "entities": {k: v for k, v in sorted_entities[:Config.MAX_ENTITIES_IN_CONTEXT]},
            "special_entities": self.entity_db.get("special_entities", {}),
            "metadata": self.entity_db.get("metadata", {})
        }
        
        return filtered_db
        
    def anonymize_text(self, text: str) -> Dict[str, Any]:
        """
        Anonymize text using the SLM and entity database.
        
        Args:
            text: The text to anonymize
            
        Returns:
            dict: Contains anonymized text, entity mapping, and the updated entity database
        """
        # Filter relevant entities to avoid context window limitations
        filtered_db = self._filter_relevant_entities(text)
        
        # Construct the prompt for the SLM
        prompt = self._create_anonymization_prompt(text, filtered_db)
        
        # Call the SLM
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            output = response['message']['content']
        except Exception as e:
            print(f"Error calling SLM: {e}")
            return {
                "anonymized_text": text,
                "error": f"Failed to call SLM: {str(e)}",
                "entity_db": self.entity_db
            }
            
        # Parse the SLM response
        try:
            result = self._parse_slm_output(output)
            
            # Update and save the entity database
            self._merge_entity_updates(result.get("updated_entity_db", {}))
            
            return {
                "anonymized_text": result.get("anonymized_text", text),
                "entity_mapping": result.get("entity_mapping", {}),
                "entity_db": self.entity_db
            }
        except Exception as e:
            print(f"Error parsing SLM output: {e}")
            print(f"Raw output: {output}")
            return {
                "anonymized_text": text,
                "error": f"Failed to parse SLM output: {str(e)}",
                "entity_db": self.entity_db
            }
            
    def _create_anonymization_prompt(self, text: str, filtered_db: Dict[str, Any]) -> str:
        """Create the prompt for the SLM to anonymize the text."""
        # Format the entity database as a string (pretty-printed JSON)
        db_json = json.dumps(filtered_db, indent=2)
        
        # Create the prompt with clearer JSON structure requirements
        prompt = f"""
You are a privacy-preserving entity mapper. Your job is to identify personally identifiable information (PII) in text, anonymize it, and maintain a database of entity mappings.

ENTITY DATABASE:
{db_json}

NEW TEXT TO ANONYMIZE:
{text}

INSTRUCTIONS:
1. Identify all PII entities in the text (names, dates, locations, etc.).
2. Cross-reference with the existing entity database.
3. For existing entities, use the previously assigned alias.
4. For new entities, assign a new alias that preserves the entity type (Person1, Location1, etc.).
5. Update the entity database with new information.
6. Replace all identified entities in the text with their aliases.

SPECIAL INSTRUCTIONS:
- References to the user themselves should use the special "Self" alias.
- Preserve the context and relationships between entities.
- Recognize partial references to known entities (e.g., "my brother" vs "my brother Mike").
- If uncertain about an entity reference, indicate this in your response.

IMPORTANT: Your response must be ONLY a valid JSON object with this exact structure:
{{
  "anonymized_text": "The anonymized version of the input text with all PII replaced by aliases",
  "entity_mapping": {{
    "original_entity_1": "alias_1",
    "original_entity_2": "alias_2"
  }},
  "updated_entity_db": {{
    "entities": {{
      // Updated entities from the database
    }},
    "special_entities": {{
      // Updated special entities
    }},
    "metadata": {{
      // Updated metadata
    }}
  }}
}}

Do not include any additional text, explanations, or markdown formatting. Return ONLY the JSON object.
"""
        return prompt
        
    def _parse_slm_output(self, output: str) -> Dict[str, Any]:
        """Parse the SLM output to extract the anonymized text and entity database updates."""
        # Clean the output by removing any markdown formatting
        cleaned_output = output.strip()
        
        # Remove any markdown code block markers
        cleaned_output = re.sub(r'```json\s*|\s*```', '', cleaned_output)
        
        # Remove any leading/trailing whitespace and newlines
        cleaned_output = cleaned_output.strip()
        
        # Try to find the first valid JSON object
        try:
            # First try parsing the entire output
            return json.loads(cleaned_output)
        except json.JSONDecodeError:
            # If that fails, try to find a JSON object within the text
            json_match = re.search(r'(\{[\s\S]*\})', cleaned_output)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
                    
        # If we still haven't found valid JSON, try to extract just the anonymized text
        text_match = re.search(r'"anonymized_text"\s*:\s*"([^"]*)"', cleaned_output)
        if text_match:
            anonymized_text = text_match.group(1)
            return {
                "anonymized_text": anonymized_text,
                "entity_mapping": {},
                "updated_entity_db": {}
            }
            
        raise ValueError("Could not extract valid JSON from SLM output")
            
    def _merge_entity_updates(self, updates: Dict[str, Any]) -> None:
        """Merge updates to the entity database from the SLM."""
        if not updates:
            return
            
        # Get the updated entities
        updated_entities = updates.get("entities", {})
        updated_special_entities = updates.get("special_entities", {})
        
        # Merge with existing database
        if updated_entities:
            self.entity_db["entities"] = {**self.entity_db.get("entities", {}), **updated_entities}
            
        if updated_special_entities:
            self.entity_db["special_entities"] = {**self.entity_db.get("special_entities", {}), **updated_special_entities}
            
        # Save the updated database
        self._save_entity_database(self.entity_db)
        
    def deanonymize_text(self, anonymized_text: str) -> str:
        """
        Replace aliases in anonymized text with original entity names.
        
        Args:
            anonymized_text: Text with entity aliases
            
        Returns:
            str: Text with original entity names restored
        """
        # Build a reverse mapping (alias -> original)
        reverse_mapping = {}
        
        # Add regular entities
        for entity_name, entity_data in self.entity_db.get("entities", {}).items():
            alias = entity_data.get("alias")
            if alias:
                reverse_mapping[alias] = entity_name
                
        # Add special entities
        for entity_key, entity_data in self.entity_db.get("special_entities", {}).items():
            alias = entity_data.get("alias")
            # For the user entity, replace with "you" or appropriate pronouns
            if entity_key == "user" and alias:
                reverse_mapping[alias] = "you"  # Or context-appropriate pronoun
            elif alias:
                reverse_mapping[alias] = entity_key
                
        # Replace all aliases in the text
        deanonymized_text = anonymized_text
        for alias, original in reverse_mapping.items():
            # Use word boundary to avoid partial replacements
            deanonymized_text = re.sub(r'\b' + re.escape(alias) + r'\b', original, deanonymized_text)
            
        return deanonymized_text
        
    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a file containing text to anonymize.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            dict: Contains anonymized text and entity mapping
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                return self.anonymize_text(text)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return {
                "anonymized_text": "",
                "error": f"Failed to process file: {str(e)}",
                "entity_db": self.entity_db
            }
            
    def save_anonymized_text(self, anonymized_text: str, output_path: Union[str, Path]) -> None:
        """
        Save anonymized text to a file.
        
        Args:
            anonymized_text: The anonymized text to save
            output_path: Path to the output file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(anonymized_text)
                print(f"Saved anonymized text to {output_path}")
        except Exception as e:
            print(f"Error saving anonymized text: {e}")

def main():
    """Main function to run the entity anonymizer from command line."""
    parser = argparse.ArgumentParser(description="Anonymize personally identifiable information in text.")
    parser.add_argument("--text", type=str, help="Text to anonymize")
    parser.add_argument("--file", type=str, help="File containing text to anonymize")
    parser.add_argument("--output", type=str, help="Output file for anonymized text")
    parser.add_argument("--model", type=str, default=Config.DEFAULT_MODEL, help="Ollama model to use")
    parser.add_argument("--db", type=str, help="Path to entity database file")
    
    args = parser.parse_args()
    
    # Validate input
    if not args.text and not args.file:
        parser.error("Either --text or --file must be provided")
        
    # Set up the anonymizer
    db_path = Path(args.db) if args.db else Config.ENTITY_DB_PATH
    anonymizer = EntityAnonymizer(model=args.model, db_path=db_path)
    
    # Process the input
    if args.file:
        result = anonymizer.process_file(args.file)
    else:
        result = anonymizer.anonymize_text(args.text)
        
    # Display results
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nAnonymized Text:")
        print(result["anonymized_text"])
        
        print("\nEntity Mapping:")
        for original, alias in result.get("entity_mapping", {}).items():
            print(f"  {original} -> {alias}")
            
    # Save output if requested
    if args.output and "anonymized_text" in result:
        anonymizer.save_anonymized_text(result["anonymized_text"], args.output)
        
if __name__ == "__main__":
    main()