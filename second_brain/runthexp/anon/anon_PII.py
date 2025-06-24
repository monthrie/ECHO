"""
Enhanced Entity Anonymization System with Knowledge Graph Support

This script provides a robust entity anonymization system that uses a Small Language Model (SLM) 
to identify, track, and anonymize personally identifiable information (PII) across multiple
interactions. It maintains two separate databases:
1. A local entity index (with PII, stays on device)
2. An anonymized knowledge graph (safe to share with external LLMs)

Usage:
    python entity_anonymizer.py --text "My input text with PII"
    python entity_anonymizer.py --file input.txt
"""

import json
import re
import os
import argparse
import ollama
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Configuration
class Config:
    # Default storage location for entity database
    LOCAL_ENTITY_INDEX_PATH = Path("local_entity_index.json")
    
    # Model configuration
    USE_OPENROUTER = False  # Set to True to use OpenRouter
    DEFAULT_MODEL = "llama3.2:latest"  # Used when USE_OPENROUTER is False
    OPENROUTER_MODEL = "anthropic/claude-3-opus"  # Used when USE_OPENROUTER is True
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    # Max entities to include in context (to avoid context window limits)
    MAX_ENTITIES_IN_CONTEXT = 50
    
    # Special user entity reference
    USER_SELF_ALIAS = "Self"
    
    # LLM configuration
    LLM_MODEL = "anthropic/claude-3-opus"  # Model to use for actual queries
    LLM_SYSTEM_PROMPT = """You are a helpful AI assistant. You have access to anonymized text and a knowledge graph.
    The text uses aliases (like Person1, Organization1) to protect privacy. Use these aliases in your responses.
    The knowledge graph shows relationships between entities. Use this context in your responses."""
    
    # Common relationship types
    RELATIONSHIP_TYPES = [
        "family_member", "parent_of", "child_of", "sibling_of", "spouse_of",
        "colleague_of", "supervisor_of", "employee_of", "friend_of", 
        "employed_at", "located_in", "visited", "owns", "created_by"
    ]

class EntityAnonymizer:
    def __init__(self, model: str = None, db_path: Optional[Path] = None, use_openrouter: Optional[bool] = None):
        """
        Initialize the entity anonymizer.
        
        Args:
            model: Name of the model to use (overrides Config settings)
            db_path: Path to the local entity index file
            use_openrouter: Whether to use OpenRouter (overrides Config.USE_OPENROUTER)
        """
        self.use_openrouter = use_openrouter if use_openrouter is not None else Config.USE_OPENROUTER
        self.model = model or (Config.OPENROUTER_MODEL if self.use_openrouter else Config.DEFAULT_MODEL)
        self.db_path = db_path or Config.LOCAL_ENTITY_INDEX_PATH
        self.local_entity_index = self._load_local_entity_index()
        
        if self.use_openrouter and not Config.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")
        
    def _load_local_entity_index(self) -> Dict[str, Any]:
        """Load the local entity index from disk or create a new one."""
        if not self.db_path.exists():
            print(f"Creating new local entity index at {self.db_path}")
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
                print(f"Loaded local entity index with {len(data.get('entities', {}))} entities")
                return data
        except json.JSONDecodeError:
            print(f"Error parsing local entity index, creating new one")
            return {"entities": {}, "special_entities": {}, "metadata": {}}
        except Exception as e:
            print(f"Error loading local entity index: {e}")
            return {"entities": {}, "special_entities": {}, "metadata": {}}
            
    def _save_local_entity_index(self) -> None:
        """Save the local entity index to disk."""
        # Ensure the parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update metadata
        self.local_entity_index["metadata"] = self.local_entity_index.get("metadata", {})
        self.local_entity_index["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save the database
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.local_entity_index, f, indent=2)
            
        print(f"Saved local entity index with {len(self.local_entity_index.get('entities', {}))} entities")
            
    def _filter_relevant_entities(self, text: str) -> Dict[str, Any]:
        """
        Filter entity database to include only the most relevant entities for the current text.
        This helps avoid context window limitations in the SLM.
        """
        # Simple implementation: include all entities up to the max count
        # A more sophisticated version would prioritize entities mentioned in the text
        
        entities = self.local_entity_index.get("entities", {})
        if len(entities) <= Config.MAX_ENTITIES_IN_CONTEXT:
            return self.local_entity_index
            
        # Simple filtering based on recency
        sorted_entities = sorted(
            entities.items(),
            key=lambda x: x[1].get("last_seen", ""),
            reverse=True
        )
        
        # Create a filtered copy of the database
        filtered_db = {
            "entities": {k: v for k, v in sorted_entities[:Config.MAX_ENTITIES_IN_CONTEXT]},
            "special_entities": self.local_entity_index.get("special_entities", {}),
            "metadata": self.local_entity_index.get("metadata", {})
        }
        
        return filtered_db
    
    def _generate_anonymized_knowledge_graph(self) -> Dict[str, Any]:
        """
        Generate an anonymized knowledge graph from the local entity index.
        This graph contains only aliases and relationships, no PII.
        """
        # Start with empty structures
        anonymized_entities = {}
        relationships = []
        
        # Process regular entities
        for entity_name, entity_data in self.local_entity_index.get("entities", {}).items():
            alias = entity_data.get("alias")
            entity_type = entity_data.get("type", "unknown")
            
            if alias:
                # Add to anonymized entities
                anonymized_entities[alias] = {
                    "type": entity_type
                }
        
        # Add special entities
        for entity_key, entity_data in self.local_entity_index.get("special_entities", {}).items():
            alias = entity_data.get("alias")
            if alias:
                anonymized_entities[alias] = {
                    "type": "person"  # Assuming special entities are typically persons
                }
        
        # Extract relationships from the local entity index
        for entity_name, entity_data in self.local_entity_index.get("entities", {}).items():
            source_alias = entity_data.get("alias")
            if not source_alias:
                continue
                
            # Process explicit relationships if they exist
            for relationship in entity_data.get("relationships", []):
                # Parse relationship string (e.g., "colleague_of:Person2")
                if ":" in relationship:
                    rel_type, target_alias = relationship.split(":", 1)
                    
                    # Add to relationships list
                    relationships.append({
                        "source": source_alias,
                        "target": target_alias,
                        "type": rel_type
                    })
        
        # Return the anonymized knowledge graph
        return {
            "entities": anonymized_entities,
            "relationships": relationships
        }
        
    def _call_model(self, prompt: str) -> str:
        """
        Call the appropriate model based on configuration.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            str: The model's response
        """
        if self.use_openrouter:
            return self._call_openrouter(prompt)
        else:
            return self._call_local_model(prompt)
            
    def _call_local_model(self, prompt: str) -> str:
        """Call the local Ollama model."""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Error calling local model: {e}")
            raise
            
    def _call_openrouter(self, prompt: str) -> str:
        """Call the OpenRouter API."""
        try:
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.text}")
                
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling OpenRouter: {e}")
            raise
        
    def anonymize_text(self, text: str) -> Dict[str, Any]:
        """
        Anonymize text using the configured model.
        
        Args:
            text: The text to anonymize
            
        Returns:
            dict: Contains anonymized text, entity mapping, and knowledge graph
        """
        # Filter relevant entities to avoid context window limitations
        filtered_index = self._filter_relevant_entities(text)
        
        # Generate anonymized knowledge graph for context
        anonymized_kg = self._generate_anonymized_knowledge_graph()
        
        # Construct the prompt
        prompt = self._create_anonymization_prompt(text, filtered_index, anonymized_kg)
        
        # Call the appropriate model
        try:
            output = self._call_model(prompt)
        except Exception as e:
            print(f"Error calling model: {e}")
            return {
                "anonymized_text": text,
                "error": f"Failed to call model: {str(e)}",
                "entity_mapping": {},
                "anonymized_kg": anonymized_kg
            }
            
        # Parse the model response
        try:
            result = self._parse_slm_output(output)
            
            # Update the local entity index with new information
            self._update_local_entity_index(result)
            
            # Save the updated local entity index
            self._save_local_entity_index()
            
            # Generate an updated anonymized knowledge graph
            updated_kg = self._generate_anonymized_knowledge_graph()
            
            return {
                "anonymized_text": result.get("anonymized_text", text),
                "entity_mapping": result.get("entity_mapping", {}),
                "anonymized_kg": updated_kg
            }
        except Exception as e:
            print(f"Error parsing model output: {e}")
            print(f"Raw output: {output}")
            return {
                "anonymized_text": text,
                "error": f"Failed to parse model output: {str(e)}",
                "entity_mapping": {},
                "anonymized_kg": anonymized_kg
            }
            
    def _create_anonymization_prompt(self, text: str, filtered_index: Dict[str, Any], anonymized_kg: Dict[str, Any]) -> str:
        """
        Create the prompt for the SLM to anonymize the text.
        
        Args:
            text: The text to anonymize
            filtered_index: The filtered local entity index
            anonymized_kg: The anonymized knowledge graph
        """
        # Format the entity index and knowledge graph as strings
        index_json = json.dumps(filtered_index, indent=2)
        kg_json = json.dumps(anonymized_kg, indent=2)
        
        # Create the prompt with clearer JSON structure requirements
        prompt_parts = [
            "You are a privacy-preserving entity mapper. Your job is to identify personally identifiable information (PII) in text, anonymize it, and maintain a knowledge graph of entity relationships.",
            "",
            "LOCAL ENTITY INDEX (PRIVATE - STAYS ON DEVICE):",
            "```json",
            index_json,
            "```",
            "",
            "ANONYMIZED KNOWLEDGE GRAPH (SAFE TO SHARE):",
            "```json",
            kg_json,
            "```",
            "",
            "NEW TEXT TO ANONYMIZE:",
            "```",
            text,
            "```",
            "",
            "INSTRUCTIONS:",
            "1. Identify all PII entities in the text (names, dates, locations, etc.)",
            "2. Cross-reference with the existing entity index",
            "3. For existing entities, use the previously assigned alias",
            "4. For new entities, assign a new alias that preserves the entity type (Person1, Location1, etc.)",
            "5. Identify relationships between entities",
            "6. Replace all identified entities in the text with their aliases",
            "",
            "RELATIONSHIP TYPES:",
            "- family_member, parent_of, child_of, sibling_of, spouse_of",
            "- colleague_of, supervisor_of, employee_of, friend_of",
            "- employed_at, located_in, visited, owns, created_by",
            "",
            "SPECIAL INSTRUCTIONS:",
            "- References to the user themselves should use the special \"Self\" alias",
            "- Preserve the context and relationships between entities",
            "- Recognize partial references to known entities (e.g., \"my brother\" vs \"my brother Mike\")",
            "",
            "IMPORTANT: Your response MUST be a valid JSON object with this exact structure:",
            "```json",
            "{",
            "  \"anonymized_text\": \"The anonymized version of the input text with all PII replaced by aliases\",",
            "  \"entity_mapping\": {",
            "    \"original_entity_1\": \"alias_1\",",
            "    \"original_entity_2\": \"alias_2\"",
            "  },",
            "  \"local_entity_updates\": {",
            "    \"entities\": {",
            "      \"Entity Name 1\": {",
            "        \"alias\": \"Person1\",",
            "        \"type\": \"person\",",
            "        \"mentions\": [\"Entity Name 1\", \"alternative mention\"],",
            "        \"relationships\": [\"colleague_of:Person2\", \"employed_at:Organization1\"],",
            "        \"first_seen\": \"TIMESTAMP\",",
            "        \"last_seen\": \"TIMESTAMP\"",
            "      }",
            "    }",
            "  }",
            "}",
            "```",
            "",
            "Do not include any additional text, explanations, or markdown formatting outside the JSON. Return ONLY valid JSON."
        ]
        
        prompt = "\n".join(prompt_parts)
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
                "local_entity_updates": {}
            }
            
        raise ValueError("Could not extract valid JSON from SLM output")
            
    def _update_local_entity_index(self, slm_result: Dict[str, Any]) -> None:
        """
        Update the local entity index with new information from the SLM.
        
        Args:
            slm_result: The parsed SLM output containing entity updates
        """
        # Get the entity updates from the SLM result
        entity_updates = slm_result.get("local_entity_updates", {}).get("entities", {})
        if not entity_updates:
            return
            
        # Update existing entities or add new ones
        for entity_name, entity_data in entity_updates.items():
            # Check if the entity already exists
            if entity_name in self.local_entity_index.get("entities", {}):
                # Update existing entity
                existing_entity = self.local_entity_index["entities"][entity_name]
                
                # Update basic properties
                for key in ["alias", "type"]:
                    if key in entity_data:
                        existing_entity[key] = entity_data[key]
                
                # Update last_seen timestamp
                existing_entity["last_seen"] = entity_data.get("last_seen", datetime.now().isoformat())
                
                # Merge mentions without duplicates
                existing_mentions = set(existing_entity.get("mentions", []))
                new_mentions = set(entity_data.get("mentions", []))
                existing_entity["mentions"] = list(existing_mentions.union(new_mentions))
                
                # Merge relationships without duplicates
                existing_relationships = set(existing_entity.get("relationships", []))
                new_relationships = set(entity_data.get("relationships", []))
                existing_entity["relationships"] = list(existing_relationships.union(new_relationships))
            else:
                # Add new entity
                self.local_entity_index.setdefault("entities", {})[entity_name] = entity_data
                
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
        for entity_name, entity_data in self.local_entity_index.get("entities", {}).items():
            alias = entity_data.get("alias")
            if alias:
                reverse_mapping[alias] = entity_name
                
        # Add special entities
        for entity_key, entity_data in self.local_entity_index.get("special_entities", {}).items():
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
                "entity_mapping": {},
                "anonymized_kg": {}
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
            
    def get_anonymized_kg_for_prompt(self) -> Dict[str, Any]:
        """
        Get the current anonymized knowledge graph, suitable for including in LLM prompts.
        
        Returns:
            dict: The anonymized knowledge graph
        """
        return self._generate_anonymized_knowledge_graph()
        
    def anonymize_for_llm(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Anonymize text and return both the anonymized text and knowledge graph 
        for sending to an external LLM.
        
        Args:
            text: The text to anonymize
            
        Returns:
            tuple: (anonymized_text, anonymized_knowledge_graph)
        """
        result = self.anonymize_text(text)
        
        return result["anonymized_text"], result["anonymized_kg"]

    def prepare_for_llm(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare a user query for sending to an LLM by anonymizing it and adding context.
        
        Args:
            user_query: The user's query text
            
        Returns:
            tuple: (prepared_prompt, context_for_deanonymization)
        """
        # First anonymize the query
        anon_result = self.anonymize_text(user_query)
        anonymized_query = anon_result["anonymized_text"]
        knowledge_graph = anon_result["anonymized_kg"]
        
        # Create the prompt with context
        prompt_parts = [
            Config.LLM_SYSTEM_PROMPT,
            "",
            "KNOWLEDGE GRAPH:",
            "```json",
            json.dumps(knowledge_graph, indent=2),
            "```",
            "",
            "USER QUERY:",
            anonymized_query
        ]
        
        prepared_prompt = "\n".join(prompt_parts)
        
        # Return both the prepared prompt and context needed for de-anonymization
        return prepared_prompt, anon_result
        
    def query_llm(self, user_query: str) -> str:
        """
        Send a query to the LLM and get a de-anonymized response.
        
        Args:
            user_query: The user's original query
            
        Returns:
            str: The de-anonymized LLM response
        """
        # Prepare the query
        prepared_prompt, anon_context = self.prepare_for_llm(user_query)
        
        # Call the LLM
        try:
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": Config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": Config.LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": prepared_prompt}
                ]
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.text}")
                
            llm_response = response.json()["choices"][0]["message"]["content"]
            
            # De-anonymize the response
            return self.deanonymize_text(llm_response)
            
        except Exception as e:
            print(f"Error querying LLM: {e}")
            return f"Error: {str(e)}"
            
    def chat_with_context(self, messages: List[Dict[str, str]]) -> str:
        """
        Have a conversation with the LLM while maintaining context.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            str: The de-anonymized LLM response
        """
        # Anonymize all messages
        anonymized_messages = []
        all_context = {}
        
        for msg in messages:
            if msg["role"] == "system":
                # Don't anonymize system messages
                anonymized_messages.append(msg)
                continue
                
            # Anonymize the message content
            anon_result = self.anonymize_text(msg["content"])
            
            # Update context
            all_context.update(anon_result.get("entity_mapping", {}))
            
            # Add anonymized message
            anonymized_messages.append({
                "role": msg["role"],
                "content": anon_result["anonymized_text"]
            })
            
        # Add knowledge graph to system message
        kg = self._generate_anonymized_knowledge_graph()
        system_msg = {
            "role": "system",
            "content": Config.LLM_SYSTEM_PROMPT + "\n\nKNOWLEDGE GRAPH:\n```json\n" + 
                      json.dumps(kg, indent=2) + "\n```"
        }
        
        # Call the LLM
        try:
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": Config.LLM_MODEL,
                "messages": [system_msg] + anonymized_messages
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.text}")
                
            llm_response = response.json()["choices"][0]["message"]["content"]
            
            # De-anonymize the response
            return self.deanonymize_text(llm_response)
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"Error: {str(e)}"

def main():
    """Main function to run the entity anonymizer from command line."""
    parser = argparse.ArgumentParser(description="Anonymize personally identifiable information in text.")
    parser.add_argument("--text", type=str, help="Text to anonymize")
    parser.add_argument("--file", type=str, help="File containing text to anonymize")
    parser.add_argument("--output", type=str, help="Output file for anonymized text")
    parser.add_argument("--model", type=str, default=Config.DEFAULT_MODEL, help="Ollama model to use")
    parser.add_argument("--db", type=str, help="Path to entity database file")
    parser.add_argument("--kg", action="store_true", help="Output the anonymized knowledge graph")
    
    args = parser.parse_args()
    
    # Validate input
    if not args.text and not args.file:
        parser.error("Either --text or --file must be provided")
        
    # Set up the anonymizer
    db_path = Path(args.db) if args.db else None
    anonymizer = EntityAnonymizer(model=args.model, db_path=db_path)
    
    # Process the input
    if args.file:
        result = anonymizer.process_file(args.file)
    else:
        result = anonymizer.anonymize_text(args.text)
        
    # Display results
    if "error" in result and result["error"]:
        print(f"Error: {result['error']}")
    else:
        print("\nAnonymized Text:")
        print(result["anonymized_text"])
        
        print("\nEntity Mapping:")
        for original, alias in result.get("entity_mapping", {}).items():
            print(f"  {original} -> {alias}")
            
        if args.kg:
            print("\nAnonymized Knowledge Graph:")
            print(json.dumps(result.get("anonymized_kg", {}), indent=2))
            
    # Save output if requested
    if args.output and "anonymized_text" in result:
        anonymizer.save_anonymized_text(result["anonymized_text"], args.output)
        
if __name__ == "__main__":
    main()