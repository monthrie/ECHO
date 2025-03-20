import os
import re
import uuid
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

# Configuration
class Config:
    # Path to Obsidian vault
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./sample_vault/")
    # Qdrant storage directory (for local persistence)
    QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_storage")
    # Collection name in Qdrant
    COLLECTION_NAME = "markdown_notes"
    # Embedding model name
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Smaller, faster model
    # EMBEDDING_MODEL = "all-mpnet-base-v2"  # More accurate but slower
    # Embedding dimension (depends on the model)
    EMBEDDING_DIM = 384  # for MiniLM-L6-v2
    # EMBEDDING_DIM = 768  # for mpnet-base-v2

# Main embedding service class
class MarkdownEmbeddingService:
    def __init__(self, config: Config = Config()):
        self.config = config
        self.vault_path = Path(config.OBSIDIAN_VAULT_PATH)
        
        # Initialize embedding model
        print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Initialize Qdrant client
        print(f"Initializing Qdrant client with storage at: {config.QDRANT_PATH}")
        self.qdrant = QdrantClient(path=config.QDRANT_PATH)
        
        # Ensure collection exists
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self):
        """Make sure the Qdrant collection exists, create it if it doesn't"""
        collections = self.qdrant.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.config.COLLECTION_NAME not in collection_names:
            print(f"Creating new collection: {self.config.COLLECTION_NAME}")
            self.qdrant.create_collection(
                collection_name=self.config.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.config.EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
        else:
            print(f"Collection {self.config.COLLECTION_NAME} already exists")
    
    def scan_vault(self) -> List[Path]:
        """Scan the vault for markdown files"""
        print(f"Scanning vault at: {self.vault_path}")
        md_files = list(self.vault_path.glob("**/*.md"))
        print(f"Found {len(md_files)} markdown files")
        return md_files
    
    def parse_markdown_file(self, file_path: Path) -> Tuple[str, Dict[str, Any], str]:
        """Parse a markdown file, extracting frontmatter, content, and ensuring an ID exists"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        frontmatter, body = self._extract_frontmatter(content)
        
        # Ensure ID exists in frontmatter
        if 'id' not in frontmatter:
            frontmatter['id'] = str(uuid.uuid4())
            
            # Write the updated frontmatter back to the file
            updated_content = self._update_frontmatter(content, frontmatter)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"Added ID to file: {file_path.relative_to(self.vault_path)}")
        
        return frontmatter['id'], frontmatter, body
    
    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter and content body from markdown"""
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        
        if frontmatter_match:
            frontmatter_yaml = frontmatter_match.group(1)
            try:
                frontmatter = yaml.safe_load(frontmatter_yaml) or {}
                content_body = content[frontmatter_match.end():]
                return frontmatter, content_body
            except yaml.YAMLError:
                return {}, content
        
        return {}, content
    
    def _update_frontmatter(self, original_content: str, frontmatter: Dict[str, Any]) -> str:
        """Update the frontmatter in a markdown file"""
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False)
        frontmatter_block = f"---\n{frontmatter_yaml}---\n"
        
        # Check if original content had frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', original_content, re.DOTALL)
        
        if frontmatter_match:
            # Replace existing frontmatter
            return frontmatter_block + original_content[frontmatter_match.end():]
        else:
            # Add new frontmatter
            return frontmatter_block + original_content
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def store_embedding(self, 
                        doc_id: str, 
                        embedding: List[float], 
                        file_path: Path, 
                        metadata: Dict[str, Any]):
        """Store an embedding in the Qdrant collection"""
        # Convert Path to string for storage
        relative_path = str(file_path.relative_to(self.vault_path))
        
        # Extract relevant metadata
        payload = {
            "path": relative_path,
            "title": metadata.get("title", relative_path),
            "tags": metadata.get("tags", []),
            "status": metadata.get("status", "unknown"),
            "para_type": self._determine_para_type(file_path),
            "last_modified": os.path.getmtime(file_path)
        }
        
        # Store in Qdrant
        self.qdrant.upsert(
            collection_name=self.config.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
    
    def _determine_para_type(self, file_path: Path) -> str:
        """Determine PARA type from file path"""
        path_parts = file_path.parts
        if len(path_parts) >= 2:
            if path_parts[0].lower() == 'projects':
                return 'project'
            elif path_parts[0].lower() == 'areas':
                return 'area'
            elif path_parts[0].lower() == 'resources':
                return 'resource'
            elif path_parts[0].lower() == 'archives':
                return 'archive'
        return 'unknown'
    
    def process_file(self, file_path: Path) -> str:
        """Process a single markdown file: parse, generate embedding, store"""
        try:
            # Parse file
            doc_id, frontmatter, content = self.parse_markdown_file(file_path)
            
            # Generate embedding from content
            embedding = self.generate_embedding(content)
            
            # Store in Qdrant
            self.store_embedding(doc_id, embedding, file_path, frontmatter)
            
            return doc_id
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return None
    
    def process_all_files(self):
        """Process all markdown files in the vault"""
        files = self.scan_vault()
        processed_count = 0
        
        for file_path in files:
            doc_id = self.process_file(file_path)
            if doc_id:
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count}/{len(files)} files...")
        
        print(f"Completed processing {processed_count}/{len(files)} files")
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for notes similar to the query"""
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)
        
        # Search in Qdrant
        search_results = self.qdrant.search(
            collection_name=self.config.COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit
        )
        
        # Format results
        results = []
        for result in search_results:
            # Load the file to get fresh content
            file_path = self.vault_path / result.payload["path"]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    _, _, content = self.parse_markdown_file(file_path)
                
                # Add to results
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "path": result.payload["path"],
                    "title": result.payload.get("title", "Untitled"),
                    "para_type": result.payload.get("para_type", "unknown"),
                    "tags": result.payload.get("tags", []),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                })
            except Exception as e:
                print(f"Error loading file {file_path}: {str(e)}")
        
        return results
    
    def search_by_category(self, para_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for notes by PARA category"""
        search_results = self.qdrant.scroll(
            collection_name=self.config.COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="para_type",
                        match=MatchValue(value=para_type)
                    )
                ]
            ),
            limit=limit
        )
        
        # Format results similar to search_similar
        results = []
        for result in search_results[0]:  # scroll returns (points, next_page_offset)
            results.append({
                "id": result.id,
                "path": result.payload["path"],
                "title": result.payload.get("title", "Untitled"),
                "tags": result.payload.get("tags", [])
            })
            
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedded notes"""
        # Get collection info
        collection_info = self.qdrant.get_collection(self.config.COLLECTION_NAME)
        
        # Count by PARA type
        para_counts = {
            "project": 0,
            "area": 0,
            "resource": 0,
            "archive": 0,
            "unknown": 0
        }
        
        # This is inefficient but works for now - in production we'd use a proper aggregation
        for para_type in para_counts.keys():
            results = self.qdrant.scroll(
                collection_name=self.config.COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="para_type",
                            match=MatchValue(value=para_type)
                        )
                    ]
                ),
                limit=1  # We just need count
            )
            para_counts[para_type] = len(results[0])
        
        return {
            "total_notes": collection_info.vectors_count,
            "para_counts": para_counts
        }
        
    def list_all_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all embeddings stored in the collection"""
        results = self.qdrant.scroll(
            collection_name=self.config.COLLECTION_NAME,
            limit=limit
        )
        
        embeddings = []
        for point in results[0]:  # scroll returns (points, next_page_offset)
            embeddings.append({
                "id": point.id,
                "path": point.payload.get("path", "Unknown"),
                "title": point.payload.get("title", "Untitled"),
                "para_type": point.payload.get("para_type", "unknown"),
                "tags": point.payload.get("tags", [])
            })
            
        return embeddings

def main():
    """Main function to run the embedding service"""
    service = MarkdownEmbeddingService()
    
    while True:
        print("\nMarkdown Embedding Service")
        print("1. Process all markdown files")
        print("2. Search for similar notes")
        print("3. Search by PARA category")
        print("4. Show statistics")
        print("5. List all embeddings")
        print("6. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            service.process_all_files()
        
        elif choice == "2":
            query = input("Enter your search query: ")
            results = service.search_similar(query)
            print("\nSearch Results:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} (Score: {result['score']:.2f})")
                print(f"   Path: {result['path']}")
                print(f"   Tags: {', '.join(result['tags'])}")
                print(f"   Preview: {result['content_preview'][:100]}...")
                print()
        
        elif choice == "3":
            print("PARA Categories: project, area, resource, archive")
            category = input("Enter PARA category to search: ")
            results = service.search_by_category(category)
            print(f"\n{category.capitalize()} Notes:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   Path: {result['path']}")
                print(f"   Tags: {', '.join(result['tags'])}")
                print()
        
        elif choice == "4":
            stats = service.get_stats()
            print("\nEmbedding Statistics:")
            print(f"Total Notes: {stats['total_notes']}")
            print("PARA Distribution:")
            for para_type, count in stats['para_counts'].items():
                print(f"  - {para_type.capitalize()}: {count}")
                
        elif choice == "5":
            limit = input("How many embeddings to list? (default: 100): ")
            try:
                limit = int(limit) if limit.strip() else 100
            except ValueError:
                limit = 100
                
            embeddings = service.list_all_embeddings(limit)
            if embeddings:
                print(f"\nFound {len(embeddings)} embeddings:")
                for i, emb in enumerate(embeddings, 1):
                    print(f"{i}. {emb['title']}")
                    print(f"   ID: {emb['id']}")
                    print(f"   Path: {emb['path']}")
                    print(f"   Type: {emb['para_type']}")
                    print()
            else:
                print("\nNo embeddings found in the collection.")
        
        elif choice == "6":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()