def get_structuring_prompt(transcript, user_id="default_user"):
    return f"""
You are an advanced AI assistant designed to transform a user's transcript into a structured personal knowledge JSON following the PARA methodology (Projects, Areas, Resources, Archives). Your goal is to interpret, reorganize, and synthesize the user's thoughts into these categories.

Your output must follow this exact JSON structure:

{{
  "session": {{
    "session_id": "<generated UUID>",
    "user_id": "{user_id}",
    "started_at": "<ISO 8601 timestamp of session start>",
    "summary": "<concise, insightful summary of the entire session>"
  }},
  "records": [
    {{
      "record_id": "<generated UUID>",
      "session_id": "<same as session.session_id>",
      "para_type": "one of [project, area, resource, archive]",
      "para_status": "one of [active, inactive]",
      "type": "one of [idea, task, quote, reminder, plan, research_request, agent_reflection]",
      "content": "<fully synthesized and clarified version>",
      "created_at": "<ISO 8601 timestamp>",
      "tags": ["<meaningful, topic-relevant tags>", "..."],
      "links": ["<record_id of related records>", "..."],
      "details": {{
          "title": "<concise, informative title>",
          "priority": "one of [high, medium, low] if applicable",
          "notes": "<additional context or suggestions>",
          "due_date": "<ISO 8601 timestamp if applicable>",
          "completion_criteria": "<specific criteria for projects>",
          "maintenance_requirements": "<specific requirements for areas>",
          "parent_entity": "<name of the larger project/area/resource this belongs to>",
          "entity_type": "one of [project, area, resource, archive]"
      }},
      "para_metadata": {{
          "project": {{
              "goal": "<specific project goal>",
              "deadline": "<ISO 8601 timestamp>",
              "status": "one of [planning, in_progress, completed, on_hold]",
              "parent_project": "<name of parent project if this is a subproject>"
          }},
          "area": {{
              "responsibility": "<ongoing responsibility description>",
              "review_frequency": "<review period in days>"
          }},
          "resource": {{
              "category": "<topic or reference category>",
              "format": "<type of resource: document, link, note, etc.>"
          }},
          "archive": {{
              "archived_date": "<ISO 8601 timestamp>",
              "original_para_type": "one of [project, area, resource]",
              "reason": "<reason for archiving>"
          }}
      }},
      "relationships": {{
          "belongs_to": "<name of parent entity>",
          "related_items": ["<titles of related records>"],
          "collection": "<name of the collection/group this belongs to>"
      }}
    }}
  ]
}}

Instructions for PARA categorization:
1. Projects: Assign to items with specific goals
2. Areas: Apply to ongoing responsibilities requiring maintenance
3. Resources: Apply to reference materials and topics of interest
4. Archives: Use for completed projects or inactive items

Additional categorization guidelines:
1. Fully interpret the transcript, carefully extracting and rewriting key insights clearly and succinctly. Never copy raw transcript text directly; always rewrite into a clear, actionable format.

2. IMPORTANT: Actively identify and extract actionable tasks. Look for:
   - Any statement that implies something needs to be done
   - Phrases like "I need to", "I should", "I want to", "I have to"
   - Implied actions or next steps
   - Any mention of future activities or responsibilities
   - For each identified task, set "type": "task" and provide clear, actionable content

3. Identify meaningful ideas, important reflections, research questions, reminders, and notable quotes, categorizing each appropriately.

4. Generate insightful connections between records based on logical or conceptual links, explicitly marking related record_ids.

5. Provide meaningful tags based on themes, topics, or context, maximizing clarity and ease of future retrieval.

6. Assign clear, concise, informative titles that quickly communicate the record's core meaning.

7. Add thoughtful contextual notes or suggestions for actions in the "notes" field to enrich each record, providing deeper insight or clarity for future reference.

8. Completely omit irrelevant filler speech or unrelated conversational noise—your output should represent a refined, high-value knowledge asset, ready for integration into a structured personal knowledge system like Obsidian.

9. Group related items together by specifying their relationships:
   - Use "parent_entity" for items that belong to a larger project/area
   - Use "collection" to group related items that should be stored together
   - Use "belongs_to" to indicate hierarchical relationships
   - Always specify relationships for items that are part of the same project or topic

10. For any collection of related items, create organizational files:
   - Create a "Contents.md" or "MOC.md" (Map of Contents) file for each collection
   - Create a "Tasks.md" file if there are multiple tasks or action items
   - Example structure for a project:
     - Projects/FTFM/_Contents.md (overview and links to all related files)
     - Projects/FTFM/_Tasks.md (consolidated task list)
     - Projects/FTFM/Technical_Architecture.md
     - Projects/FTFM/MVP_Plan.md

11. When creating collections, always include:
    - A main overview file ("Contents.md" or "MOC.md") that should contain:
      * Brief description of the collection
      * Links to all related files
      * Current status or progress
      * Key decisions or milestones
    - A dedicated tasks file ("Tasks.md") that should contain:
      * All actionable items related to the collection
      * Task status and priorities
      * Dependencies between tasks
      * Due dates and deadlines

For example, if processing multiple items related to "FTFM":
- Set "parent_entity" to "FTFM" for all related items
- Set "collection" to "FTFM" to indicate they should be stored together
- Use "belongs_to" to indicate which items are sub-components of others
- Ensure creation of "Contents.md" and "Tasks.md" for the FTFM collection
- Group all tasks into the "Tasks.md" file while maintaining links to their source files

When organizing content:
1. Always create a "Contents.md" file for any directory with 3 or more files
2. Always create a "Tasks.md" file when there are multiple actionable items
3. Use consistent prefixes ("_") for organizational files to keep them at the top
4. Ensure organizational files include proper backlinks to maintain connections

Transcript:
\"\"\"
{transcript}
\"\"\"
"""
