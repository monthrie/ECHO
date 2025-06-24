# Second Brain AI

> _"I got tired of shoehorning AI into note-taking apps that don't care about privacy or real customization. So I decided to build my own AI-powered second brain—one that's private, hackable, and actually works the way I want. It's a work in progress, but it's already way more fun than sending all of my notes off to OpenAI and Anthropic. We need privacy with our AI otherwise we will lose everything."_

---

## Features at a Glance
- **PARA Methodology**: Projects, Areas, Resources, Archives—structured for clarity
- **AI-Powered Organization**: Synthesizes, links, and categorizes your notes
- **Local-First & Private**: Your data, your machine, your rules
- **Agent System**: Modular AI agents for curation, research, synthesis, and more (coming soon)
- **Vector Embeddings**: Semantic, conceptual, and temporal search (WIP)
- **Flexible Ingestion**: Text now, multi-modal (PDF, voice, code, web) soon

---

## Why Not Just Use X?
Most note-taking apps bolt on AI as an afterthought, or worse, send your data to the cloud. I wanted:
- **Real privacy** (local-first, no forced cloud sync)
- **Bespoke workflows** (not just a chat box in a sidebar)
- **Hackability** (open code, modular agents, real extensibility)
- **A system that grows with me**

If you've ever felt boxed in by Notion, or the latest AI plugin, you'll get why this exists.

---

## Why I Like Obsidian
Obsidian is the backbone of this project for a reason: it lets you keep your notes in plain Markdown files, stored locally, with zero vendor lock-in. Its plugin ecosystem and local-first philosophy are pretty tasty in a world of cloud silos. This project is about supercharging your Obsidian vault with AI—while keeping everything private, extensible, and hackable.

---

## Overview
Second Brain AI is an evolving, intelligent knowledge system. It doesn't just store your notes—it actively helps you organize, connect, and synthesize them. Inspired by the PARA method, it's designed for:
- **Active Knowledge Management**: The system processes and links your info, not just files it away
- **Autonomous Agents**: Specialized AI agents work alongside you (and each other)
- **Emergent Insights**: Surfaces non-obvious connections and new ideas
- **Adaptive Structure**: The knowledge base evolves as you use it
- **Research Partnership**: Like a research assistant that actually helps

---

## Architecture (Current & Future)

### Current POC
- **Data Ingestion**: Text-based, structured into PARA
- **SQLite Storage**: Local, simple, and private
- **Basic Processing**: Text structuring, metadata extraction, PARA categorization, basic linking

#### Example Schema
```json
{
  "session": { ... },
  "records": [
    {
      "record_id": "<UUID>",
      "para_type": "project|area|resource|archive",
      "type": "idea|task|quote|...",
      "content": "<synthesized note>",
      ...
    }
  ]
}
```

### Future (WIP)
- **Multi-Modal Ingestion**: PDFs, voice, images, code, web
- **Vector Storage**: Multiple embedding spaces (semantic, concept, temporal)
- **Agent System**: Curator, Researcher, Synthesizer, Planner, Reviewer
- **Knowledge Graph**: Concept mapping, relationship inference, dynamic restructuring
- **Interface Layer**: Web, CLI, API, Obsidian plugin

---

## Technical Implementation

### Embedding System
```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

class EmbeddingSystem:
    def __init__(self):
        self.semantic_model = SentenceTransformer('all-mpnet-base-v2')
        self.concept_model = SentenceTransformer('sentence-t5-xl')
        self.vector_db = QdrantClient("localhost", port=6333)
    def create_embeddings(self, text, embedding_type="semantic"):
        if embedding_type == "semantic":
            return self.semantic_model.encode(text)
        return self.concept_model.encode(text)
```

### Agent Framework
```python
class BaseAgent:
    def __init__(self, knowledge_base, embedding_system):
        self.kb = knowledge_base
        self.embeddings = embedding_system
        self.memory = ConversationBufferMemory()
    async def run_cycle(self):
        relevant_context = self.get_context()
        thoughts = self.analyze(relevant_context)
        actions = self.plan_actions(thoughts)
        await self.execute_actions(actions)
```

---

## Getting Started
1. Clone the repo
2. `pip install -r requirements.txt`
3. Set up environment variables
4. Initialize the DB: `python init_db.py`
5. Run: `python main.py`

---

## Status / What's Next?
- **Current**: PARA structure, text processing, local DB, basic API
- **Next Up**: Vector embeddings, first agent prototypes, better linking
- **On the Horizon**: Multi-agent system, knowledge graph, UI/UX

_This is a work in progress. If you're interested in hacking, collaborating, or just want to see where this goes—PRs and ideas welcome!_

---

## Roadmap
- [x] Basic PARA implementation
- [x] Simple text processing
- [x] Initial database structure
- [x] Basic API integration
- [ ] Vector embedding integration
- [ ] Basic agent implementation
- [ ] Enhanced metadata extraction
- [ ] Improved linking system
- [ ] Multi-agent system
- [ ] Advanced research capabilities
- [ ] Knowledge graph implementation
- [ ] UI/UX development
- [ ] Autonomous research
- [ ] Predictive insights
- [ ] Collaborative features
- [ ] API ecosystem

---

## License
MIT
