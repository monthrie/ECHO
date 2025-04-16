---
tags: ["technical architecture", "JSON structure", "entity extraction", "embeddings", "NLP"]
record_ids: ["d5e6f7g8-h9i0-4j1k-l2m3-n4o5p6q7r8s9"]
goal: Design and implement the technical architecture for the FTFM system
---

# Technical Architecture

## System Overview

The technical architecture for FTFM involves creating a model to batch process transcripts into structured JSON records containing entities (people, places, laws, events) and their relationships. Special attention would be paid to conflicts of interest, hypocrisies, and changes in stated positions. Each record would include embeddings for semantic search capabilities.

## Core Components

### 1. Data Ingestion Pipeline

- **Transcript Acquisition**: Automated systems to obtain or generate transcripts
- **Preprocessing**: Cleaning, normalization, and segmentation of text
- **Metadata Extraction**: Capturing source information, timestamps, speakers

### 2. NLP Processing Engine

- **Entity Recognition**: Identifying people, organizations, locations, events
- **Claim Extraction**: Isolating specific statements and assertions
- **Relationship Mapping**: Determining connections between entities
- **Sentiment Analysis**: Capturing tone and attitude toward subjects
- **Contradiction Detection**: Identifying inconsistencies in statements over time

### 3. Storage Layer

- **JSON Document Store**: Structured storage of processed information
- **Vector Database**: Storage of embeddings for semantic search
- **Relational Database**: Managing entity relationships and metadata
- **Versioning System**: Tracking changes to statements and positions over time

### 4. Query and Retrieval System

- **Search API**: Interface for querying the database
- **RAG Pipeline**: Retrieval-augmented generation for complex queries
- **Visualization Tools**: Graphical representation of relationships and patterns

## Data Structures

### Entity Record
```json
{
  "entity_id": "unique_identifier",
  "entity_type": "person|organization|event|law|place",
  "name": "Entity Name",
  "aliases": ["Alternative names"],
  "metadata": {
    "first_mentioned": "ISO-date",
    "last_mentioned": "ISO-date",
    "mention_count": 42,
    "entity_specific_fields": {}
  },
  "embedding": [0.1, 0.2, ...],
  "relationships": [
    {
      "related_entity_id": "another_entity_id",
      "relationship_type": "works_for|supports|opposes|etc",
      "source_claims": ["claim_id1", "claim_id2"]
    }
  ]
}
```

### Claim Record
```json
{
  "claim_id": "unique_identifier",
  "source_id": "transcript_id",
  "speaker_id": "entity_id_of_speaker",
  "timestamp": "ISO-date-with-time",
  "text": "Exact quote of the claim",
  "entities_mentioned": ["entity_id1", "entity_id2"],
  "claim_type": "statement|promise|prediction|opinion",
  "embedding": [0.1, 0.2, ...],
  "related_claims": [
    {
      "related_claim_id": "another_claim_id",
      "relationship_type": "supports|contradicts|elaborates"
    }
  ],
  "verification_status": "unverified|confirmed|disputed",
  "verification_notes": "Optional notes about verification"
}
```

## Technical Challenges

1. **Accuracy of Entity Recognition**: Ensuring correct identification of entities, especially with ambiguous references
2. **Claim Boundary Detection**: Determining where one claim ends and another begins
3. **Coreference Resolution**: Tracking pronouns and references to previously mentioned entities
4. **Contradiction Detection**: Identifying subtle changes in position over time
5. **Scaling**: Processing large volumes of content efficiently

## Implementation Phases

1. **Prototype**: Basic entity and claim extraction from limited sources
2. **Alpha**: Expanded processing capabilities with initial relationship mapping
3. **Beta**: Full system with contradiction detection and basic search
4. **Production**: Complete system with RAG integration and advanced features

## Related Notes

- [[Projects/Follow The Money/Project Overview|Project Overview]]
- [[Projects/Follow The Money/Obsidian Integration|Obsidian Integration]]
- [[Projects/Follow The Money/RAG Query System|RAG Query System]]