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
    logger.info(f"[Request {request_id}] About to enter try block")
    
    try:
        logger.info(f"[Request {request_id}] Entering try block")
        # Debug logging for request structure
        logger.info(f"[Request {request_id}] Files in request: {list(request.files.keys()) if request.files else 'None'}")
        logger.info(f"[Request {request_id}] Form data: {list(request.form.keys()) if request.form else 'None'}")
        
        # Check for file uploads first
        logger.info(f"[Request {request_id}] Checking for file uploads...")
        if 'file' in request.files and request.files['file'].filename:
            logger.info(f"[Request {request_id}] File upload detected: {request.files['file'].filename}")
            
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
                # Import RQ for async task processing
                from rq import Queue
                from redis import Redis
                
                # Connect to Redis using environment variable or default
                redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@redis:6379/0')
                redis_conn = Redis.from_url(redis_url)
                queue = Queue('casestrainer', connection=redis_conn)
                
                # Enqueue the file processing task using the wrapper function
                job = queue.enqueue(
                    'src.rq_worker.process_citation_task_direct',
                    args=[request_id, 'file', {'file_path': temp_file_path, 'filename': filename}],
                    job_id=request_id,
                    job_timeout='10m'
                )
                
                logger.info(f"[Request {request_id}] File processing task enqueued with job_id: {job.id}")
                
                # Return task_id immediately for frontend polling
                return jsonify({
                    'task_id': request_id,
                    'status': 'processing',
                    'message': 'File processing started'
                })
                
            except Exception as e:
                error_msg = f"[Request {request_id}] Exception in file task enqueuing: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return jsonify({
                    'error': 'Failed to start file processing',
                    'request_id': request_id,
                    'details': str(e) if current_app.debug else None
                }), 500
                
        # Get request data - handle both JSON and form data
        data = None
        if request.content_type and 'application/json' in request.content_type:
            logger.info(f"[Request {request_id}] Attempting to parse JSON data")
            logger.info(f"[Request {request_id}] Raw request data length: {len(request.get_data()) if request.get_data() else 0}")
            try:
                data = request.get_json()
                logger.info(f"[Request {request_id}] JSON parsing successful: {data}")
            except Exception as e:
                logger.error(f"[Request {request_id}] JSON parsing failed: {str(e)}")
                logger.error(f"[Request {request_id}] Raw data: {request.get_data(as_text=True)[:500]}")
                return jsonify({
                    'error': 'Invalid JSON data',
                    'request_id': request_id,
                    'content_type': request.content_type,
                    'details': str(e)
                }), 400
        else:
            # Handle form data
            text_content = request.form.get('text', '')
            if text_content is None:
                text_content = ''
            data = {
                'text': text_content,
                'type': request.form.get('type', 'text')
            }
        
        # Handle URL analysis requests
        if data and 'url' in data and data.get('type') == 'url':
            logger.info(f"[Request {request_id}] URL analysis requested: {data['url']}")
            try:
                # Import RQ for async task processing
                from rq import Queue
                from redis import Redis
                
                # Connect to Redis using environment variable or default
                redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@redis:6379/0')
                redis_conn = Redis.from_url(redis_url)
                queue = Queue('casestrainer', connection=redis_conn)
                
                # Enqueue the URL processing task using the wrapper function
                job = queue.enqueue(
                    'src.rq_worker.process_citation_task_direct',
                    args=[request_id, 'url', {'url': data['url']}],
                    job_id=request_id,
                    job_timeout='10m'
                )
                
                logger.info(f"[Request {request_id}] URL processing task enqueued with job_id: {job.id}")
                
                # Return task_id immediately for frontend polling
                return jsonify({
                    'task_id': request_id,
                    'status': 'processing',
                    'message': 'URL processing started'
                })
                
            except Exception as e:
                error_msg = f"[Request {request_id}] Exception in URL task enqueuing: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return jsonify({
                    'error': 'Failed to start URL processing',
                    'request_id': request_id,
                    'details': str(e) if current_app.debug else None
                }), 500
        
        # Handle text analysis requests
        if not data or 'text' not in data or not data['text']:
            return jsonify({
                'error': 'Missing or invalid request data',
                'request_id': request_id,
                'content_type': request.content_type
            }), 400
            
        # Log the start of processing
        text_length = len(data['text']) if data['text'] else 0
        logger.info(f"[Request {request_id}] Starting analysis of text (length: {text_length})")
        
        # Process the text using async task queue
        try:
            # Import RQ for async task processing
            from rq import Queue
            from redis import Redis
            
            # Connect to Redis using environment variable or default
            redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@redis:6379/0')
            redis_conn = Redis.from_url(redis_url)
            queue = Queue('casestrainer', connection=redis_conn)
            
            # Enqueue the text processing task using the wrapper function
            job = queue.enqueue(
                'src.rq_worker.process_citation_task_direct',
                args=[request_id, 'text', {'text': data['text']}],
                job_id=request_id,
                job_timeout='10m'
            )
            
            logger.info(f"[Request {request_id}] Text processing task enqueued with job_id: {job.id}")
            
            # Return task_id immediately for frontend polling
            return jsonify({
                'task_id': request_id,
                'status': 'processing',
                'message': 'Text processing started'
            })
            
        except Exception as e:
            error_msg = f"[Request {request_id}] Exception in text task enqueuing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': 'Failed to start text processing',
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


@vue_api.route('/processing_progress', methods=['GET'])
def processing_progress():
    """Legacy endpoint for processing progress - redirects to task_status."""
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id parameter'}), 400
    
    # Redirect to the existing task_status endpoint
    return get_task_status(task_id)

@vue_api.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get the status and results of an async task.
    
    Args:
        task_id: The task ID to check
        
    Returns:
        JSON response with task status and results if completed
    """
    logger.info(f"[Request {task_id}] Checking task status")
    
    try:
        # Import RQ for task status checking
        from rq import Queue
        from redis import Redis
        
        # Connect to Redis using environment variable or default
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@redis:6379/0')
        redis_conn = Redis.from_url(redis_url)
        queue = Queue('casestrainer', connection=redis_conn)
        
        # Get the job
        job = queue.fetch_job(task_id)
        
        if not job:
            return jsonify({
                'error': 'Task not found',
                'task_id': task_id
            }), 404
        
        # Check job status
        if job.is_finished:
            result = job.result
            logger.info(f"[Request {task_id}] Task completed successfully")
            return jsonify({
                'task_id': task_id,
                'status': 'completed',
                'result': result
            })
        elif job.is_failed:
            logger.error(f"[Request {task_id}] Task failed: {job.exc_info}")
            return jsonify({
                'task_id': task_id,
                'status': 'failed',
                'error': str(job.exc_info) if job.exc_info else 'Unknown error'
            }), 500
        else:
            # Job is still running
            logger.info(f"[Request {task_id}] Task still processing")
            return jsonify({
                'task_id': task_id,
                'status': 'processing',
                'message': 'Task is still being processed'
            })
            
    except Exception as e:
        logger.error(f"[Request {task_id}] Exception checking task status: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to check task status',
            'task_id': task_id,
            'details': str(e) if current_app.debug else None
        }), 500


# This ensures the blueprint is available when imported
if __name__ == '__main__':
    pass
