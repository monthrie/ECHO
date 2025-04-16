---
tags: ["FTFM", "data acquisition", "transcripts", "Glenn Greenwald"]
record_ids: ["9d8c7b6a-5f4e-3d2c-1b0a-9e8d7f6a5b4c"]
goal: Gather initial test data for FTFM entity extraction model
---

# Acquire Glenn Greenwald Podcast Transcripts

## Task Description
Obtain transcripts from one or two Glenn Greenwald podcasts to use as initial test data for the FTFM model development. These transcripts will serve as the foundation for our entity extraction and claim identification processes.

## Selection Criteria
- Choose episodes that contain significant political claims or discussions of public figures
- Look for episodes with verifiable statements that can be fact-checked
- Select content that includes a variety of entity types (people, organizations, locations)
- Prioritize episodes discussing current events with follow-up coverage

## Acquisition Methods
1. **Check for Existing Transcripts**
   - Review Glenn Greenwald's website or podcast platform for official transcripts
   - Contact the podcast production team to request transcripts if available

2. **Transcription Services**
   - If existing transcripts aren't available, use a professional transcription service
   - Options include Rev.com, Trint, Otter.ai, or similar services
   - Budget approximately $1-1.50 per minute of audio for professional transcription

3. **Automated Transcription**
   - As a fallback, use automated transcription tools like Whisper AI
   - Will require manual review and correction for accuracy

## Post-Processing
- Format transcripts consistently for processing
- Add speaker identification where possible
- Include timestamps at regular intervals (ideally every 30 seconds)
- Save in both plain text and structured formats (JSON)

## Timeline
- Identify suitable episodes: By November 20, 2023
- Acquire/create transcripts: By November 30, 2023

## Next Steps
- Once transcripts are obtained, begin entity extraction process
- Use transcripts to test and refine the data processing pipeline
- Document any challenges or insights from the transcription process

## Related Items
- [[Projects/Follow The Money/Proof of Concept Proposal|Proof of Concept Proposal]]
- Data Processing Pipeline