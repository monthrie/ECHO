---
tags: [FTFM, accountability, news, transparency, fact-checking, "public statements"]
status: active
priority: high
startDate: 2023-11-05
deadline: 2024-03-31
---

# FTFM: Public Accountability Information System

## Project Overview
FTFM is designed to track, index, and analyze public statements, creating a searchable "source of truth" for accountability. The system extracts named entities and claims from media sources like podcasts, linking them to specific moments when statements were made. This enables tracking of promises, identification of patterns, and verification of consistency in public figures' positions over time.

> [!GOAL]
> Build a working proof of concept for FTFM that demonstrates the core accountability functionality by March 31, 2024.

## Current Status
- **Current Phase**: Planning
- **Next Milestone**: MVP with Glenn Greenwald podcast mapping (due Jan 15, 2024)

## Key Components
- [[FTFM - MVP Glenn Greenwald Podcast Mapping|MVP Development]]
- [[FTFM - System Architecture|System Architecture]]
- [[Research - Existing Accountability Systems|Market Research]]

## Why This Matters
The project addresses a critical gap in current media accountability systems. While platforms like Wikipedia handle static information well (births, deaths, major events), there's no comprehensive system for tracking day-to-day statements and ensuring accountability for what public figures say.

## Implementation Plan
1. **Phase 1**: MVP Development with Glenn Greenwald podcasts
   - Create structured data from podcast transcripts
   - Extract named entities, claims, and evidence references
   - Implement basic search functionality
   
2. **Phase 2**: Two-Layer System Architecture Implementation
   - Build back-end JSON database with embeddings
   - Develop front-end using Obsidian markdown
   - Implement synchronization mechanism
   
3. **Phase 3**: AI-Enhanced Analysis
   - Develop pattern recognition for contradictions
   - Implement natural language queries
   - Build visualization of statement networks

## Tasks
- [ ] Obtain transcripts of Glenn Greenwald podcasts
- [ ] Develop entity extraction model
- [ ] Build JSON structure for storing statements
- [ ] Create prototype for data ingestion
- [ ] Implement basic search functionality
- [ ] Design two-layer architecture
- [ ] Research existing accountability systems
- [ ] Explore partnerships with fact-checking organizations

## Completion Criteria
A functioning prototype that can:
- Ingest podcast transcripts
- Extract claims and entities
- Allow querying by topic or individual
- Demonstrate core accountability features

## Notes
Consider starting with podcasts as test data. Worth exploring partnerships with existing fact-checking organizations.