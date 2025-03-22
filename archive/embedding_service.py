import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional
from markdown_embedder import MarkdownEmbeddingService
from config import Config

# Set up logging
logger = Config.setup_logging()

class AutomaticEmbeddingService:
    def __init__(self, config: Config = Config()):
        self.config = config
        self.embedding_service = MarkdownEmbeddingService(config)
        self.file_timestamps: Dict[Path, float] = {}
        self.last_scan_time = 0
        
    def scan_for_changes(self) -> Set[Path]:
        """Scan vault for changed or new files since last scan"""
        changed_files = set()
        all_files = self.embedding_service.scan_vault()
        
        for file_path in all_files:
            # Get last modified time
            mod_time = os.path.getmtime(file_path)
            
            # Check if file is new or modified
            if file_path not in self.file_timestamps or mod_time > self.file_timestamps[file_path]:
                changed_files.add(file_path)
                self.file_timestamps[file_path] = mod_time
        
        # Check for deleted files
        current_files = set(all_files)
        known_files = set(self.file_timestamps.keys())
        deleted_files = known_files - current_files
        
        # Remove deleted files from our tracking
        for file_path in deleted_files:
            logger.info(f"File deleted: {file_path}")
            del self.file_timestamps[file_path]
            # TODO: Implement removal from vector database
        
        return changed_files
    
    def process_changed_files(self, files: Set[Path]) -> int:
        """Process all changed files"""
        processed_count = 0
        
        for file_path in files:
            try:
                logger.info(f"Processing changed file: {file_path}")
                doc_id = self.embedding_service.process_file(file_path)
                if doc_id:
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
        
        return processed_count
    
    def run_once(self) -> int:
        """Run a single scan and process cycle"""
        logger.info("Starting scan for changes...")
        changed_files = self.scan_for_changes()
        
        if changed_files:
            logger.info(f"Found {len(changed_files)} changed files")
            processed_count = self.process_changed_files(changed_files)
            logger.info(f"Processed {processed_count} files")
            return processed_count
        else:
            logger.info("No changes detected")
            return 0
    
    def run_service(self, interval_seconds: int = 300):
        """Run the service continuously with a specified interval"""
        logger.info(f"Starting automatic embedding service with {interval_seconds}s interval")
        
        try:
            while True:
                start_time = time.time()
                processed = self.run_once()
                
                # Calculate sleep time (accounting for processing time)
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                
                if processed > 0:
                    logger.info(f"Processed {processed} files. Next scan in {sleep_time:.1f}s")
                else:
                    logger.info(f"No changes. Next scan in {sleep_time:.1f}s")
                
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Service error: {str(e)}")
            raise

    def remove_embedding(self, doc_id: str):
        """Remove an embedding from the Qdrant collection"""
        try:
            self.embedding_service.qdrant.delete(
                collection_name=self.config.COLLECTION_NAME,
                points_selector=[doc_id]
            )
            print(f"Removed embedding with ID: {doc_id}")
            return True
        except Exception as e:
            print(f"Error removing embedding: {str(e)}")
            return False

def main():
    """Main function to run the automatic embedding service"""
    print("Automatic Markdown Embedding Service")
    print("====================================")
    
    # Get interval from user or use default
    interval_input = input("Enter scan interval in seconds (default: 300): ")
    try:
        interval = int(interval_input) if interval_input.strip() else 300
    except ValueError:
        print("Invalid input, using default 300 seconds")
        interval = 300
    
    # Create and run service
    service = AutomaticEmbeddingService()
    
    # Initial scan to build the timestamp database
    print("Performing initial scan...")
    service.run_once()
    
    # Run continuous service
    print(f"Starting continuous service with {interval}s interval")
    print("Press Ctrl+C to stop")
    service.run_service(interval)

if __name__ == "__main__":
    main()
