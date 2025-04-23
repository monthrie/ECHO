---
tags: ["accountability", "transparency", "news-storage", "public-statements", "ai-analysis"]
description: A detailed brainstorm on building 'Follow The Fucking Money' (FTFM), a system to track and analyze public statements for accountability using AI and structured data.
---
## Overview
This note outlines the conceptual framework for 'Follow The Fucking Money' (FTFM), a system designed to track, analyze, and store public statements from sources like podcasts and news to ensure accountability and transparency. The goal is to create a 'source of truth' for public claims, enabling users to verify what was said, detect patterns, contradictions, or changes in stance over time.

## Core Concept
FTFM aims to map and analyze public content, such as Glenn Greenwald's podcasts over the last six months, to extract named entities, claims, promises, and events. It serves as a source of truth to track statements (e.g., a politician promising action on their first day) and flags inconsistencies or patterns over time.

## Purpose and Vision
The system seeks to hold public figures accountable by making obfuscated information transparent. It enables ordinary citizens to check how someone's stance evolves, detect hypocrisy, or identify conflicts of interest. Unlike Wikipedia, which stores static, encyclopedic data, FTFM aims to record day-to-day realities that matter in a dynamic, text-based format suitable for AI analysis.

## Minimal Viable Proof of Concept (MVP)
Start by transcribing one or two of Glenn Greenwald's podcasts, then create a model to batch process transcripts into JSON structures. Extract entities (people, places, laws, events), and note conflicts of interest, hypocrisies, or changes of mind. Include details like voting history, past employment, or financial ties.

## Technical Architecture
The system will involve:
1. **Data Ingestion**: Transcripts and media sources converted to JSON records with embeddings for search and analysis.
2. **Storage Layer**: A backend database storing structured JSON data with embeddings, connected to a frontend for user interaction (e.g., Obsidian for note editing).
3. **Synchronization**: Sync mechanisms between frontend and backend databases.
4. **AI Analysis**: A generative AI component for research, answering queries, and providing insights using a RAG (Retrieval-Augmented Generation) pipeline.
5. **User Interaction**: Enable querying and interacting with the system while viewing notes, with the AI simultaneously accessing the same data.

### Architecture Diagram (Conceptual)
```mermaid
flowchart TD
    A[Data Sources
(Podcasts, News)] --> B[Data Ingestion
(Transcripts to JSON)]
    B --> C[Storage Layer
(Database with Embeddings)]
    C --> D[AI Analysis
(RAG Pipeline)]
    C --> E[Frontend
(Obsidian/User Interface)]
    E --> F[User Queries
(Search & Interaction)]
    D --> F
    F --> E
```

## Challenges and Considerations
Objective weighting of source reliability is complex. The system must balance competing versions of truth with metrics (e.g., open-weight metrics) while focusing on verifiable facts like what was said or written. It must also handle vast data without attempting to record everything—focusing only on what matters.

## Future Potential
As AI inference, compute, and graph databases improve, FTFM could offer deeper insights, better matching, and intricate detail levels. It could become the backend storage layer for news and reality, transforming how information is accessed and verified.

## Related Notes
- [[AI Dictation System Project]]