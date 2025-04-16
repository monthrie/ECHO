---
tags: ["FTFM", "proof of concept", "accountability", "data extraction", "media analysis"]
record_ids: ["7a12b45c-3e9f-4d87-a5e2-9f8c7b6d5e4a"]
goal: Create a minimal viable proof of concept for the FTFM accountability system
---

# FTFM Proof of Concept Proposal

## Overview
This proposal outlines a proof of concept for the Follow The Money (FTFM) project by mapping entities and claims from Glenn Greenwald's podcasts over a six-month period. The goal is to extract all named entities, claims, and evidence, linking each to the exact moment when statements were made to create a verifiable 'source of truth'.

## Approach
1. **Data Source Selection**: Start with Glenn Greenwald's podcasts as the initial dataset
2. **Entity Extraction**: Identify and catalog all named entities (people, organizations, places)
3. **Claim Identification**: Document specific claims, promises, and statements
4. **Evidence Linking**: Connect each claim to its source with precise timestamps
5. **Structured Database**: Organize all extracted information in a queryable format

## Implementation Plan
- Begin with a small sample of podcast episodes to refine the extraction methodology
- Develop a structured data model that captures statements and their context
- Create a system for verifying the accuracy of extracted information
- Build a basic search interface to demonstrate the concept's utility

## Expected Outcomes
- A functioning prototype that demonstrates the core FTFM concept
- A database of entities and claims from the selected podcast episodes
- Documentation of the extraction methodology for future scaling
- Insights into challenges and opportunities for the full FTFM implementation

## Timeline
- **Data Acquisition**: November 2023
- **Model Development**: December 2023
- **Proof of Concept Completion**: January 15, 2024

## Related Components
- [[Projects/Follow The Money/Promise Tracking System|Promise Tracking System]]
- [[Projects/Follow The Money/Position Change Tracker|Position Change Tracker]]
- [[Projects/Follow The Money/Technical Architecture Overview|Technical Architecture Overview]]
- [[Projects/Follow The Money/Podcast Transcript Acquisition|Podcast Transcript Acquisition]]

## Next Steps
After successful proof of concept, the project can potentially expand to other media sources and implement more advanced features like the promise tracking and position change detection systems.