from pathlib import Path
import os
from archive.json_to_obsidian import convert_all_json_files
from archive.config import Config


if __name__ == "__main__":
    # Validate configuration
    Config.initialize()
    
    # Run only the conversion part
    print("Starting conversion of JSON files to Obsidian markdown...")
    convert_all_json_files(Config)
    print("Conversion complete! Check the markdown_output directory.") 