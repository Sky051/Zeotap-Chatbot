from flask import Flask, request, jsonify, render_template
from chatbot import Chatbot
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
chatbot = Chatbot()

@app.route('/')
def home():
    """Render the main chat interface"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Handle chatbot questions and return answers"""
    try:
        user_question = request.json.get('question')
        if not user_question:
            return jsonify({'error': 'No question provided'}), 400

        logger.info(f"Received question: {user_question}")
        
        # Get answer from chatbot
        response = chatbot.get_answer(user_question)
        
        # Format the answer for display
        formatted_answer = format_answer(response)
        
        logger.info(f"Generated response for question: {user_question}")
        return jsonify({'answer': formatted_answer})

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'An error occurred while processing your question'
        }), 500

def format_answer(response: dict) -> str:
    """Format the chatbot response for display"""
    if not response:
        return "I'm sorry, I couldn't find an answer to your question. Please try rephrasing it."

    # Start with the main answer content
    formatted_answer = response.get('answer', '')

    # Add source URL if available
    source_url = response.get('source_url')
    if source_url:
        formatted_answer += f"\n\nSource: <a href='{source_url}' target='_blank'>Documentation</a>"

    # Add code examples if available
    code_examples = response.get('code_examples', [])
    if code_examples:
        formatted_answer += "\n\nCode Examples:\n"
        for i, example in enumerate(code_examples, 1):
            formatted_answer += f"\nExample {i}:\n<pre><code>{example}</code></pre>"

    # Add API details if available
    api_details = response.get('api_details', {})
    if api_details:
        formatted_answer += "\n\nAPI Details:\n"
        if 'method' in api_details and 'endpoint' in api_details:
            formatted_answer += f"\nEndpoint: {api_details['method']} {api_details['endpoint']}"
        if 'request_example' in api_details:
            formatted_answer += f"\nRequest Example:\n<pre><code>{api_details['request_example']}</code></pre>"
        if 'response_example' in api_details:
            formatted_answer += f"\nResponse Example:\n<pre><code>{api_details['response_example']}</code></pre>"

    return formatted_answer

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
