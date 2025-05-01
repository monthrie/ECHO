# Entity Anonymization System

A privacy-focused system for anonymizing personally identifiable information (PII) using Small Language Models (SLMs). This system maintains context and relationships between entities while providing consistent anonymization across multiple sessions.

## Overview

This system uses a local SLM (via Ollama) to:

1. Identify personally identifiable information in text
2. Create and maintain a consistent database of entities and their anonymized aliases
3. Preserve entity relationships and context
4. Handle partial references to known entities
5. Process text before sending to external LLMs to maintain privacy

## Key Features

- **Persistent Entity Tracking**: Maintains a database of entities and their aliases
- **Context Preservation**: Understands relationships between entities
- **Entity Resolution**: Links partial references to previously seen entities
- **Bidirectional Mapping**: Anonymizes and deanonymizes text
- **SLM-Based Intelligence**: Uses local language models for sophisticated entity recognition

## Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) with at least one local model installed (e.g., llama3.2)

### Setup

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install ollama
```

3. Ensure Ollama is running with your preferred model:

```bash
ollama pull llama3.2:latest
```

## Usage

### Basic Usage

```python
from entity_anonymizer import EntityAnonymizer

# Create an anonymizer
anonymizer = EntityAnonymizer()

# Anonymize text
text = "My name is John Smith and I live in New York."
result = anonymizer.anonymize_text(text)

# Print results
print(result["anonymized_text"])
```

### Command Line Usage

```bash
# Anonymize text directly
python entity_anonymizer.py --text "My name is John Smith and I live in New York."

# Anonymize text from a file
python entity_anonymizer.py --file input.txt --output anonymized.txt

# Use a specific model
python entity_anonymizer.py --text "Hello, I'm Sarah." --model llama3.2:8b

# Use a custom database location
python entity_anonymizer.py --text "Hello, I'm Sarah." --db my_entities.json
```

### Integration with LLMs

See the `usage_examples.py` file for examples of how to:
- Maintain consistency across multiple runs
- Preserve context and relationships
- Process LLM responses containing anonymized entities
- Integrate with LLM services

## How It Works

1. **Entity Database**: The system maintains a JSON file with all known entities and their aliases
2. **SLM Processing**: Uses a local language model to identify entities and their relationships
3. **Contextual Resolution**: Resolves partial references based on context and previous mentions
4. **Consistent Aliases**: Ensures the same entity always gets the same alias

### Database Structure

The entity database is stored as a JSON file with the following structure:

```json
{
  "entities": {
    "John Smith": {
      "alias": "Person1",
      "type": "person",
      "relationships": ["user-relation"],
      "mentions": ["John", "Mr. Smith"],
      "first_seen": "2023-01-15T14:30:00",
      "last_seen": "2023-04-20T09:15:00"
    }
  },
  "special_entities": {
    "user": {
      "alias": "Self",
      "mentions": ["I", "me", "myself"]
    }
  },
  "metadata": {
    "created_at": "2023-01-15T14:30:00",
    "updated_at": "2023-04-20T09:15:00",
    "version": "1.0"
  }
}
```

## Customization

You can customize the system by modifying the `Config` class in `entity_anonymizer.py`:

- `DEFAULT_MODEL`: Change the default SLM model
- `ENTITY_DB_PATH`: Set a different path for the entity database
- `MAX_ENTITIES_IN_CONTEXT`: Adjust how many entities to include in the SLM prompt
- `USER_SELF_ALIAS`: Change how the user themselves is anonymized

## Limitations and Considerations

- **Performance**: Processing large texts may be slow depending on the SLM being used
- **Accuracy**: Entity resolution accuracy depends on the quality of the local SLM
- **Database Growth**: The entity database will grow over time and may need maintenance

## Privacy Considerations

- All processing is done locally on your device
- No PII is sent to external services (apart from anonymized text you explicitly send)
- The entity database contains the original entities, so keep the database file secure

## License

MIT License