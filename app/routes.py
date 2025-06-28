from flask import Blueprint, jsonify, send_from_directory, current_app, request, jsonify, make_response
import os
from werkzeug.utils import secure_filename
import logging
import sys
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from citation_extractor import CitationExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add Flask after_request handler to log all JSON responses
def log_json_responses(response):
    """
    Flask after_request handler to log all JSON responses before they are sent to the frontend.
    This ensures we capture all JSON output regardless of which endpoint generates it.
    """
    try:
        # Only log JSON responses
        if response.content_type == 'application/json':
            # Get the response data
            response_data = response.get_data(as_text=True)
            
            # Try to parse and pretty-print the JSON for better logging
            try:
                import json
                parsed_data = json.loads(response_data)
                formatted_json = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                
                # Log the response with context
                logger.info("=" * 80)
                logger.info("JSON RESPONSE BEING SENT TO FRONTEND (APP ROUTES)")
                logger.info("=" * 80)
                logger.info(f"Endpoint: {request.endpoint}")
                logger.info(f"Method: {request.method}")
                logger.info(f"URL: {request.url}")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(f"Content-Type: {response.content_type}")
                logger.info(f"Response Size: {len(response_data)} characters")
                logger.info("-" * 80)
                logger.info("RESPONSE BODY:")
                logger.info(formatted_json)
                logger.info("=" * 80)
                
            except json.JSONDecodeError:
                # If JSON parsing fails, log the raw response
                logger.warning("Failed to parse JSON response, logging raw data:")
                logger.info(f"Raw response: {response_data}")
                
        return response
        
    except Exception as e:
        logger.error(f"Error in log_json_responses: {str(e)}")
        return response

# Create API blueprint
api = Blueprint('api', __name__)

# Register the after_request handler to log all JSON responses
api.after_request(log_json_responses)

@api.route('/analyze-document', methods=['POST'])
def analyze_document():
    """
    Deprecated: Forwards file upload to /analyze endpoint. Use /analyze instead.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request', 'deprecated': True, 'message': 'This endpoint is deprecated. Please use /analyze.'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file', 'deprecated': True, 'message': 'This endpoint is deprecated. Please use /analyze.'}), 400
        # Forward the file to /analyze as multipart/form-data
        file.seek(0)
        files = {'file': (file.filename, file.stream, file.mimetype)}
        # Forward any additional form data if needed
        data = dict(request.form)
        # Build the internal URL (assume same host, port)
        analyze_url = request.url_root.rstrip('/') + '/analyze'
        # Forward the request
        resp = requests.post(analyze_url, files=files, data=data, headers={"X-Forwarded-For": "internal-analyze-document"})
        # Return the response from /analyze, with a deprecation warning
        response_json = resp.json()
        response_json['deprecated'] = True
        response_json['message'] = 'This endpoint is deprecated. Please use /analyze.'
        return make_response(jsonify(response_json), resp.status_code)
    except Exception as e:
        return jsonify({'error': str(e), 'deprecated': True, 'message': 'This endpoint is deprecated. Please use /analyze.'}), 500

# Add more API routes here

# Frontend routes
frontend = Blueprint('frontend', __name__)

# Register the after_request handler to log all JSON responses
frontend.after_request(log_json_responses)

@frontend.route('/')
def index():
    """Serve the main Vue.js application"""
    return send_from_directory(current_app.static_folder, 'index.html')

@frontend.route('/<path:path>')
def serve_static(path):
    """Serve static files from the Vue.js build"""
    if path != "" and os.path.exists(os.path.join(current_app.static_folder, path)):
        return send_from_directory(current_app.static_folder, path)
    return send_from_directory(current_app.static_folder, 'index.html')
