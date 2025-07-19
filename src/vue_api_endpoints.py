"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from .api.services.citation_service import CitationService
from .database_manager import get_database_manager

logger = logging.getLogger(__name__)

# Create the blueprint
vue_api = Blueprint('vue_api', __name__)

# Initialize citation service
citation_service = CitationService()

@vue_api.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Basic health checks
        db_manager = get_database_manager()
        db_stats = db_manager.get_database_stats()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0',
            'components': {
                'database': 'healthy',
                'citation_processor': 'healthy',
                'upload_directory': 'healthy'
            },
            'database_stats': {
                'tables': len(db_stats.get('tables', {})),
                'size_mb': round(db_stats.get('database_size_mb', 0), 2)
            }
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@vue_api.route('/db_stats', methods=['GET'])
def db_stats():
    """Database statistics endpoint"""
    try:
        db_manager = get_database_manager()
        stats = db_manager.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Database stats error: {e}")
        return jsonify({'error': 'Database stats unavailable'}), 503

@vue_api.route('/analyze', methods=['POST'])
def analyze():
    """Main analyze endpoint that handles text, file, and URL input"""
    logger.info("=== ANALYZE ENDPOINT CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Content type: {request.content_type}")
    
    try:
        # Handle file upload
        if 'file' in request.files:
            return _handle_file_upload()
        
        # Handle JSON input
        elif request.is_json:
            return _handle_json_input()
        
        # Handle form input
        elif request.form:
            return _handle_form_input()
        
        else:
            return jsonify({'error': 'Invalid or missing input. Please provide text, file, or URL.'}), 400
            
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500

@vue_api.route('/analyze_enhanced', methods=['POST'])
def analyze_enhanced():
    """Enhanced analyze endpoint with better citation extraction, clustering, and verification"""
    logger.info("=== ENHANCED_ANALYZE ENDPOINT CALLED ===")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        input_type = data.get('type', 'text')
        
        if input_type == 'text':
            text = data.get('text', '')
            if not text:
                return jsonify({'error': 'No text provided'}), 400
            
            # Check if this should be processed immediately
            if citation_service.should_process_immediately({'type': 'text', 'text': text}):
                logger.info("Processing text immediately")
                result = citation_service.process_immediately({'type': 'text', 'text': text})
            else:
                logger.info("Processing text asynchronously")
                # Generate task ID and process
                task_id = str(uuid.uuid4())
                result = citation_service.process_citation_task(
                    task_id, 
                    'text', 
                    {'text': text}
                )
            
            if result['status'] == 'completed':
                return jsonify({
                    'citations': result['citations'],
                    'clusters': result.get('clusters', []),
                    'success': True,
                    'statistics': result.get('statistics', {}),
                    'metadata': result.get('metadata', {})
                })
            else:
                return jsonify({
                    'error': result.get('message', 'Processing failed'),
                    'success': False
                }), 500
        
        else:
            return jsonify({'error': 'File upload processing not implemented in this endpoint'}), 501
            
    except Exception as e:
        logger.error(f"Error in enhanced analyze endpoint: {e}", exc_info=True)
        return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500

def _handle_file_upload():
    """Handle file upload processing"""
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400
    
    try:
        # Secure filename and create unique name
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file temporarily
        temp_file_path = os.path.join(uploads_dir, unique_filename)
        file.save(temp_file_path)
        
        try:
            # Process the file
            task_id = str(uuid.uuid4())
            result = citation_service.process_citation_task(
                task_id,
                'file',
                {
                    'file_path': temp_file_path,
                    'filename': filename,
                    'file_ext': file_ext
                }
            )
            
            # Clean up file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            if result['status'] == 'success':
                return jsonify({
                    'citations': result['citations'],
                    'clusters': result.get('clusters', []),
                    'success': True,
                    'statistics': result.get('statistics', {}),
                    'metadata': result.get('metadata', {})
                })
            else:
                return jsonify({
                    'error': result.get('error', 'File processing failed'),
                    'success': False
                }), 500
                
        except Exception as e:
            # Ensure cleanup even if processing fails
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise
            
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

def _handle_json_input():
    """Handle JSON input processing"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    input_type = data.get('type', 'text')
    
    if input_type == 'text':
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        return _process_text_input(text)
        
    elif input_type == 'url':
        url = data.get('url', '')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        return _process_url_input(url)
        
    else:
        return jsonify({'error': 'Invalid input type. Use "text" or "url"'}), 400

def _handle_form_input():
    """Handle form input processing"""
    data = request.form.to_dict()
    input_type = data.get('type', 'text')
    
    if input_type == 'text':
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        return _process_text_input(text)
        
    elif input_type == 'url':
        url = data.get('url', '')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        return _process_url_input(url)
        
    else:
        return jsonify({'error': 'Invalid input type. Use "text" or "url"'}), 400

def _process_text_input(text, source_name="pasted_text"):
    """Process text input and return results"""
    try:
        # Check if should process immediately
        if citation_service.should_process_immediately({'type': 'text', 'text': text}):
            result = citation_service.process_immediately({'type': 'text', 'text': text})
        else:
            # Process asynchronously
            task_id = str(uuid.uuid4())
            result = citation_service.process_citation_task(
                task_id,
                'text',
                {'text': text, 'source_name': source_name}
            )
        
        if result['status'] in ['completed', 'success']:
            return jsonify({
                'citations': result['citations'],
                'clusters': result.get('clusters', []),
                'success': True,
                'statistics': result.get('statistics', {}),
                'metadata': result.get('metadata', {})
            })
        else:
            return jsonify({
                'error': result.get('message', 'Text processing failed'),
                'success': False
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing text input: {e}", exc_info=True)
        return jsonify({'error': 'Text processing failed', 'details': str(e)}), 500

def _process_url_input(url):
    """Process URL input and return results"""
    try:
        # Process URL
        task_id = str(uuid.uuid4())
        result = citation_service.process_citation_task(
            task_id,
            'url',
            {'url': url}
        )
        
        if result['status'] in ['completed', 'success']:
            return jsonify({
                'citations': result['citations'],
                'clusters': result.get('clusters', []),
                'success': True,
                'statistics': result.get('statistics', {}),
                'metadata': result.get('metadata', {})
            })
        else:
            return jsonify({
                'error': result.get('error', 'URL processing failed'),
                'success': False
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing URL input: {e}", exc_info=True)
        return jsonify({'error': 'URL processing failed', 'details': str(e)}), 500
