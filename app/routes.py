from flask import Blueprint, jsonify, send_from_directory, current_app, request, jsonify
import os
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API blueprint
api = Blueprint('api', __name__)

@api.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'environment': current_app.config.get('ENV', 'development'),
            'debug': current_app.debug,
            'version': '1.0.0',
            'service': 'CaseStrainer API',
            'timestamp': '2025-06-08T12:00:00Z'  # This will be dynamic in a real app
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'service': 'CaseStrainer API',
            'timestamp': '2025-06-08T12:00:00Z'  # This will be dynamic in a real app
        }), 500

@api.route('/analyze-document', methods=['POST'])
def analyze_document():
    """
    Handle document upload and analysis
    """
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
        
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            logger.info(f'Processing file: {filename}')
            
            # Here you would typically process the file
            # For now, we'll just return a mock response
            return jsonify({
                'status': 'success',
                'filename': filename,
                'message': 'File uploaded successfully',
                'citations': [
                    {'text': 'Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)', 'valid': True},
                    {'text': 'Doe v. Roe, 987 F.2d 654 (2d Cir. 2019)', 'valid': False}
                ]
            })
    
    except Exception as e:
        logger.error(f'Error processing file: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

# Add more API routes here

# Frontend routes
frontend = Blueprint('frontend', __name__)

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
