import json

def get_conversion_prompt(json_data):
    """Generate the prompt for converting JSON to markdown."""
    return f"""
# Instructions for Converting Second Brain JSON to Obsidian Markdown

## Overview
Transform structured JSON knowledge records into intuitive Obsidian markdown files that organize information for human consumption. Don't simply map JSON fields to markdown - instead, synthesize content into meaningful notes that follow Obsidian best practices.

## General Principles
1. Consolidate related ideas rather than creating many fragmented notes
2. Prioritize narrative flow and human readability over preserving data structure
3. Utilize Obsidian-specific features (links, embeds, callouts, YAML frontmatter)
4. Convert tasks and action items into checkable lists
5. Create appropriate hierarchy with headers and subheaders
6. Maintain all semantic information while reorganizing presentation
7. Generate meaningful filenames based on content rather than IDs

## JSON Data to Convert
{json.dumps(json_data, indent=2)}
```

## Output Format
For each markdown file you recommend creating, provide:

1. The file path (relative to root, such as "Projects/Project Name.md")
2. The complete markdown content for that file

Format your response as follows:

FILE: Projects/Project Name.md
```
# Project Name

[Content here...]
```

FILE: [Next file path]
```
[Next file content]
```

## Note Types to Generate

### Project Notes
For each project identified in the JSON:
- Create a comprehensive main project note with overview, status, and key details
- Include a "Related Notes" section with Obsidian links to sub-components
- Extract all associated tasks into a checklist section
- Add a YAML frontmatter with key metadata like status, priority, and deadlines
- Use callouts to highlight important warnings or insights

### Implementation Notes
For technical or implementation details:
- Create separate notes focusing on architecture and technical aspects
- Include mermaid diagrams where relationships are described
- Organize with clear technical headers
- Link back to parent project notes
- Maintain technical accuracy while improving readability

### Task Notes
For each group of related tasks:
- Consolidate into logical task categories
- Convert to Markdown task format (- [ ] Task description)
- Group by status or timeline
- Include due dates where available
- Link tasks to their relevant project notes

### Entity Notes
For important named entities (people, organizations, concepts):
- Create dedicated notes for significant entities referenced across multiple records
- Include relationships to projects
- Add relevant tags
- Establish bidirectional links

## Directory Organization
- Place projects in the "Projects/" folder
- Place areas of responsibility in the "Areas/" folder
- Place resources and reference materials in the "Resources/" folder
- Place archived items in the "Archives/" folder
- Place entities in the "Entities/" folder
- Place daily journal entries in the "Daily Notes/" folder

Please create the most useful and well-organized set of markdown files possible from this JSON data.
""" 