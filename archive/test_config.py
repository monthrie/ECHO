"""
Test script to verify the centralized configuration is working correctly.
"""
import os
from pathlib import Path
from archive.config import Config

def test_config():
    """Test the configuration initialization and settings."""
    print("=== Testing Configuration ===")
    
    # Initialize the configuration
    print("Initializing configuration...")
    Config.initialize()
    
    # Get a logger
    logger = Config.setup_logging()
    logger.info("Logger initialized successfully")
    
    # Test critical paths
    print("\n=== Testing Critical Paths ===")
    paths_to_check = [
        ("DB_PATH", Config.DB_PATH),
        ("OBSIDIAN_VAULT_PATH", Config.OBSIDIAN_VAULT_PATH),
        ("JSON_OUTPUT_DIR", Config.JSON_OUTPUT_DIR),
        ("QDRANT_PATH", Config.QDRANT_PATH)
    ]
    
    for name, path in paths_to_check:
        path_obj = Path(path)
        exists = path_obj.exists()
        print(f"{name}: {path} {'✅ exists' if exists else '❌ does not exist'}")
    
    # Test API key
    print("\n=== Testing API Configuration ===")
    api_key = Config.OPENROUTER_API_KEY
    if api_key:
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        print(f"OPENROUTER_API_KEY: {masked_key} ✅")
    else:
        print("OPENROUTER_API_KEY: ❌ Not found")
    
    print(f"MODEL: {Config.MODEL}")
    
    # Test embedding configuration
    print("\n=== Testing Embedding Configuration ===")
    print(f"EMBEDDING_MODEL: {Config.EMBEDDING_MODEL}")
    print(f"EMBEDDING_DIM: {Config.EMBEDDING_DIM}")
    print(f"COLLECTION_NAME: {Config.COLLECTION_NAME}")
    
    print("\n=== Configuration Test Complete ===")
    return True

if __name__ == "__main__":
    test_config() 