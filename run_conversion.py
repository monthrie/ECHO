from pathlib import Path
import os
from dotenv import load_dotenv
from json_to_obsidian import convert_all_json_files

# Load environment variables
load_dotenv()

# Simple Config class that mimics the one in main.py
class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    DB_PATH = os.getenv("DB_PATH", "second_brain.db")
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", 
        "/Users/wilmon/Documents/projects/ECHO/markdown_output")
    MODEL = os.getenv("MODEL", "deepseek/deepseek-chat:free")
    JSON_OUTPUT_DIR = "output_jsons"
    
    @classmethod
    def validate(cls):
        print(f"API Key: {cls.OPENROUTER_API_KEY}")
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        # Create JSON output directory if it doesn't exist
        Path(cls.JSON_OUTPUT_DIR).mkdir(exist_ok=True)

if __name__ == "__main__":
    # Validate configuration
    Config.validate()
    
    # Run only the conversion part
    print("Starting conversion of JSON files to Obsidian markdown...")
    convert_all_json_files(Config)
    print("Conversion complete! Check the markdown_output directory.") 