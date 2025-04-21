import json

def get_blueprint_conversion_prompt(json_data):
    """
    Output JSON blueprints using the new Blueprint Maker approach.
    Takes input JSON data and returns a prompt string.
    """
    # Extract only structural instructions for reference in the prompt
    structural_instructions = []
    
    # Create a clean copy
    clean_json = json_data.copy()
    
    # Process system_instructions if they exist
    if "system_instructions" in clean_json:
        # Extract structural instructions before removing them all
        structural_instructions = [
            instruction for instruction in clean_json["system_instructions"] 
            if instruction.get("instruction_type") == "structural"
        ]
        
        # Remove all system_instructions from the JSON
        del clean_json["system_instructions"]
    
    json_str = json.dumps(clean_json, indent=2)
    structural_instructions_str = json.dumps(structural_instructions, indent=2) if structural_instructions else "[]"
    
    prompt = f"""
# Blueprint Creation Prompt

## Purpose
Transform structured JSON records into a concise set of Obsidian markdown files. Your primary goal is to avoid unnecessary fragmentation of information while creating an intuitive, practical knowledge organization.

## Input
A JSON object containing:
- A `session` object with metadata
- A `records` array containing knowledge entries
- A `system_instructions` array containing any organizational directives

## Input JSON Data
{json_str}

## Structural Instructions to Apply
{structural_instructions_str}

## Output
An array of blueprint objects, each representing a markdown file:

```json
{{
  "file_info": {{
    "directory": "Appropriate directory path based on content",
    "filename": "Descriptive filename with spaces",
    "record_id": "Original record_id if available"
  }},
  "frontmatter": {{
    "tags": ["relevant", "tags"],
    "description": "Concise description of the note's purpose"
  }},
  "content": {{
    "title": "Note title",
    "body": "Fully formatted markdown content"
  }}
}}
```

## Core Principles

### Strong Consolidation Preference
- By default, aim for a maximum of one note per record in the input
- Look for opportunities to further consolidate records into fewer notes when content is closely related
- Only create multiple notes from a single record when there is a compelling reason (such as explicit user instructions)
- Prioritize comprehensive, well-structured notes over numerous smaller notes

### Content-Driven Organization
- Organize content primarily by topic, not by record structure
- Place conceptually related information together, even if it spans multiple records
- Use clear section headings within notes to delineate different components
- Consider how the user would naturally think about and access the information

### Minimal File Structure
- Create the smallest number of files that effectively organizes the content
- For small to medium amounts of content (under ~2000 words total), consider using a single note with clear sections
- Only create separate directory structures when dealing with clearly distinct topic areas
- Avoid creating "special" files (like Contents.md) for small collections

### Explicit Instruction Priority
- Only create separate notes for specific structural directives from the user
- When a user explicitly requests a separate note, honor that request
- Otherwise, default to consolidation and simplicity
- Interpret ambiguous instructions in favor of fewer, more comprehensive notes

## Markdown Best Practices

### Effective Internal Structure
- Use clear heading hierarchy (H2 and below) to organize content within notes
- Create logical sections that group related information
- For longer notes, consider adding a brief table of contents at the beginning
- Use formatting (lists, emphasis, etc.) to enhance readability

### Knowledge Connections
- Create links between separate notes using Obsidian's `[[File Name]]` syntax
- For content within the same note, use heading links with Obsidian's syntax: `[[File Name#Section Heading]]`
- Add a "Related Notes" section only when there are actual separate notes to link to
- Maintain the semantic connections present in the original records

### Task Management
- Format actionable items as markdown task lists: `- [ ] Task description`
- Keep tasks with their relevant context rather than extracting to separate files
- Only create a dedicated tasks file if explicitly requested or if there are many tasks spanning multiple distinct topics
- Ensure tasks maintain clear association with their parent topics

## Frontmatter Guidelines
- Include meaningful tags that aid in finding and categorizing the note
- Provide a concise, informative description that captures the note's essence
- Keep frontmatter simple and focused on user-relevant metadata
- Use consistent tag formatting (lowercase, hyphenated multi-word tags)

## Implementation Strategy

1. Start by assuming each record will become at most one note
2. Look for opportunities to consolidate records into even fewer notes based on topic relationships
3. Only create separate notes when:
   - Explicitly directed by user instructions
   - The content represents truly distinct topic areas that would be unnaturally combined
   - Combining would create an excessively long note (>3000 words) that covers multiple major topics
4. Create a simple, logical directory structure, avoiding unnecessary nesting
5. Implement a clear internal structure within each note using headings, lists, and formatting

Remember: The goal is to create a concise, well-organized knowledge structure that avoids unnecessary fragmentation. A small number of comprehensive, well-structured notes is generally preferable to many small notes.

Output only valid JSON with nothing before AND nothing after
"""
    return prompt