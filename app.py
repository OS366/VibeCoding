from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import openai
import logging
import httpx
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable debug mode
app.config['DEBUG'] = True

# Get OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    app.logger.error("No OpenAI API key found in environment variables!")

@app.route('/')
def index():
    app.logger.debug("Index route accessed")
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    app.logger.debug("Analyze route accessed")
    app.logger.debug(f"Request headers: {request.headers}")
    
    # Get text from request
    text = request.json.get('text', '')
    app.logger.debug(f"Received text: {text[:50]}...")
    
    if not text:
        app.logger.warning("No text provided")
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Determine urgency and concept type based on text content
        urgency_level = determine_urgency(text)
        concept_type = determine_concept_type(text)
        
        # Create a dummy response for testing
        app.logger.debug("Creating dummy response for testing")
        dummy_analysis = f"""
        {{
            "grammatical_errors": [
                {{
                    "error": "Incorrect word usage",
                    "suggestion": "Consider using more precise language"
                }}
            ],
            "tone": "Informal",
            "formality_level": "Casual",
            "urgency_level": "{urgency_level}",
            "concept_type": "{concept_type}",
            "improvement_suggestions": [
                "Add more structure to your sentences",
                "Consider using more professional terminology"
            ]
        }}
        """
        
        app.logger.debug("Returning dummy analysis")
        return jsonify({'analysis': dummy_analysis})
        
        # NOTE: The OpenAI API call is commented out due to the proxies error
        # We'll use a dummy response instead for now
        """
        # Create a custom HTTP transport without proxies
        app.logger.debug("Creating HTTP transport without proxies")
        transport = httpx.HTTPTransport(local_address="0.0.0.0")
        http_client = httpx.Client(transport=transport, timeout=60.0)
        
        app.logger.debug("Initializing OpenAI client")
        client = openai.OpenAI(
            api_key=api_key,
            http_client=http_client
        )
        
        app.logger.debug("Calling OpenAI API")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes text for grammatical errors, tone, urgency level, and other language aspects. Provide your analysis in JSON format with the following structure: {grammatical_errors: [{error: string, suggestion: string}], tone: string, formality_level: string, urgency_level: string, concept_type: string, improvement_suggestions: [string]}. For urgency_level, use one of: 'High', 'Medium', 'Low'. For concept_type, use one of: 'Idea', 'Question', 'Problem', 'Request', 'Information'."},
                {"role": "user", "content": f"Analyze the following text: {text}"}
            ]
        )
        
        # Extract analysis from the response
        analysis = response.choices[0].message.content
        app.logger.debug(f"Analysis received from OpenAI")
        
        return jsonify({'analysis': analysis})
        """
    
    except Exception as e:
        app.logger.error(f"Error during analysis: {str(e)}")
        app.logger.error(f"Error type: {type(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

def determine_urgency(text):
    """Determine the urgency level based on text content."""
    text = text.lower()
    
    # High urgency keywords
    if any(word in text for word in ['urgent', 'immediately', 'asap', 'emergency', 'critical', 'crucial']):
        return "High"
    
    # Medium urgency keywords
    elif any(word in text for word in ['important', 'soon', 'timely', 'priority', 'attention']):
        return "Medium"
    
    # Default to low urgency
    else:
        return "Low"

def determine_concept_type(text):
    """Determine the concept type based on text content."""
    text = text.lower()
    
    # Check for idea patterns
    if any(word in text for word in ['idea', 'concept', 'thought', 'imagine', 'consider', 'what if', 'how about']):
        return "Idea"
    
    # Check for question patterns
    elif '?' in text or any(word in text for word in ['who', 'what', 'when', 'where', 'why', 'how']):
        return "Question"
    
    # Check for problem patterns
    elif any(word in text for word in ['problem', 'issue', 'error', 'bug', 'fix', 'trouble', 'help']):
        return "Problem"
    
    # Check for request patterns
    elif any(word in text for word in ['please', 'could you', 'would you', 'request', 'need']):
        return "Request"
    
    # Default to information
    else:
        return "Information"

@app.after_request
def add_headers(response):
    """Add headers to allow cross-origin requests."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

if __name__ == '__main__':
    # Allow connections from any IP
    # Changing port to avoid conflicts
    app.run(debug=True, host='0.0.0.0', port=5003) 