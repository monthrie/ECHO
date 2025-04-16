---
tags: ["promise tracking", "political accountability", "automated verification", "FTFM"]
record_ids: ["98e7d6c5-4b3a-2f1e-a9c8-7d6e5f4a3b2c"]
goal: Create an automated system for tracking and verifying public promises
---

# FTFM Promise Tracking System

## Overview
The Promise Tracking System will automatically flag promises made by public figures and track their future fulfillment. For example, when a politician says 'I will do X on my first day in office', the system records this claim and checks whether it was accomplished when the deadline arrives.

## Key Features

### Promise Detection
- Natural language processing to identify commitment statements
- Classification of promises by type (policy, personal, timeline-specific, etc.)
- Extraction of specific deadlines or conditions attached to promises

### Temporal Tracking
- Calendar-based monitoring of promise deadlines
- Event correlation to match promises with subsequent actions
- Notification system for approaching or passed deadlines

### Verification Framework
- Evidence collection for promise fulfillment assessment
- Multi-source verification to confirm status
- Classification system for promise status (fulfilled, broken, in progress, modified)

### Reporting Interface
- Dashboard showing promise fulfillment rates by individual or organization
- Timeline visualization of promises and their status
- Evidence links for each promise status determination

## Implementation Considerations
- Will require sophisticated temporal awareness and event correlation capabilities
- Need to distinguish between explicit promises and general statements of intent
- Must account for contextual factors that might legitimately affect promise fulfillment

## Applications
- Political campaign promise tracking
- Government accountability monitoring
- Corporate commitment verification
- Public figure consistency assessment

## Timeline
- Design and architecture: December 2023 - January 2024
- Initial implementation: February 2024
- Testing and refinement: Ongoing through February 2024
- Completion deadline: February 28, 2024

## Related Components
- [[Projects/Follow The Money/Proof of Concept Proposal|Proof of Concept Proposal]]
- [[Projects/Follow The Money/Position Change Tracker|Position Change Tracker]]
- Temporal Tracking Module