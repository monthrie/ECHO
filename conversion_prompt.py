import json

def get_conversion_prompt(json_data):
    """Generate the prompt for converting JSON to markdown."""
    prompt = f"""
# Instructions for Converting Second Brain JSON to Obsidian Markdown with Hierarchical Organization

## IMPORTANT: Create Proper Subdirectory Structure
You MUST organize related notes into subdirectories. Do not place notes in a flat structure.

## JSON Data to Convert
{json.dumps(json_data, indent=2)}

## Hierarchical Organization Requirements
1. Group ALL related notes under appropriate subdirectories
2. NEVER place notes directly in root PARA folders without a subdirectory
3. Files related to the same project, area, or topic MUST be placed in a dedicated subdirectory
4. Example hierarchy:
   - Projects/FTFM/Overview.md
   - Projects/FTFM/MVP-Plan.md
   - Projects/FTFM/Technical-Architecture.md

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
- Projects/FTFM/Contents.md
- Projects/FTFM/Tasks.md
- Projects/FTFM/Technical-Architecture.md
- Projects/FTFM/MVP-Plan.md

## Naming and Formatting Requirements
1. Use descriptive, concise filenames with hyphens between words
2. USE ONLY YAML FRONTMATTER at the beginning of each file - DO NOT add H1 headings
3. After the YAML frontmatter, begin your content directly with paragraph text
4. Ensure filenames match the content they contain
5. Use only hyphens (-) for word separation in filenames, never spaces or underscores

## YAML Frontmatter Format
Every file should begin with YAML frontmatter in this format:
```yaml
---
tags: [relevant, tags, here]
status: active/completed/planning
priority: high/medium/low
due: YYYY-MM-DD
created: YYYY-MM-DD
---
```

## Content Organization Principles
1. Consolidate related ideas rather than creating many fragmented notes
2. Prioritize narrative flow and human readability over preserving data structure
3. Convert tasks and action items into checkable lists (- [ ] format)
4. Use only H2 (##) and below for content headings, NEVER use H1 (#)
5. Maintain all semantic information while reorganizing for human consumption

## Obsidian-Specific Features
1. Use proper [[link]] syntax for internal links between related notes - ensure filenames match exactly
2. Utilize callouts for important warnings or insights (> [!note] format)
3. Create mermaid diagrams for technical relationships where appropriate
4. Use embedded files (![[filename]]) for related content when relevant

## Note Types and Content Structure

### Project Notes
For each project:
- Create a comprehensive main project note with overview, status, and key details
- Include "Related Notes" section with Obsidian links
- Extract associated tasks into a checklist section or link to tasks file
- Add context about the project's purpose, goals, and timeline
- Include any dependencies or requirements

### Implementation/Technical Notes
For technical details:
- Create separate notes focusing on architecture and technical aspects
- Include mermaid diagrams for system relationships
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
5. Format dates for human readability in content but maintain machine-readable formats in frontmatter
6. Create index notes that help navigate complex topic areas

## Output Format
For each markdown file you recommend creating, provide:

FILE: <directory>/<subdirectory>/<filename>.md
---
tags: [tag1, tag2]
status: active/completed/planning
priority: high/medium/low
due: YYYY-MM-DD
created: YYYY-MM-DD
---

[Start content directly here with paragraph text - DO NOT add a title or H1 heading]

Please create the most useful and well-organized set of markdown files possible from this JSON data."""
    
    return prompt