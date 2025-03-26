import re
import csv
import io
from pathlib import Path

def text_to_csv_ready(text, is_markdown=False):
    """
    Convert any text into CSV-ready format by:
    1. Removing only Markdown syntax (not content) if specified
    2. Replacing newlines with spaces
    3. Properly escaping the text for CSV
    
    Args:
        text (str): The input text to be processed
        is_markdown (bool): Whether the text contains Markdown formatting
    
    Returns:
        str: CSV-ready text that can be safely pasted into a CSV file
    """
    # If the text is Markdown, remove only the syntax markers, not the content
    if is_markdown:
        # Remove header markers but keep the text
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove emphasis markers (* and _) but keep the content
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'__(.+?)__', r'\1', text)      # Bold
        text = re.sub(r'_(.+?)_', r'\1', text)        # Italic
        
        # Extract link text [text](url) -> text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # Remove code block markers but keep the code content
        text = re.sub(r'```[\w]*\n', '', text)  # Opening code fence
        text = re.sub(r'```$', '', text, flags=re.MULTILINE)  # Closing code fence
        
        # Remove inline code markers but keep the code
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # Remove blockquote markers but keep the text
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        
        # Remove horizontal rules
        text = re.sub(r'^-{3,}$', ' ', text, flags=re.MULTILINE)
        text = re.sub(r'^[*_]{3,}$', ' ', text, flags=re.MULTILINE)
        
        # Remove list markers but keep the content
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # Unordered lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # Ordered lists
    
    # Replace all newlines with spaces
    text = re.sub(r'\n+', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Use the CSV module to properly escape the text
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([text.strip()])
    
    # Get the CSV-formatted text without the trailing newline
    csv_text = output.getvalue().strip()
    
    return csv_text

def process_file(file_path, is_markdown=None):
    """
    Process a file and return CSV-ready text
    
    Args:
        file_path (str): Path to the file
        is_markdown (bool): Whether the file is Markdown. If None, will be auto-detected from extension
        
    Returns:
        str: CSV-ready text
    """
    path = Path(file_path)
    
    # Auto-detect if file is Markdown based on extension if not specified
    if is_markdown is None:
        is_markdown = path.suffix.lower() in ['.md', '.markdown']
    
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    return text_to_csv_ready(text, is_markdown)

def main():
    # Example usage
    example_text = """This is a note with
    multiple lines. It has some "quoted text" and some text with, commas.
    
    ## Markdown heading
    
    * Bullet point 1
    * Bullet point 2
    
    [A link](https://example.com)
    
    ```python
    def hello():
        print("Hello world!")
    ```
    """
    
    # Process as regular text
    csv_ready_text = text_to_csv_ready(example_text)
    print("Regular text processing:")
    print(csv_ready_text)
    print()
    
    # Process as Markdown
    csv_ready_md = text_to_csv_ready(example_text, is_markdown=True)
    print("Markdown processing:")
    print(csv_ready_md)
    
    # You can also process files directly
    # csv_ready_file = process_file("your_file.md")
    # print(csv_ready_file)

if __name__ == "__main__":
    main()