import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration for Second Brain application."""
    
    # API Settings
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MODEL = os.getenv("MODEL", "anthropic/claude-3-haiku-20240307")
    
    # File Paths
    DB_PATH = os.getenv("DB_PATH", "second_brain.db")
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", 
                                   os.path.join(os.getcwd(), "markdown_output"))
    JSON_OUTPUT_DIR = os.getenv("JSON_OUTPUT_DIR", "output_jsons")
    INDEX_FILE = "file_index.csv"
    
    # Embedding Settings
    QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_storage")
    COLLECTION_NAME = "markdown_notes"
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = 384  # for MiniLM-L6-v2
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def setup_logging(cls):
        """Configure logging based on settings."""
        numeric_level = getattr(logging, cls.LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
            
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("second_brain.log"),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger("SecondBrain")
    
    @classmethod
    def initialize(cls):
        """Initialize required directories and validate configuration."""
        # Create necessary directories
        Path(cls.JSON_OUTPUT_DIR).mkdir(exist_ok=True)
        Path(cls.OBSIDIAN_VAULT_PATH).mkdir(exist_ok=True, parents=True)
        Path(os.path.dirname(cls.QDRANT_PATH)).mkdir(exist_ok=True, parents=True)
        
        # Validate critical settings
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
        # Setup logging
        logger = cls.setup_logging()
        logger.info(f"Initialized with vault path: {os.path.abspath(cls.OBSIDIAN_VAULT_PATH)}")
        logger.info(f"Using model: {cls.MODEL}")
        logger.info(f"Database path: {cls.DB_PATH}")
        
        return cls
