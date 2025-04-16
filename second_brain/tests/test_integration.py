import os
import json
import sys
import shutil
from pathlib import Path

# Add the parent directory to sys.path to import the integration module
sys.path.append(str(Path(__file__).parent.parent))
from core.integration import process_blueprint

# Test configuration
TEST_DIR = Path(__file__).parent / "test_data"
BLUEPRINT_PATH = TEST_DIR / "test_blueprint.json"
MARKDOWN_DIR = TEST_DIR / "markdown"
EMBEDDINGS_FILE = TEST_DIR / "test_embeddings.json"

def setup_test_environment():
    """Set up the test environment with sample data."""
    # Create test directories
    os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(MARKDOWN_DIR, exist_ok=True)
    
    # Create a sample existing document
    sample_doc_path = MARKDOWN_DIR / "existing_document.md"
    with open(sample_doc_path, 'w', encoding='utf-8') as f:
        f.write("""---
tags: ["knowledge management", "notes", "organization"]
record_ids: ["abc123"]
---

# Knowledge Management System

This is an existing document about knowledge management systems.

## Key Concepts

- Organization of information
- Retrieval mechanisms
- Metadata management

## Implementation

A good knowledge management system should be easy to use and maintain.
""")
    
    # Create sample embeddings file
    sample_embeddings = {
        str(sample_doc_path): [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # Simple mock embedding
    }
    with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sample_embeddings, f)
    
    # Create a sample blueprint
    sample_blueprint = {
        "file_info": {
            "directory": "Areas/Personal Knowledge Management",
            "filename": "Daily Weekly Story Journaling.md",
            "record_id": "h9i0j1k2-l3m4-4n5o-p6q7-r8s9t0u1v2w3"
        },
        "frontmatter": {
            "tags": [
                "journaling",
                "daily stories",
                "weekly stories",
                "personal tracking"
            ],
            "record_ids": [
                "h9i0j1k2-l3m4-4n5o-p6q7-r8s9t0u1v2w3"
            ],
            "responsibility": "Maintain a journaling practice with daily or weekly summaries"
        },
        "content": {
            "title": "Daily/Weekly Story Journaling Concept",
            "body": "## Concept Overview\n\nThe Daily/Weekly Story concept is a journaling approach that focuses on capturing concise summaries of daily or weekly events in a single sentence or short paragraph. This creates a lightweight, sustainable journaling practice that can be maintained over time without becoming burdensome.\n\n## Format\n\nEach entry follows a simple format:\n\n```\n[Date] - A [daily/weekly] story today is... [concise summary of memorable events]\n```\n\nExample:\n```\n2023-11-27 - A weekly story today is... cool with the Ralphie and a memorable video call with Jaz.\n```\n\n## Purpose\n\nThis journaling approach serves several purposes:\n\n1. **Memory Preservation**: Captures key moments that might otherwise be forgotten\n2. **Pattern Recognition**: Helps identify trends in activities and experiences over time\n3. **Reflection Prompt**: Encourages daily/weekly reflection on what was most meaningful\n4. **Low Friction**: Requires minimal time commitment, increasing sustainability\n5. **Future Context**: Provides future self with context about past experiences"
        }
    }
    
    with open(BLUEPRINT_PATH, 'w', encoding='utf-8') as f:
        json.dump(sample_blueprint, f, indent=2)
    
    return {
        "blueprint_path": str(BLUEPRINT_PATH),
        "markdown_dir": str(MARKDOWN_DIR),
        "embeddings_file": str(EMBEDDINGS_FILE)
    }

def run_test():
    """Run the integration test."""
    # Set up test environment
    test_config = setup_test_environment()
    
    # Override global variables in the integration module
    import core.integration as integration
    integration.MARKDOWN_DIR = test_config["markdown_dir"]
    integration.EMBEDDINGS_FILE = test_config["embeddings_file"]
    
    # Process the blueprint
    print(f"Processing blueprint: {test_config['blueprint_path']}")
    result = process_blueprint(test_config["blueprint_path"])
    
    print(f"\nIntegration result: {result}")
    
    # Display the result file content
    if result and os.path.exists(result):
        print(f"\nResult file content:")
        with open(result, 'r', encoding='utf-8') as f:
            print(f.read())

def cleanup():
    """Clean up the test environment."""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
        print(f"\nCleaned up test directory: {TEST_DIR}")

if __name__ == "__main__":
    try:
        run_test()
    finally:
        # Comment out this line if you want to inspect the files after the test
        # cleanup()
        pass 