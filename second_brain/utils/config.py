import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration for Second Brain application."""
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent  # This points to the second_brain directory
    PROJECT_ROOT = BASE_DIR.parent  # This points to the project root (ECHO)
    INPUT_DIR = str(BASE_DIR / "data" / "input")
    VAULTS_BASE_DIR = str(BASE_DIR / "data" / "vaults")
    
    # API settings
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MODEL = os.getenv("MODEL", "anthropic/claude-3.7-sonnet")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    
    # Database settings
    DB_PATH = str(PROJECT_ROOT / "second_brain.db")
    
    # Runtime paths (set during initialization)
    TRANSCRIPTS_PATH = None
    CURRENT_TRANSCRIPT_NAME = None
    CURRENT_VAULT_DIR = None
    JSON_OUTPUT_DIR = None
    BLUEPRINTS_DIR = None
    MARKDOWN_OUTPUT_DIR = None
    
    # Embedding Settings
    QDRANT_PATH = os.getenv("QDRANT_PATH", str(BASE_DIR / "second_brain" / "data" / "qdrant_storage"))
    COLLECTION_NAME = "markdown_notes"
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = 384  # for MiniLM-L6-v2
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = str(PROJECT_ROOT / "second_brain.log")
    
    @classmethod
    def setup_logging(cls):
        """Set up logging configuration."""
        # Create a logger
        logger = logging.getLogger("SecondBrain")
        logger.setLevel(logging.INFO)
        
        # Create handlers
        log_file = cls.LOG_FILE
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.info(f"Logger initialized successfully")
        return logger
    
    @classmethod
    def initialize(cls, transcript_file=None):
        """Initialize configuration with runtime paths."""
        # Set up logging
        logger = cls.setup_logging()
        
        # If no transcript file is specified, list available transcripts
        if transcript_file is None:
            transcript_files = list(Path(cls.INPUT_DIR).glob("*.csv"))
            if not transcript_files:
                logger.error(f"No transcript files found in {cls.INPUT_DIR}")
                raise FileNotFoundError(f"No transcript files found in {cls.INPUT_DIR}")
            
            # Use the first transcript file by default
            transcript_file = transcript_files[0]
            logger.info(f"No transcript specified, using: {transcript_file.name}")
        else:
            # Make sure the transcript file exists
            transcript_path = Path(transcript_file)
            if not transcript_path.is_absolute():
                transcript_path = Path(cls.INPUT_DIR) / transcript_path
            
            if not transcript_path.exists():
                logger.error(f"Transcript file not found: {transcript_path}")
                raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
            
            transcript_file = transcript_path
        
        # Set the current transcript path
        cls.TRANSCRIPTS_PATH = str(transcript_file)
        
        # Extract the base name without extension for vault naming
        cls.CURRENT_TRANSCRIPT_NAME = transcript_file.stem
        
        # Create the base vaults directory if it doesn't exist
        Path(cls.VAULTS_BASE_DIR).mkdir(parents=True, exist_ok=True)
        
        # Create a vault directory for this transcript
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cls.CURRENT_VAULT_DIR = Path(cls.VAULTS_BASE_DIR) / f"{cls.CURRENT_TRANSCRIPT_NAME}_{timestamp}"
        cls.CURRENT_VAULT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Set up the directory structure for this run
        cls.JSON_OUTPUT_DIR = str(cls.CURRENT_VAULT_DIR / "json")
        Path(cls.JSON_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        
        cls.BLUEPRINTS_DIR = str(cls.CURRENT_VAULT_DIR / "blueprints")
        Path(cls.BLUEPRINTS_DIR).mkdir(parents=True, exist_ok=True)
        
        cls.MARKDOWN_OUTPUT_DIR = str(cls.CURRENT_VAULT_DIR / "markdown")
        Path(cls.MARKDOWN_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        
        # Add this line to maintain compatibility with blueprint_to_markdown.py
        cls.VAULT_PATH = cls.MARKDOWN_OUTPUT_DIR
        
        logger.info(f"Initialized with transcript: {cls.TRANSCRIPTS_PATH}")
        logger.info(f"Output directories: {cls.CURRENT_VAULT_DIR}")
        
        return logger
