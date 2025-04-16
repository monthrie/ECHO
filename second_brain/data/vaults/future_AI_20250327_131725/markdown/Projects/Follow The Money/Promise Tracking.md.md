---
tags: ["promise tracking", "politician accountability", "pattern detection", "political statements", "automated flagging"]
record_ids: ["c4d5e6f7-a8b9-4c0d-e1f2-g3h4i5j6k7l8"]
goal: Develop an automated system to track promises made by public figures and flag fulfillment or non-fulfillment
---

# Promise and Pattern Tracking Feature

## Feature Overview

The FTFM system would detect and flag significant events, such as when a politician makes a promise (e.g., 'I will do X on my first day in office'). These would be tagged as events or promises, and the system would track whether those promises are fulfilled. This creates a mechanism for identifying patterns in behavior and statements over time.

## Promise Detection

The system will identify several types of commitments:

1. **Explicit promises**: Clear statements of intent ("I will lower taxes")
2. **Conditional promises**: Commitments with conditions ("If elected, I will...")
3. **Timebound commitments**: Promises with deadlines ("Within my first 100 days...")
4. **Policy positions**: Stated stances on issues ("I support/oppose X")
5. **Predictions**: Claims about future events ("This policy will lead to...")

## Tracking Mechanisms

For each promise or commitment, the system will:

- Record the exact statement with timestamp and source
- Identify the speaker and relevant entities
- Classify the type of commitment
- Track subsequent statements about the same topic
- Monitor for fulfillment events or contradictory statements
- Calculate a "consistency score" for individuals over time

## Pattern Recognition

By aggregating promises and tracking their outcomes, the system can identify patterns such as:

- Politicians who consistently make promises they don't keep
- Topics where positions frequently shift
- Correlations between promise fulfillment and external factors
- Cascading effects where one public figure's statements influence others

## Implementation Approach

1. Develop NLP models to identify commitment language
2. Create a classification system for promise types
3. Implement a tracking database with status fields
4. Design algorithms to detect fulfillment or contradiction events
5. Build visualization tools to display promise fulfillment rates

## Use Cases

This feature would be particularly valuable during:

- Election campaigns
- First 100 days of new administrations
- Legislative sessions
- Crisis response situations
- Policy implementation periods

## Related Notes

- [[Projects/Follow The Money/Project Overview|Project Overview]]
- [[Projects/Follow The Money/Society Storage Layer|Society Storage Layer]]
- [[Projects/Follow The Money/RAG Query System|RAG Query System]]