def get_summary_prompt(content):
    """Generate a prompt for summarizing file content."""
    return f"""
Please create a concise summary of the following Markdown content. Focus on:
1. The key topics and themes
2. Main projects or entities mentioned
3. Core information or knowledge represented
4. Primary purpose of the document

Your summary should be approximately 2-3 sentences and no more than 150 characters.

CONTENT:
{content}
"""

def get_integration_decision_prompt(record, matching_files):
    """Generate a prompt for deciding how to integrate a new record."""
    # Format the record data
    record_title = record.get('details', {}).get('title', 'Untitled')
    record_content = record.get('content', '')
    record_type = record.get('type', '')
    record_para_type = record.get('para_type', '')
    record_tags = ", ".join(record.get('tags', []))
    
    # Format matching files
    matching_files_text = ""
    for i, match in enumerate(matching_files, 1):
        matching_files_text += f"""
{i}. File Path: {match['file_path']}
   Summary: {match['summary']}
   Tags: {match['tags']}
   Match Score: {match['score']}
"""
    
    return f"""
You are a knowledge management assistant helping organize notes according to the PARA method (Projects, Areas, Resources, Archives).

You need to decide how to integrate a new piece of information with the existing knowledge base.

NEW RECORD:
Title: {record_title}
Type: {record_type}
PARA Type: {record_para_type}
Tags: {record_tags}

Content:
{record_content}

POTENTIAL MATCHING FILES:
{matching_files_text if matching_files else "No matching files found."}

Based on the information above, decide the best way to integrate this new record by choosing ONE of these options:

1. UPDATE: Choose a specific existing file to update with this new information. Select this if the new content clearly belongs in an existing file and adds to it without drastically changing its focus.

2. MERGE: Choose multiple existing files to merge with this new information. Select this if the new content bridges multiple existing files that should be consolidated.

3. CREATE: Create a new file for this content. Select this if the content represents a new topic or doesn't closely align with existing files.

IMPORTANT INSTRUCTIONS:
- Respond in this exact format:
  DECISION: UPDATE/MERGE/CREATE
  FILE(S): [If UPDATE: file path, If MERGE: list of file paths, If CREATE: leave blank]
  REASON: [Brief explanation of your decision]

- If the match score is very low (below 5) or the content doesn't clearly relate to existing files, prefer CREATE.
- If the content would significantly expand or alter the scope of an existing file, prefer CREATE.
- If the content is a task that belongs to an existing project, prefer UPDATE.
- If the content is a new perspective on an existing topic, prefer UPDATE.
"""

def get_content_update_prompt(existing_content, record):
    """Generate a prompt for updating existing content with new information."""
    record_title = record.get('details', {}).get('title', 'Untitled')
    record_content = record.get('content', '')
    record_type = record.get('type', '')
    
    return f"""
You are tasked with updating an existing Obsidian markdown file with new information.

EXISTING FILE CONTENT:
```markdown
{existing_content}
```

NEW INFORMATION TO INCORPORATE:
Title: {record_title}
Type: {record_type}
Content: {record_content}

Please update the file content by:
1. Preserving the existing YAML frontmatter (but updating tags if relevant)
2. Integrating the new information in the most appropriate section
3. Creating a new section if necessary (but only if it doesn't fit elsewhere)
4. Avoiding duplication of information
5. Maintaining the overall document structure and flow
6. If it's a task, add it to a tasks or to-do section (creating one if needed)
7. If it's an update to existing information, integrate it seamlessly
8. If it contradicts existing information, update the existing content noting the change
9. Maintain proper markdown formatting throughout

CRITICAL: Your response must ONLY contain the complete updated markdown content with no additional text, explanations, code blocks, or formatting. Do not include phrases like "Here's the updated content" or "```markdown" tags. The output should be ready to be written directly to a file.
"""