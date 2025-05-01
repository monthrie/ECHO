from flask import Flask, render_template, request, jsonify
from cli_agent import ChatAgent
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
agent = ChatAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    
    response = agent.get_web_response(user_input)
    return jsonify({'response': response})

@app.route('/clear', methods=['POST'])
def clear():
    agent.conversation = []
    return jsonify({'status': 'Conversation cleared'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True)