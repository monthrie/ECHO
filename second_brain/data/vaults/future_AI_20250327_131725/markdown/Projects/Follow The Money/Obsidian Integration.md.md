---
tags: ["Obsidian integration", "markdown", "syncing mechanism", "database", "translation layer"]
record_ids: ["e6f7g8h9-i0j1-4k2l-m3n4-o5p6q7r8s9t0"]
goal: Create a bi-directional sync between JSON database and Obsidian markdown files
---

# FTFM Integration with Obsidian

## Integration Overview

The FTFM system would include a translation layer that converts JSON structures from the database into markdown notes and files that can be viewed and edited in Obsidian. This would require a syncing mechanism between the backend database and the front-end Obsidian notes to maintain consistency across both systems.

## Key Components

### 1. Translation Layer

- **JSON to Markdown Converter**: Transforms structured data into human-readable notes
- **Template System**: Applies consistent formatting to different entity types
- **Link Generator**: Creates appropriate internal links between related notes
- **Metadata Preservation**: Maintains all essential data in YAML frontmatter

### 2. Synchronization Mechanism

- **Change Detection**: Identifies updates in either the database or markdown files
- **Conflict Resolution**: Handles cases where both versions have been modified
- **Versioning**: Maintains history of changes for auditing and rollback
- **Real-time Updates**: Pushes important changes immediately when possible

### 3. Obsidian-Specific Features

- **Graph View Integration**: Ensures entity relationships appear in Obsidian's graph view
- **Custom Queries**: Creates dataview queries for filtering and analyzing data
- **Templates**: Provides templates for creating new entities and claims
- **Custom CSS**: Styles notes for better readability and visual distinction

## Markdown Structure

### Entity Note Example
```markdown
---
entity_id: unique_identifier
entity_type: person
first_mentioned: 2023-06-15
last_mentioned: 2023-11-20
mention_count: 42
tags: [politician, democrat, foreign_policy]
---

# John Smith

## Overview
Senior Senator from State X, serving since 2018. Previously served as State Attorney General (2010-2018).

## Key Positions
- Supports increased military spending
- Opposes carbon tax legislation
- Advocates for stricter immigration policies

## Recent Claims
- [[Claim-2023-11-15-001|"We need to increase border security funding by 25%"]] (Nov 15, 2023)
- [[Claim-2023-10-22-003|"The infrastructure bill will create 50,000 jobs"]] (Oct 22, 2023)

## Relationships
- Works for: [[United States Senate]]
- Member of: [[Committee on Foreign Relations]]
- Opposed by: [[Jane Doe]]
```

## Implementation Approach

1. **Database Design**: Create a schema that supports bidirectional syncing
2. **API Development**: Build endpoints for querying and updating data
3. **Obsidian Plugin**: Develop a custom plugin for seamless integration
4. **Template Creation**: Design markdown templates for different entity types
5. **Sync Logic**: Implement robust synchronization algorithms

## User Experience

From the user perspective, the integration would allow:

- Browsing entities and claims in a familiar note-taking interface
- Following links between related concepts
- Adding personal annotations and insights
- Creating custom views and filters using Obsidian's capabilities
- Searching across the entire knowledge base using natural language

## Technical Considerations

- **Performance**: Efficient handling of large numbers of notes
- **Offline Support**: Functionality when database connection is unavailable
- **Security**: Protecting sensitive information in the markdown files
- **Extensibility**: Supporting future data types and relationships

## Related Notes

- [[Projects/Follow The Money/Technical Architecture|Technical Architecture]]
- [[Projects/Follow The Money/RAG Query System|RAG Query System]]