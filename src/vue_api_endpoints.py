"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
import sys
import uuid
import logging
import traceback
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the citation service using absolute imports
from src.api.services.citation_service import CitationService

logger = logging.getLogger(__name__)

# Create the blueprint with explicit name and import name
vue_api = Blueprint('vue_api', __name__)

# Initialize citation service
citation_service = CitationService()


@vue_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Vue API is running',
        'timestamp': datetime.utcnow().isoformat()
    })


@vue_api.route('/analyze', methods=['POST'])
def analyze_text():
    """
    Analyze text for citations.
    
    Expected JSON payload:
    {
        "text": "text to analyze",
        "type": "text"
    }
    
    Or form data with:
    - text: text to analyze
    - type: "text"
    
    Returns:
        JSON response with citation analysis results
    """
    # Log the start of the request
    request_id = str(uuid.uuid4())
    logger.info(f"[Request {request_id}] Starting analyze request")
    logger.info(f"[Request {request_id}] Content-Type: {request.content_type}")
    
    try:
        # Get request data - handle both JSON and form data
        data = None
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            # Handle form data
            text_content = request.form.get('text', '')
            if text_content is None:
                text_content = ''
            data = {
                'text': text_content,
                'type': request.form.get('type', 'text')
            }
        
        if not data or 'text' not in data or not data['text']:
            return jsonify({
                'error': 'Missing or invalid request data',
                'request_id': request_id,
                'content_type': request.content_type
            }), 400
            
        # Log the start of processing
        text_length = len(data['text']) if data['text'] else 0
        logger.info(f"[Request {request_id}] Starting analysis of text (length: {text_length})")
        
        # Process the text using asyncio
        try:
            # Use asyncio to run the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    citation_service.process_citations_from_text(data['text'])
                )
            finally:
                loop.close()
                
            logger.debug(f"[Request {request_id}] Processed with result: {result}")
            
            if 'status' in result and result['status'] == 'error':
                error_msg = f"[Request {request_id}] Processing error: {result.get('error')}"
                logger.error(error_msg)
                return jsonify({
                    'error': result.get('error', 'Error processing text'),
                    'request_id': request_id,
                    'details': result.get('details') if current_app.debug else None
                }), 500
                    
            logger.info(f"[Request {request_id}] Successfully processed text")
            return jsonify(result)
                
        except Exception as e:
            error_msg = f"[Request {request_id}] Exception in processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': 'Failed to process text',
                'request_id': request_id,
                'details': str(e) if current_app.debug else None
            }), 500
            
    except ImportError as e:
        logger.error(f"[Request {request_id}] Import error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'Configuration error',
            'details': str(e) if current_app.debug else None,
            'request_id': request_id
        }), 500
        
    except Exception as e:
        logger.error(
            f"[Request {request_id}] Unexpected error in /analyze endpoint: {str(e)}\n{traceback.format_exc()}"
        )
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e) if current_app.debug else None,
            'request_id': request_id,
            'content_type': request.content_type
        }), 500


@vue_api.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and analyze a file for citations.
    
    Expected multipart/form-data with:
    - file: The file to analyze
    
    Returns:
        JSON response with citation analysis results
    """
    # Log the start of the request
    request_id = str(uuid.uuid4())
    logger.info(f"[Request {request_id}] Starting file upload request")
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'request_id': request_id
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'request_id': request_id
            }), 400
            
        # Secure the filename and save to temp location
        if file.filename is None:
            return jsonify({
                'error': 'Invalid filename',
                'request_id': request_id
            }), 400
            
        filename = secure_filename(file.filename)
        logger.info(f"[Request {request_id}] Processing file: {filename}")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file to temporary location
        temp_file_path = os.path.join(uploads_dir, f"{request_id}_{filename}")
        file.save(temp_file_path)
        logger.info(f"[Request {request_id}] File saved to: {temp_file_path}")
        
        try:
            # Process the file using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    citation_service.processor.process_document(temp_file_path)
                )
            finally:
                loop.close()
                
            logger.debug(f"[Request {request_id}] Processed with result: {result}")
            
            if 'status' in result and result['status'] == 'error':
                error_msg = f"[Request {request_id}] Processing error: {result.get('error')}"
                logger.error(error_msg)
                return jsonify({
                    'error': result.get('error', 'Error processing file'),
                    'request_id': request_id,
                    'details': result.get('details') if current_app.debug else None
                }), 500
                    
            logger.info(f"[Request {request_id}] Successfully processed file")
            return jsonify(result)
                
        except Exception as e:
            error_msg = f"[Request {request_id}] Exception in processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': 'Failed to process file',
                'request_id': request_id,
                'details': str(e) if current_app.debug else None
            }), 500
            
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
                logger.info(f"[Request {request_id}] Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"[Request {request_id}] Failed to clean up file: {cleanup_error}")
            
    except Exception as e:
        logger.error(
            f"[Request {request_id}] Unexpected error in /upload endpoint: {str(e)}\n{traceback.format_exc()}"
        )
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e) if current_app.debug else None,
            'request_id': request_id
        }), 500


# This ensures the blueprint is available when imported
if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
    app.run(debug=True)
