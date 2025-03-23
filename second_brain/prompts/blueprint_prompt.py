import json

def get_blueprint_conversion_prompt(json_data):
    """
    Output JSON blueprints instead of markdown.
    Based on the sophisticated logic in conversion_prompt.py.
    Handles structural instructions separately.
    Removes tool instructions completely.
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
# Instructions for Converting Second Brain JSON to Markdown Blueprints

## JSON Data to Convert
{json_str}

## Structural Instructions to Apply
These are special formatting and organization instructions that should guide your conversion process,
but should NOT be converted into separate markdown files themselves:

{structural_instructions_str}

## Hierarchical Organization Requirements
1. Group ALL related notes under appropriate subdirectories
2. NEVER place notes directly in root PARA folders without a subdirectory
3. Files related to the same project, area, or topic MUST be placed in a dedicated subdirectory
4. Example hierarchy:
   - Projects/Investigation/Overview.md
   - Projects/Investigation/Plan.md
   - Projects/Investigation/MVP.md

## Directory Organization
- Projects must use: "Projects/<Project Name>/<filename>.md"
- Areas must use: "Areas/<Area Name>/<filename>.md"
- Resources must use: "Resources/<Topic Name>/<filename>.md"
- Archives must use: "Archives/<Original Category>/<filename>.md"

## Organizational Files
For any collection with multiple files, create:
1. A "Contents.md" file that serves as a Map of Contents (MOC)
2. A "Tasks.md" file if there are multiple tasks or action items

Example structure:
- Projects/Investigation/Contents.md
- Projects/Investigation/Tasks.md
- Projects/Investigation/Overview.md
- Projects/Investigation/Plan.md
- Projects/Investigation/MVP.md

## Naming and Formatting Requirements
1. Use descriptive, concise filenames with spaces between words
2. Ensure filenames match the content they contain
3. Structure content with appropriate headings, lists, and formatting
4. Preserve all important information from the original records

## Note Types and Content Structure

### Project Notes
For each project:
- Create a comprehensive main project note with overview, status, and key details
- Include "Related Notes" section with links
- Extract associated tasks into a checklist section or link to tasks file
- Add context about the project's purpose, goals, and timeline
- Include any dependencies or requirements

### Implementation/Technical Notes
For technical details:
- Create separate notes focusing on architecture and technical aspects
- Include diagrams for system relationships when appropriate
- Use code blocks with appropriate syntax highlighting
- Maintain technical accuracy while improving readability
- Link to relevant external resources or documentation

### Entity Notes
For important entities (people, concepts, organizations):
- Create dedicated notes for significant entities referenced across multiple records
- Describe relationships to projects and other entities
- Include relevant background information
- Establish bidirectional links to related notes

## Special Instructions
1. Preserve ALL detailed information while reorganizing presentation
2. For complex projects, suggest canvas files to visualize relationships
3. Include direct quotes or critical content verbatim to maintain accuracy
4. Look for narrative connections between JSON records and combine logically related content

## Applying Structural Instructions
When applying the structural instructions:
1. Use them as guidance for how to organize and format the markdown content
2. Follow any specific requirements about combining or separating notes
3. Apply formatting instructions to the relevant content
4. DO NOT create separate notes for the instructions themselves
5. Prioritize instructions by their priority value if provided

## OUTPUT FORMAT
Instead of directly creating markdown files, you must output a JSON array of blueprint objects.
Each blueprint should have this structure:

{{
  "file_info": {{
    "directory": "The appropriate directory path (e.g., Projects/FTFM)",
    "filename": "A descriptive filename (e.g., Technical Architecture)",
    "record_id": "The original record_id from the source"
  }},
  "frontmatter": {{
    "tags": ["tag1", "tag2"],
    "record_ids": ["record_id1", "record_id2"],
    "goal": "The project goal (only for projects)"
  }},
  "content": {{
    "title": "The title for the note",
    "body": "The fully formatted markdown content (without the title or frontmatter)"
  }}
}}

Your response must be a valid JSON array of these blueprint objects, with no additional text or explanation.
"""
    return prompt