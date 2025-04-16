---
tags: ["MVP", "Glenn Greenwald", "podcasts", "entity extraction", "proof of concept"]
record_ids: ["7e8f9a0b-c1d2-4e3f-a4b5-c6d7e8f9a0b1", "g8h9i0j1-k2l3-4m5n-o6p7-q8r9s0t1u2v3"]
goal: Create a functioning prototype using Glenn Greenwald's podcasts as source material
---

# MVP Concept for FTFM

## Minimum Viable Product Approach

For an MVP (Minimum Viable Product) of the FTFM project, we will focus on mapping all episodes of Glenn Greenwald's podcasts over the last six months. This targeted approach allows us to test the core functionality with a manageable dataset before expanding to additional media sources.

## MVP Scope

1. **Data Collection**: Obtain transcripts for 10-20 episodes of Glenn Greenwald's podcasts
2. **Entity Extraction**: Identify all named entities (people, organizations, events, laws)
3. **Claim Identification**: Extract specific claims made about these entities
4. **Reference Linking**: Connect each claim to the exact timestamp in the source material
5. **Basic Search**: Implement simple search functionality across the extracted data

## Implementation Steps

1. **Transcript Acquisition**: Obtain podcast transcripts through automated transcription services or manual transcription
2. **Processing Pipeline**: Develop a system to process transcripts and extract structured data
3. **Storage Schema**: Create a database schema to store entities and claims
4. **Basic UI**: Implement a simple interface for browsing and searching the data
5. **Testing & Validation**: Verify accuracy of entity and claim extraction

## Success Criteria

- Successfully process at least 10 podcast episodes
- Achieve >80% accuracy in entity extraction
- Identify at least 50 substantive claims per episode
- Create a searchable database of all extracted information
- Demonstrate the ability to track a specific entity across multiple episodes

## Next Steps After MVP

- Expand to additional podcast hosts and media sources
- Implement more sophisticated NLP for claim extraction
- Develop contradiction and promise tracking features
- Create visualization tools for entity relationships
- Scale the processing pipeline for larger volumes of content

## Initial Task

- [ ] Obtain transcripts for one or two of Glenn Greenwald's podcasts as initial test data

## Related Notes

- [[Projects/Follow The Money/Project Overview|Project Overview]]
- [[Projects/Follow The Money/Technical Architecture|Technical Architecture]]
- [[Projects/Follow The Money/Tasks|Project Tasks]]