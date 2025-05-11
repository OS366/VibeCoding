from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from dotenv import load_dotenv, set_key
import openai
import logging
import json
import httpx

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)

# Enable debug mode
app.config['DEBUG'] = True

# Clear any proxy environment variables that might be causing issues
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

def get_api_key():
    """Get the OpenAI API key from .env file."""
    # Reload the .env file to get the latest changes
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        app.logger.warning("No valid API key found in .env file")
        return None
    else:
        masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "Invalid key format"
        app.logger.debug(f"Using API key from .env: {masked_key}")
        return api_key

def save_api_key(new_key):
    """Save the API key to .env file."""
    try:
        # Check if .env file exists
        if not os.path.exists('.env'):
            # Create the file
            with open('.env', 'w') as f:
                f.write(f"OPENAI_API_KEY={new_key}\n")
        else:
            # Use python-dotenv's set_key function
            set_key('.env', 'OPENAI_API_KEY', new_key)
            
        app.logger.debug("API key saved to .env file")
        return True
    except Exception as e:
        app.logger.error(f"Failed to save API key to .env file: {str(e)}")
        return False

@app.route('/')
def index():
    app.logger.debug("Index route accessed")
    api_key = get_api_key()
    
    if not api_key:
        app.logger.warning("Redirecting to setup page")
        return render_template('setup.html')
    else:
        return render_template('index.html')

@app.route('/set-api-key', methods=['POST'])
def set_api_key():
    new_api_key = request.form.get('api_key')
    if new_api_key and new_api_key.strip():
        new_api_key = new_api_key.strip()
        
        # Save to .env file
        if save_api_key(new_api_key):
            app.logger.debug("API key updated and saved to .env file")
        else:
            app.logger.error("Failed to save API key")
            return "Failed to save API key", 500
            
        return redirect(url_for('index'))
    else:
        return "API key cannot be empty", 400

@app.route('/analyze', methods=['POST'])
def analyze():
    app.logger.debug("Analyze route accessed")
    app.logger.debug(f"Request headers: {request.headers}")
    
    # Get API key from .env
    api_key = get_api_key()
    if not api_key:
        return jsonify({'error': 'No valid OpenAI API key found in .env file. Please set your API key.'}), 401
    
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
        
        app.logger.debug("Setting up direct API call")
        # Make a direct API call without using the OpenAI client library
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes text and returns results in JSON format."},
                {"role": "user", "content": f"""
                Please analyze the following text and provide your analysis in valid JSON format with the following structure:
                {{
                  "grammatical_errors": [
                    {{
                      "error": "description of the error",
                      "suggestion": "suggestion to fix the error"
                    }}
                  ],
                  "tone": "description of the tone (e.g. formal, friendly, technical)",
                  "formality_level": "description of the formality level (e.g. formal, casual)",
                  "improvement_suggestions": [
                    "suggestion 1",
                    "suggestion 2"
                  ]
                }}

                The text to analyze is: {text}
                
                Ensure the response is a valid JSON object and nothing else.
                """}
            ]
        }
        
        # Create a client with no proxy configuration
        client = httpx.Client(timeout=60.0)
        
        masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "Invalid key format"
        app.logger.debug(f"Making API request with key: {masked_key}")
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes
        
        response_data = response.json()
        app.logger.debug(f"Response status code: {response.status_code}")
        
        # Extract analysis from the response
        analysis_json = response_data["choices"][0]["message"]["content"]
        app.logger.debug(f"Analysis received from OpenAI: {analysis_json[:100]}...")
        
        # Parse the JSON to validate it
        analysis = json.loads(analysis_json)
        
        # Add our detected urgency and concept type to the analysis
        analysis["urgency_level"] = urgency_level
        analysis["concept_type"] = concept_type
        
        # Convert back to JSON string
        final_analysis = json.dumps(analysis)
        
        return jsonify({'analysis': final_analysis})
    
    except Exception as e:
        app.logger.error(f"Error during analysis: {str(e)}")
        app.logger.error(f"Error type: {type(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Fallback to dummy analysis in case of API error
        app.logger.warning("Falling back to dummy analysis due to API error")
        dummy_analysis = f"""
        {{
            "grammatical_errors": [
                {{
                    "error": "API Error - Couldn't analyze",
                    "suggestion": "Please try again later"
                }}
            ],
            "tone": "Unknown (API Error)",
            "formality_level": "Unknown (API Error)",
            "urgency_level": "{urgency_level}",
            "concept_type": "{concept_type}",
            "improvement_suggestions": [
                "Unable to provide suggestions due to API error: {str(e)}"
            ]
        }}
        """
        return jsonify({'analysis': dummy_analysis, 'error': str(e)}), 500

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