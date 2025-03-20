---
tags: [FTFM, MVP, "Glenn Greenwald", "podcast analysis", "entity extraction"]
status: active
priority: high
startDate: 2023-11-05
deadline: 2024-01-15
project: "[[FTFM - Public Accountability Information System]]"
---

# FTFM MVP: Glenn Greenwald Podcast Mapping

## Overview
This is the first concrete implementation phase of the [[FTFM - Public Accountability Information System]] project. The MVP will focus on mapping Glenn Greenwald's podcasts from the last six months, extracting all named entities, claims, and evidence references, and structuring this information in a searchable format.

> [!GOAL]
> Create a functional prototype demonstrating entity extraction and statement tracking capabilities by January 15, 2024.

## Implementation Plan

### Phase 1: Data Collection
1. Identify 6 months of Glenn Greenwald podcast episodes
2. Obtain transcripts (either from existing sources or through transcription)
3. Organize transcripts by episode, with timestamps

### Phase 2: Processing Pipeline
1. Develop batch processing system for transcripts
2. Implement named entity recognition
   - People
   - Places
   - Laws
   - Events
3. Implement claim extractor
4. Add special detection for:
   - Conflicts of interest
   - Changes in position over time

### Phase 3: Data Structure
1. Design JSON schema for storing extracted information
2. Generate embeddings for search functionality
3. Establish entity relationships
4. Implement initial search capabilities

## Key Tasks
- [ ] Obtain transcripts of 1-2 initial podcasts
- [ ] Build model for batching and converting to structured JSON
- [ ] Develop entity extraction system
- [ ] Implement claim identification
- [ ] Create search functionality
- [ ] Test with sample queries

## Completion Criteria
Working prototype that can:
- Ingest Glenn Greenwald podcasts
- Output structured data with entity extraction
- Allow basic querying of statements and positions
- Demonstrate the core functionality of the larger FTFM system

## Connection to Main Project
This MVP serves as a proof of concept for the larger FTFM accountability system. By focusing on a single podcast host with strong opinions and numerous claims about public figures, we can test the core functionality within a manageable scope.