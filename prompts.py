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
          "maintenance_requirements": "<specific requirements for areas>"
      }},
      "para_metadata": {{
          "project": {{
              "goal": "<specific project goal>",
              "deadline": "<ISO 8601 timestamp>",
              "status": "one of [planning, in_progress, completed, on_hold]"
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
      }}
    }}
  ]
}}

Instructions for PARA categorization:
1. Projects: Assign to items with specific goals and deadlines
2. Areas: Use for ongoing responsibilities without end dates
3. Resources: Apply to reference materials and topics of interest
4. Archives: Use for completed projects or inactive items

Additional categorization guidelines:
1. Fully interpret the transcript, carefully extracting and rewriting key insights clearly and succinctly. Never copy raw transcript text directly; always rewrite into a clear, actionable format.
2. Identify actionable tasks, meaningful ideas, important reflections, research questions, reminders, and notable quotes, categorizing each appropriately.
3. Generate insightful connections between records based on logical or conceptual links, explicitly marking related record_ids.
4. Provide meaningful tags based on themes, topics, or context, maximizing clarity and ease of future retrieval.
5. Assign clear, concise, informative titles that quickly communicate the record's core meaning.
6. Add thoughtful contextual notes or suggestions for actions in the "notes" field to enrich each record, providing deeper insight or clarity for future reference.
7. Include a priority level (high, medium, low) for tasks and research requests based on urgency or significance inferred from the transcript.
8. Completely omit irrelevant filler speech or unrelated conversational noise—your output should represent a refined, high-value knowledge asset, ready for integration into a structured personal knowledge system like Obsidian.

Transcript:
\"\"\"
{transcript}
\"\"\"
"""
