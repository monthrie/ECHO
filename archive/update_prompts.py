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
    """Generate a prompt focused on preserving ALL new information when updating content."""
    # Extract record details
    record_title = record.get('details', {}).get('title', 'Untitled')
    record_content = record.get('content', '')
    record_type = record.get('type', '')
    record_tags = record.get('tags', [])
    
    # Additional metadata that might be useful
    priority = record.get('details', {}).get('priority', '')
    due_date = record.get('details', {}).get('due_date', '')
    notes = record.get('details', {}).get('notes', '')
    completion_criteria = record.get('details', {}).get('completion_criteria', '')
    
    # Format tags as a string for display
    tags_str = ", ".join(record_tags)
    
    # Create a structured block of the new information that MUST be preserved
    must_preserve = f"""
NEW CONTENT THAT MUST BE PRESERVED:

* Title: {record_title}
* Content: {record_content}
* Type: {record_type}
* Tags: {tags_str}
"""
    
    if priority:
        must_preserve += f"* Priority: {priority}\n"
    if due_date:
        must_preserve += f"* Due Date: {due_date}\n"
    if notes:
        must_preserve += f"* Notes: {notes}\n"
    if completion_criteria:
        must_preserve += f"* Completion Criteria: {completion_criteria}\n"
    
    return f"""
You are updating an Obsidian markdown file with new information. Your PRIMARY GOAL is to ensure that EVERY PIECE of new information is incorporated into the document - nothing should be lost.

EXISTING FILE CONTENT:
markdown
{existing_content}

{must_preserve}

CRITICAL INSTRUCTIONS:
1. Ensure all important new information is incorporated into the document
2. Integrate new content thoughtfully while maintaining document coherence
3. Add all new tags to the frontmatter (keeping existing tags)
4. For tasks or action items, add them appropriately, avoiding exact duplicates
5. If new content contradicts existing content, include both with a note about the update
6. Maintain proper markdown formatting throughout
7. Use your judgment to organize information logically

APPROACH:
1. Identify key new information not present in the existing content
2. Find the most appropriate location in the document to add each piece
3. Integrate new content naturally, extending the document structure as needed
4. For tasks, add them to a Tasks/To-Do section (create one if needed)
5. For concepts or ideas, integrate them in relevant sections or create new ones

The updated content should be coherent and well-organized, incorporating the valuable new information.

Your response must ONLY contain the complete updated markdown content with no additional text or explanations. Begin with the YAML frontmatter and include the entire document.
"""