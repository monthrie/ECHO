---
tags: ["FTFM", "technical architecture", "database design", "Obsidian integration"]
record_ids: ["1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"]
goal: Define the complete technical stack and data flow for the FTFM system
---

# FTFM Technical Architecture Overview

## System Architecture
The FTFM technical architecture consists of three main components working together to create a comprehensive accountability system:

### 1. Backend Database
- **Data Structure**: JSON-based storage with embedded metadata
- **Entity Model**: Structured representation of people, organizations, events, and claims
- **Relationship Tracking**: Graph-based connections between entities and statements
- **Temporal Database**: Time-aware storage to track changes and evolution
- **Vector Embeddings**: For semantic search and similarity detection

### 2. Translation Layer
- **Format Conversion**: Transforms database records to markdown files and images
- **Bidirectional Sync**: Ensures changes in either system propagate correctly
- **Change Detection**: Identifies and resolves conflicts between versions
- **Metadata Preservation**: Maintains structured data within markdown format
- **Image Generation**: Creates visualizations from structured data

### 3. Frontend Interface (Obsidian)
- **Knowledge Graph**: Visual representation of entities and relationships
- **Markdown Notes**: Human-readable and editable content
- **Bidirectional Links**: Connections between related concepts and entities
- **Search Capabilities**: Leveraging both Obsidian and custom search functionality
- **Plugin Integration**: Custom functionality through Obsidian plugins

## Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  JSON Database  │◄───►│ Translation     │◄───►│  Obsidian       │
│  - Entities     │     │ Layer           │     │  Frontend       │
│  - Claims       │     │ - MD Conversion │     │  - Notes        │
│  - Relationships│     │ - Sync Engine   │     │  - Knowledge    │
│  - Metadata     │     │ - Conflict      │     │    Graph        │
│                 │     │   Resolution    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Technical Challenges

### Bidirectional Sync
The bidirectional sync between backend database and Obsidian frontend will be particularly challenging but crucial for usability. Key considerations include:
- Conflict resolution when both systems have changes
- Preserving structured data when editing in Obsidian
- Maintaining performance with large datasets
- Handling offline edits and synchronization

### Data Integrity
- Ensuring accuracy of extracted entities and claims
- Maintaining provenance for all information
- Preventing data corruption during synchronization
- Implementing validation for user-contributed content

### Scalability
- Designing for growth in both data volume and complexity
- Optimizing query performance for large datasets
- Managing computational resources for embedding generation
- Supporting multiple users and concurrent edits

## Implementation Plan
1. **Database Schema Design**: Define the core data structures (December 2023)
2. **Proof of Concept**: Implement basic functionality with limited dataset (January 2024)
3. **Translation Layer Development**: Build bidirectional sync capability (February 2024)
4. **Obsidian Integration**: Create custom plugins as needed (March 2024)
5. **Testing and Refinement**: Iterate based on user feedback (April 2024)

## Related Components
- [[Projects/Follow The Money/RAG Query System|RAG Query System]]
- [[Projects/Follow The Money/Proof of Concept Proposal|Proof of Concept Proposal]]
- Database Schema Design
- Obsidian Integration Module