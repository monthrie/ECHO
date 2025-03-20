import csv
import uuid
from datetime import datetime, timedelta

def create_sample_transcripts(filename="transcripts.csv"):
    """Create a sample CSV file with example transcripts."""
    
    # Sample transcript data
    sample_transcripts = [
        {
            'transcript_id': str(uuid.uuid4()),
            'user_id': 'user_123',
            'timestamp': datetime.now().isoformat(),
            'source': 'meeting_notes',
            'content': """Today I had an idea about building an AI-powered knowledge management system. 
                         I also need to follow up on that research request about open-source models. 
                         Maybe add a reminder for tomorrow to review the notes."""
        },
        {
            'transcript_id': str(uuid.uuid4()),
            'user_id': 'user_123',
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
            'source': 'voice_memo',
            'content': """Need to research the following topics for the project:
                         1. Vector databases for semantic search
                         2. RAG architectures for LLMs
                         3. Obsidian API documentation"""
        },
        {
            'transcript_id': str(uuid.uuid4()),
            'user_id': 'user_123',
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'source': 'journal',
            'content': """Key insights from today's reading on knowledge management:
                         - Information should be atomic
                         - Links between notes are as important as the notes themselves
                         - Regular review is crucial for learning
                         TODO: Implement these principles in our system"""
        }
    ]
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['transcript_id', 'user_id', 'timestamp', 'source', 'content']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for transcript in sample_transcripts:
            writer.writerow(transcript)
    
    print(f"Sample CSV created at {filename}")
    print(f"Created {len(sample_transcripts)} sample transcripts")

if __name__ == "__main__":
    create_sample_transcripts() 