#!/usr/bin/env python3
"""
A lightweight Flask wrapper for your existing note_rag functionality.
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
from pathlib import Path

# Add parent directory to path to access Config
sys.path.append(str(Path(__file__).parent.parent))
from utils.config import Config

# Initialize Config
Config.initialize()

# Import your existing functions - use relative import with the full path
sys.path.append(str(Path(__file__).parent))
from note_rag import create_note_embeddings, find_relevant_notes, query_llm

app = Flask(__name__)
NOTE_EMBEDDINGS = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    global NOTE_EMBEDDINGS
    
    # Load embeddings if not already loaded
    if NOTE_EMBEDDINGS is None:
        NOTE_EMBEDDINGS = create_note_embeddings()
        if not NOTE_EMBEDDINGS:
            return jsonify({"success": False, "message": "No embeddings available"})
    
    # Get query from request
    query = request.json.get('query', '')
    if not query.strip():
        return jsonify({"success": False, "message": "Query cannot be empty"})
    
    # Find relevant notes
    relevant_notes = find_relevant_notes(query, NOTE_EMBEDDINGS)
    if not relevant_notes:
        return jsonify({"success": False, "message": "No relevant notes found"})
    
    # Format notes for display
    formatted_notes = [
        {
            'number': i+1,
            'filepath': note['filepath'],
            'relevance': note['relevance'],
            'preview': note['preview']
        }
        for i, note in enumerate(relevant_notes)
    ]
    
    # Get LLM response
    response = query_llm(query, relevant_notes)
    
    return jsonify({
        "success": True,
        "notes": formatted_notes,
        "response": response
    })

@app.route('/rebuild', methods=['POST'])
def rebuild_embeddings():
    global NOTE_EMBEDDINGS
    
    try:
        NOTE_EMBEDDINGS = create_note_embeddings(force_rebuild=True)
        return jsonify({
            "success": True,
            "message": f"Embeddings rebuilt successfully. Created {len(NOTE_EMBEDDINGS)} embeddings."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error rebuilding embeddings: {str(e)}"
        })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Create index.html if it doesn't exist
    index_path = templates_dir / 'index.html'
    if not index_path.exists():
        with open(index_path, 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note RAG</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
            color: #333;
        }
        .container {
            display: flex;
            gap: 20px;
            height: calc(100vh - 100px);
        }
        .chat-panel {
            flex: 2;
            display: flex;
            flex-direction: column;
        }
        .notes-panel {
            flex: 1;
            border-left: 1px solid #ddd;
            padding-left: 20px;
            overflow-y: auto;
        }
        .chat-history {
            flex-grow: 1;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        }
        .input-area {
            display: flex;
            margin-bottom: 10px;
        }
        .query-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        button {
            padding: 10px 15px;
            margin-left: 10px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
        }
        .rebuild-button {
            background-color: #2ecc71;
        }
        button:hover {
            opacity: 0.9;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background-color: #d1f3ff;
            margin-left: 20px;
            border-radius: 10px 10px 0 10px;
        }
        .assistant-message {
            background-color: #e8f5e9;
            margin-right: 20px;
            border-radius: 10px 10px 10px 0;
        }
        .note-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #fff;
        }
        .note-title {
            font-weight: bold;
        }
        .note-preview {
            font-size: 0.9em;
            margin-top: 5px;
            max-height: 100px;
            overflow-y: auto;
            white-space: pre-line;
        }
        .thinking {
            color: #7f8c8d;
            font-style: italic;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        pre {
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>Personal Note RAG</h1>
    
    <div class="container">
        <div class="chat-panel">
            <div class="chat-history" id="chatHistory"></div>
            <div class="input-area">
                <input type="text" class="query-input" id="queryInput" placeholder="Ask a question about your notes...">
                <button id="sendButton">Send</button>
                <button class="rebuild-button" id="rebuildButton">Rebuild Embeddings</button>
            </div>
        </div>
        <div class="notes-panel">
            <h3>Relevant Notes</h3>
            <div id="notesList"></div>
        </div>
    </div>

    <script>
        // DOM elements
        const chatHistory = document.getElementById('chatHistory');
        const queryInput = document.getElementById('queryInput');
        const sendButton = document.getElementById('sendButton');
        const rebuildButton = document.getElementById('rebuildButton');
        const notesList = document.getElementById('notesList');

        // Debug check if elements are found
        console.log('Chat history element found:', !!chatHistory);
        console.log('Query input element found:', !!queryInput);
        console.log('Send button element found:', !!sendButton);
        console.log('Rebuild button element found:', !!rebuildButton);
        console.log('Notes list element found:', !!notesList);

        // Add a message to the chat
        function addMessage(content, isUser = false) {
            console.log('Adding message:', content.substring(0, 50) + '...');
            const message = document.createElement('div');
            message.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
            message.innerHTML = content;
            chatHistory.appendChild(message);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        // Display relevant notes
        function displayNotes(notes) {
            console.log('Displaying notes:', notes.length);
            notesList.innerHTML = '';
            notes.forEach(note => {
                const noteCard = document.createElement('div');
                noteCard.className = 'note-card';
                noteCard.innerHTML = `
                    <div class="note-title">Note ${note.number}: ${note.filepath}</div>
                    <div>Relevance: ${note.relevance}</div>
                    <div class="note-preview">${note.preview}</div>
                `;
                notesList.appendChild(noteCard);
            });
        }

        // Send query to the backend
        async function sendQuery(query) {
            console.log('Sending query:', query);
            
            // Add user message
            addMessage(query, true);
            
            // Clear input
            queryInput.value = '';
            
            // Show thinking message
            const thinkingId = 'thinking-' + Date.now();
            addMessage(`<div id="${thinkingId}" class="thinking">Thinking...</div>`);
            
            try {
                console.log('Fetching from /query endpoint...');
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query }),
                });
                
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
                
                // Remove thinking message
                const thinkingElement = document.getElementById(thinkingId);
                if (thinkingElement) thinkingElement.remove();
                
                if (data.success) {
                    // Format response text
                    let formattedResponse = data.response
                        .replace(/```[\s\S]*?```/g, (match) => {
                            // Extract code between backticks
                            const code = match.slice(3, -3);
                            return `<pre><code>${code}</code></pre>`;
                        })
                        .replace(/`([^`]+)`/g, (match, p1) => `<code>${p1}</code>`)
                        .replace(/\n/g, '<br>');
                    
                    // Add assistant message
                    addMessage(formattedResponse);
                    
                    // Display notes
                    displayNotes(data.notes);
                } else {
                    // Show error
                    addMessage(`Error: ${data.message}`);
                }
            } catch (error) {
                console.error('Error:', error);
                
                // Remove thinking message
                const thinkingElement = document.getElementById(thinkingId);
                if (thinkingElement) thinkingElement.remove();
                
                addMessage('An error occurred. Please try again.');
            }
        }

        // Rebuild embeddings
        async function rebuildEmbeddings() {
            console.log('Rebuilding embeddings...');
            rebuildButton.disabled = true;
            rebuildButton.textContent = 'Rebuilding...';
            
            try {
                const response = await fetch('/rebuild', {
                    method: 'POST',
                });
                
                const data = await response.json();
                console.log('Rebuild response:', data);
                
                if (data.success) {
                    addMessage(`System: ${data.message}`);
                } else {
                    addMessage(`Error: ${data.message}`);
                }
            } catch (error) {
                console.error('Error:', error);
                addMessage('An error occurred while rebuilding embeddings.');
            } finally {
                rebuildButton.disabled = false;
                rebuildButton.textContent = 'Rebuild Embeddings';
            }
        }

        // Event listeners
        console.log('Setting up event listeners...');
        sendButton.addEventListener('click', () => {
            console.log('Send button clicked');
            const query = queryInput.value.trim();
            if (query) {
                console.log('Query is not empty, sending...');
                sendQuery(query);
            } else {
                console.log('Query is empty, not sending');
            }
        });
        
        queryInput.addEventListener('keypress', (e) => {
            console.log('Key pressed:', e.key);
            if (e.key === 'Enter') {
                const query = queryInput.value.trim();
                if (query) sendQuery(query);
            }
        });
        
        rebuildButton.addEventListener('click', rebuildEmbeddings);

        // Initial message
        console.log('Adding welcome message...');
        addMessage('Welcome to your personal notes RAG system! Ask me anything about your notes.');
    </script>
</body>
</html>''')
    
    # Run the Flask app
    app.run(debug=True)