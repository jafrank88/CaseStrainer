"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
import sys
import uuid
import logging
import traceback
import time
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from src.api.services.citation_service import CitationService
from src.database_manager import get_database_manager

logger = logging.getLogger(__name__)

# Create the blueprint
vue_api = Blueprint('vue_api', __name__)

# Initialize citation service
citation_service = CitationService()

# Rest of the file content will be copied from the original file...

@vue_api.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with detailed diagnostics"""
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': 'unknown',
        'components': {},
        'database_stats': {},
        'environment': {
            'python_version': sys.version.split()[0],
            'platform': sys.platform
        },
        'endpoints': {
            'current': '/casestrainer/api/health',
            'alias': '/health',
            'base_url': request.base_url
        }
    }
    
    try:
        # Try to get version from VERSION file
        try:
            version_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'VERSION')
            if os.path.exists(version_path):
                with open(version_path, 'r', encoding='utf-8') as vf:
                    health_data['version'] = vf.read().strip()
            else:
                health_data['version'] = 'development'
                logger.warning("VERSION file not found, using 'development'")
        except Exception as e:
            health_data['version'] = 'error'
            health_data['components']['version_check'] = f'error: {str(e)}'
            logger.warning(f"Could not read VERSION file: {e}")

        # Check database connection
        try:
            db_manager = get_database_manager()
            db_stats = db_manager.get_database_stats()
            health_data['components']['database'] = 'healthy'
            health_data['database_stats'] = {
                'tables': len(db_stats.get('tables', {})),
                'size_mb': round(db_stats.get('database_size_mb', 0), 2),
                'path': os.path.abspath(db_manager.db_path) if hasattr(db_manager, 'db_path') else 'unknown'
            }
        except Exception as e:
            health_data['status'] = 'degraded'
            health_data['components']['database'] = f'error: {str(e)}'
            logger.error(f"Database check failed: {e}")

        # Check upload directory
        try:
            upload_dir = os.path.join(current_app.root_path, 'uploads')
            if os.path.isdir(upload_dir) and os.access(upload_dir, os.W_OK):
                health_data['components']['upload_directory'] = 'healthy'
            else:
                health_data['status'] = 'degraded'
                health_data['components']['upload_directory'] = 'unwritable'
        except Exception as e:
            health_data['status'] = 'degraded'
            health_data['components']['upload_directory'] = f'error: {str(e)}'

        # Check citation processor
        try:
            # Simple check if citation service is importable
            from api.services.citation_service import CitationService
            health_data['components']['citation_processor'] = 'healthy'
        except Exception as e:
            health_data['status'] = 'degraded'
            health_data['components']['citation_processor'] = f'error: {str(e)}'
            logger.error(f"Citation processor check failed: {e}")

        # Set appropriate status code
        status_code = 200 if health_data['status'] == 'healthy' else 207  # 207 for partial content
        
        return jsonify(health_data), status_code

    except Exception as e:
        logger.error(f"Health check failed completely: {e}", exc_info=True)
        health_data.update({
            'status': 'unhealthy',
            'error': str(e),
            'traceback': str(traceback.format_exc()) if 'traceback' in locals() else 'Not available'
        })
        return jsonify(health_data), 500

# Add this alias route for /casestrainer/api/health
@vue_api.route('/casestrainer/api/health', methods=['GET'])
def health_check_alias():
    return health_check()

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
async def analyze():
    """
    Main analysis endpoint that handles all types of input (file, JSON, form, URL).
    
    This endpoint routes requests to the appropriate handler based on the input type:
    - File uploads (multipart/form-data with file)
    - JSON payloads (application/json)
    - Form data (application/x-www-form-urlencoded or multipart/form-data)
    - URL parameters (for backward compatibility)
    
    Returns:
        Response with analysis results or task status
    """
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Log request details
    logger.info(f"=== ANALYZE ENDPOINT CALLED [Request ID: {request_id}] ===")
    logger.info(f"[Request {request_id}] Method: {request.method}")
    logger.info(f"[Request {request_id}] URL: {request.url}")
    logger.info(f"[Request {request_id}] Content-Type: {request.content_type}")
    logger.debug(f"[Request {request_id}] Headers: {dict(request.headers)}")
    
    # Initialize response metadata
    start_time = time.time()
    metadata = {
        'request_id': request_id,
        'endpoint': '/analyze',
        'timestamp': datetime.utcnow().isoformat(),
        'processing_mode': 'unknown',
        'source': 'direct_api',
        'input_type': 'unknown',
        'input_size': len(request.data) if request.data else 0,
        'content_type': request.content_type or 'not_specified'
    }
    
    try:
        # Log form data if present
        if request.form:
            logger.debug(f"[Request {request_id}] Form data received: {dict(request.form)}")
        
        # Log files if present
        if request.files:
            logger.info(f"[Request {request_id}] Files received: {[f.filename for f in request.files.values()]}")
        
        # Initialize citation service
        service = CitationService()
        
        # Try to parse JSON data if present
        json_data = None
        if request.data:
            try:
                json_data = request.get_json(silent=True, force=True)
                if json_data:
                    # Sanitize and log JSON data
                    sanitized_data = {}
                    for k, v in json_data.items():
                        if isinstance(v, str) and len(v) > 100:
                            sanitized_data[k] = f"[content of length {len(v)}]"
                        else:
                            sanitized_data[k] = v
                    logger.debug(f"[Request {request_id}] JSON data: {sanitized_data}")
            except Exception as e:
                logger.warning(f"[Request {request_id}] Failed to parse JSON data: {str(e)}")
        
        # Route to appropriate handler based on input type
        # 1. Check for file uploads first
        if 'file' in request.files and request.files['file'].filename:
            logger.info(f"[Request {request_id}] Routing to file upload handler")
            metadata.update({
                'input_type': 'file',
                'filename': request.files['file'].filename,
                'content_type': request.files['file'].content_type or 'application/octet-stream'
            })
            
            try:
                result = await _handle_file_upload(service, request_id)
                return _format_response(result, request_id, metadata, start_time)
                
            except Exception as e:
                error_msg = f"Error in file upload handler: {str(e)}"
                logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
                return _format_error(
                    error_msg, 
                    status_code=500, 
                    request_id=request_id, 
                    metadata={
                        **metadata,
                        'error_type': 'file_upload_error',
                        'error_details': str(e)
                    }
                )
        
        # 2. Check for JSON input
        elif request.is_json or json_data:
            logger.info(f"[Request {request_id}] Routing to JSON input handler")
            metadata.update({
                'input_type': 'json',
                'has_json_data': json_data is not None
            })
            
            try:
                result = await _handle_json_input(service, request_id, json_data or request.get_json())
                return _format_response(result, request_id, metadata, start_time)
                
            except Exception as e:
                error_msg = f"Error in JSON input handler: {str(e)}"
                logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
                return _format_error(
                    error_msg,
                    status_code=400,
                    request_id=request_id,
                    metadata={
                        **metadata,
                        'error_type': 'json_parse_error',
                        'error_details': str(e)
                    }
                )
        
        # 3. Check for form data (including URL parameters)
        elif request.form:
            logger.info(f"[Request {request_id}] Routing to form input handler")
            metadata.update({
                'input_type': 'form',
                'form_fields': list(request.form.keys())
            })
            
            try:
                result = await _handle_form_input(service, request_id)
                return _format_response(result, request_id, metadata, start_time)
                
            except Exception as e:
                error_msg = f"Error in form input handler: {str(e)}"
                logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
                return _format_error(
                    error_msg,
                    status_code=400,
                    request_id=request_id,
                    metadata={
                        **metadata,
                        'error_type': 'form_parse_error',
                        'error_details': str(e)
                    }
                )
        
        # 4. Check for raw URL in request data (for backward compatibility)
        elif request.data and isinstance(request.data, (str, bytes)):
            try:
                url = request.data.decode('utf-8').strip() if isinstance(request.data, bytes) else request.data.strip()
                if url.startswith(('http://', 'https://')):
                    logger.info(f"[Request {request_id}] Detected raw URL input: {url}")
                    metadata.update({
                        'input_type': 'url',
                        'url': url
                    })
                    
                    result = await _process_url_input(url)
                    return _format_response(result, request_id, metadata, start_time)
                    
            except Exception as e:
                logger.warning(f"[Request {request_id}] Failed to process as URL: {str(e)}")
        
        # 5. No valid input found
        content_type = request.content_type or 'not specified'
        error_msg = (
            f"Invalid or missing input. No file, JSON, or form data found. "
            f"Content-Type: {content_type}, Data length: {len(request.data) if request.data else 0}"
        )
        logger.error(f"[Request {request_id}] {error_msg}")
        logger.debug(f"[Request {request_id}] Request data: {request.data[:1000] if request.data else 'No data'}")
        
        return _format_error(
            'Invalid or missing input. Please check the Content-Type header and request format.',
            details=error_msg,
            status_code=400,
            request_id=request_id,
            metadata={
                **metadata,
                'error_type': 'invalid_input',
                'error_details': error_msg
            }
        )
        
    except Exception as e:
        error_msg = f"Unexpected error in analyze endpoint: {str(e)}"
        logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
        
        return _format_error(
            'An unexpected error occurred during analysis',
            details=str(e),
            status_code=500,
            request_id=request_id,
            metadata={
                **metadata,
                'error_type': 'unexpected_error',
                'error_details': str(e)
            }
        )


def _format_response(result, request_id, metadata, start_time):
    """Format a successful response with consistent structure"""
    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Ensure metadata is included in the response
    if not isinstance(result, dict):
        result = {}
    
    # Update metadata with timing information
    metadata.update({
        'processing_time_ms': processing_time_ms,
        'processing_mode': result.get('metadata', {}).get('processing_mode', metadata.get('processing_mode', 'unknown')),
        'status': result.get('status', 'completed'),
        'success': result.get('success', True)
    })
    
    # Ensure required fields are present
    response_data = {
        'citations': result.get('citations', []),
        'clusters': result.get('clusters', []),
        'statistics': result.get('statistics', {}),
        'request_id': request_id,
        'success': result.get('success', True),
        'metadata': {**result.get('metadata', {}), **metadata}
    }
    
    # Include task information if this is an async task
    if 'task_id' in result:
        response_data.update({
            'task_id': result['task_id'],
            'status': result.get('status', 'processing'),
            'message': result.get('message', 'Request is being processed')
        })
    
    # Include any additional fields from the result
    for key in ['message', 'warnings', 'debug']:
        if key in result and key not in response_data:
            response_data[key] = result[key]
    
    # Log successful response (without large data)
    log_data = response_data.copy()
    if 'citations' in log_data and len(log_data['citations']) > 5:
        log_data['citations'] = f"[list of {len(log_data['citations'])} citations]"
    if 'clusters' in log_data and len(log_data['clusters']) > 3:
        log_data['clusters'] = f"[list of {len(log_data['clusters'])} clusters]"
    
    logger.info(f"[Request {request_id}] Request completed successfully in {processing_time_ms}ms")
    logger.debug(f"[Request {request_id}] Response data: {log_data}")
    
    return jsonify(response_data)


def _format_error(message, details=None, status_code=400, request_id=None, metadata=None):
    """Format an error response with consistent structure"""
    error_data = {
        'error': message,
        'details': details or message,
        'request_id': request_id or str(uuid.uuid4()),
        'success': False,
        'citations': [],
        'clusters': [],
        'metadata': metadata or {}
    }
    
    # Ensure metadata has required fields
    if 'request_id' not in error_data['metadata'] and request_id:
        error_data['metadata']['request_id'] = request_id
    
    if 'status' not in error_data['metadata']:
        error_data['metadata']['status'] = 'error'
    
    logger.error(f"[Request {request_id or 'unknown'}] Error: {message}")
    if details and details != message:
        logger.error(f"[Request {request_id or 'unknown'}] Details: {details}")
    
    return jsonify(error_data), status_code

@vue_api.route('/analyze_enhanced', methods=['POST'])
async def analyze_enhanced():
    """Enhanced analyze endpoint with better citation extraction, clustering, and verification"""
    logger.info("=== ENHANCED_ANALYZE ENDPOINT CALLED ===")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided', 'citations': [], 'clusters': []}), 400
        
        input_type = data.get('type', 'text')
        
        if input_type == 'text':
            text = data.get('text', '')
            if not text:
                return jsonify({'error': 'No text provided', 'citations': [], 'clusters': []}), 400
            
            # Check if this should be processed immediately
            if citation_service.should_process_immediately({'type': 'text', 'text': text}):
                logger.info("Processing text immediately")
                result = citation_service.process_immediately({'type': 'text', 'text': text})
            else:
                logger.info("Processing text asynchronously")
                # Generate task ID and process
                task_id = str(uuid.uuid4())
                result = await citation_service.process_citation_task(
                    task_id, 
                    'text', 
                    {'text': text}
                )
            
            # Handle the result
            if isinstance(result, dict) and result.get('status') == 'completed':
                return jsonify({
                    'citations': result.get('citations', []),
                    'clusters': result.get('clusters', []),
                    'success': True,
                    'statistics': result.get('statistics', {}),
                    'metadata': result.get('metadata', {})
                })
            else:
                return jsonify({
                    'error': result.get('message', 'Processing failed') if isinstance(result, dict) else 'Processing failed',
                    'success': False
                }), 500
        
        else:
            return jsonify({'error': 'File upload processing not implemented in this endpoint', 'citations': [], 'clusters': []}), 501
            
    except Exception as e:
        logger.error(f"Error in enhanced analyze endpoint: {e}", exc_info=True)
        return jsonify({'error': 'Analysis failed', 'details': str(e), 'citations': [], 'clusters': []}), 500

@vue_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Check the status of a queued task"""
    logger.info(f"Checking status for task_id: {task_id}")
    
    try:
        from rq import Queue, Worker
        from redis import Connection
        from redis import Redis
        
        # Get Redis connection from environment (required)
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            logger.error("REDIS_URL environment variable not set")
            return jsonify({
                'error': 'Server configuration error',
                'details': 'Redis URL not configured',
                'task_id': task_id,
                'citations': [],
                'clusters': []
            }), 500
            
        logger.info(f"Connecting to Redis at: {redis_url}")
        
        redis_conn = Redis.from_url(redis_url, socket_connect_timeout=5, socket_timeout=5)
        
        # Test the connection
        try:
            redis_conn.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return jsonify({
                'error': 'Failed to connect to task queue',
                'details': str(e),
                'task_id': task_id,
                'citations': [],
                'clusters': []
            }), 500
        
        # Get the queue
        queue = Queue('casestrainer', connection=redis_conn)
        
        # Log all job IDs in the queue for debugging
        job_ids = queue.job_ids
        logger.info(f"Found {len(job_ids)} jobs in queue. Job IDs: {job_ids}")
        
        # Get the job
        job = queue.fetch_job(task_id)
        
        if not job:
            logger.warning(f"Job {task_id} not found in queue")
            return jsonify({
                'error': 'Task not found',
                'task_id': task_id,
                'citations': [],
                'clusters': []
            }), 404
        
        # Log job details
        logger.info(f"Job {task_id} status: {job.get_status()}")
        logger.info(f"Job {task_id} meta: {job.meta}")
        
        # Get job result if available
        result = None
        if job.is_finished:
            try:
                result = job.result
                logger.info(f"Job {task_id} result type: {type(result)}")
            except Exception as e:
                logger.error(f"Error getting job result: {e}")
        
        # Check job status
        if job.is_finished:
            # Job completed successfully
            if result and isinstance(result, dict) and result.get('status') in ['success', 'completed']:
                return jsonify({
                    'status': 'completed',
                    'task_id': task_id,
                    'citations': result.get('citations', []),
                    'clusters': result.get('clusters', []),
                    'statistics': result.get('statistics', {}),
                    'metadata': result.get('metadata', {}),
                    'success': True
                })
            else:
                error_msg = 'Unknown error'
                if result and isinstance(result, dict):
                    error_msg = result.get('error', 'Processing failed')
                elif job.exc_info:
                    error_msg = f"Job failed with exception: {job.exc_info}"
                
                logger.error(f"Job {task_id} failed: {error_msg}")
                return jsonify({
                    'status': 'failed',
                    'task_id': task_id,
                    'error': error_msg,
                    'success': False,
                    'citations': [],
                    'clusters': []
                })
        
        elif job.is_failed:
            # Job failed
            error_msg = str(job.exc_info) if job.exc_info else 'Job failed without exception info'
            logger.error(f"Job {task_id} failed: {error_msg}")
            return jsonify({
                'status': 'failed',
                'task_id': task_id,
                'error': error_msg,
                'success': False,
                'citations': [],
                'clusters': []
            })
        
        elif job.is_started:
            # Job is currently running
            return jsonify({
                'status': 'processing',
                'task_id': task_id,
                'message': 'Task is currently being processed',
                'success': True,
                'citations': [],
                'clusters': []
            })
        
        else:
            # Job is queued but not started yet
            try:
                position = queue.get_job_position(task_id)
            except Exception as e:
                logger.warning(f"Could not get job position: {e}")
                position = -1
                
            return jsonify({
                'status': 'queued',
                'task_id': task_id,
                'message': f'Task is queued and waiting to be processed (position: {position})',
                'position': position,
                'success': True,
                'citations': [],
                'clusters': []
            })
            
    except Exception as e:
        error_msg = f"Error checking task status for {task_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'error': 'Failed to check task status',
            'details': str(e),
            'task_id': task_id,
            'citations': [],
            'clusters': []
        }), 500

async def _handle_file_upload(service, request_id):
    """
    Handle file upload with proper async processing and CitationService integration
    
    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
        
    Returns:
        Response with analysis results or task status
    """
    logger.info(f"[File Upload {request_id}] Starting file upload handler")
    
    try:
        if 'file' not in request.files:
            error_msg = 'No file provided in request.files'
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                'error': error_msg,
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False,
                'metadata': {}
            }
        
        file = request.files['file']
        if not file or file.filename == '':
            error_msg = 'No file selected or empty file'
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                'error': error_msg,
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False,
                'metadata': {}
            }
        
        # Log file details
        filename = secure_filename(file.filename) if file.filename else 'unknown_file'
        logger.info(f"[File Upload {request_id}] Processing file: {filename}")
        logger.info(f"[File Upload {request_id}] Content type: {file.content_type}")
        
        # Validate file type
        allowed_extensions = {'pdf', 'txt', 'doc', 'docx', 'rtf'}
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            error_msg = f'File type not allowed. Allowed types: {', '.join(allowed_extensions)}. Got: {file_ext}'
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                'error': error_msg,
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False,
                'metadata': {}
            }
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        logger.info(f"[File Upload {request_id}] Generated secure filename: {unique_filename}")
        
        # Ensure uploads directory exists with proper permissions
        uploads_dir = os.path.join(current_app.instance_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        logger.info(f"[File Upload {request_id}] Upload directory: {uploads_dir}")
        
        # Save the file with proper error handling
        file_path = os.path.join(uploads_dir, unique_filename)
        logger.info(f"[File Upload {request_id}] Saving file to: {file_path}")
        
        try:
            file.save(file_path)
            
            # Verify file was saved
            if not os.path.exists(file_path):
                raise IOError("File was not saved successfully")
                
            logger.info(f"[File Upload {request_id}] File saved successfully")
            
            # Get options from form data if provided
            options = {}
            if 'options' in request.form:
                try:
                    options = json.loads(request.form['options'])
                    logger.info(f"[File Upload {request_id}] Parsed options: {options}")
                except json.JSONDecodeError as e:
                    logger.warning(f"[File Upload {request_id}] Failed to parse options JSON: {e}")
            
            # Process the file using CitationService
            logger.info(f"[File Upload {request_id}] Starting file processing with CitationService")
            
            # Check if we should process in background
            process_async = options.get('async', True)
            
            if process_async:
                # Enqueue for background processing
                from rq import Queue
                from redis import Redis
                
                redis_conn = Redis.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
                task_queue = Queue('default', connection=redis_conn)
                
                # Enqueue the task for processing
                task = task_queue.enqueue(
                    'src.tasks.process_uploaded_file',
                    filepath=file_path,
                    original_filename=filename,
                    options=options,
                    job_timeout=3600,  # 1 hour timeout
                    result_ttl=86400,  # Keep results for 24 hours
                    failure_ttl=86400,  # Keep failed jobs for 24 hours
                    job_id=f"file_{request_id}"
                )
                
                if not task:
                    raise RuntimeError("Failed to enqueue task")
                
                logger.info(f"[File Upload {request_id}] Task enqueued with ID: {task.get_id()}")
                
                return {
                    'status': 'processing',
                    'task_id': task.get_id(),
                    'request_id': request_id,
                    'message': 'File upload received and queued for processing',
                    'success': True,
                    'citations': [],
                    'clusters': [],
                    'metadata': {
                        'filename': filename,
                        'file_size': os.path.getsize(file_path),
                        'content_type': file.content_type,
                        'processing_mode': 'async'
                    }
                }
            else:
                # Process synchronously
                logger.info(f"[File Upload {request_id}] Processing file synchronously")
                
                # Read file content based on type
                if file_ext == 'pdf':
                    import PyPDF2
                    text = ''
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = '\n'.join(page.extract_text() for page in pdf_reader.pages)
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                
                # Process the text
                result = await _process_text_input(
                    service=service,
                    request_id=request_id,
                    text=text,
                    source_name=filename
                )
                
                # Add file metadata to result
                result['metadata'].update({
                    'filename': filename,
                    'file_size': os.path.getsize(file_path),
                    'content_type': file.content_type,
                    'processing_mode': 'sync'
                })
                
                return result
                
        except IOError as e:
            error_msg = f"Failed to process file: {str(e)}"
            logger.error(f"[File Upload {request_id}] {error_msg}", exc_info=True)
            return {
                'error': error_msg,
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False,
                'metadata': {}
            }
            
        except Exception as e:
                error_msg = f"Failed to enqueue task: {str(e)}"
                logger.error(f"[File Upload {request_id}] {error_msg}", exc_info=True)
                
                # Clean up the uploaded file if task creation failed
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"[File Upload {request_id}] Cleaned up file after task enqueue failure")
                except Exception as cleanup_error:
                    logger.error(f"[File Upload {request_id}] Failed to clean up file: {str(cleanup_error)}")
                
                return jsonify({
                    'error': error_msg,
                    'citations': [],
                    'clusters': [],
                    'request_id': request_id
                }), 500
            
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return jsonify({'error': f'Failed to process file: {str(e)}', 'citations': [], 'clusters': []}), 500

async def _handle_json_input(service, request_id, data=None):
    """
    Handle JSON input processing with CitationService integration
    
    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
        data: Optional pre-parsed JSON data (for testing or direct call)
        
    Returns:
        Dictionary with analysis results or error information
    """
    logger.info(f"[JSON Input {request_id}] Starting JSON input processing")
    
    try:
        # Log request details
        logger.info(f"[JSON Input {request_id}] Request URL: {request.url}")
        logger.info(f"[JSON Input {request_id}] Request method: {request.method}")
        logger.info(f"[JSON Input {request_id}] Content-Type: {request.content_type}")
        
        # Get JSON data if not provided
        if data is None:
            # Log raw request data for debugging
            try:
                raw_data = request.get_data(as_text=True)
                logger.info(f"[JSON Input {request_id}] Raw request data (first 1000 chars): {raw_data[:1000]}")
            except Exception as e:
                logger.warning(f"[JSON Input {request_id}] Could not read raw request data: {e}")
            
            # Parse JSON data
            try:
                data = request.get_json(force=True, silent=True)
                if data is None:
                    error_msg = "Failed to parse JSON data"
                    logger.error(f"[JSON Input {request_id}] {error_msg}")
                    return {
                        'error': error_msg,
                        'citations': [],
                        'clusters': [],
                        'request_id': request_id,
                        'success': False,
                        'metadata': {}
                    }
            except Exception as e:
                error_msg = f"Error parsing JSON: {str(e)}"
                logger.error(f"[JSON Input {request_id}] {error_msg}", exc_info=True)
                return {
                    'error': 'Invalid JSON data',
                    'details': str(e),
                    'citations': [],
                    'clusters': [],
                    'request_id': request_id,
                    'success': False,
                    'metadata': {}
                }
        
        # Log sanitized data (truncate long text fields)
        sanitized_data = {}
        for k, v in data.items():
            if isinstance(v, str):
                sanitized_data[k] = v[:100] + '...' if len(v) > 100 else v
            else:
                sanitized_data[k] = str(v)[:200] + '...' if len(str(v)) > 200 else v
        
        logger.info(f"[JSON Input {request_id}] Processing data with keys: {list(data.keys())}")
        logger.debug(f"[JSON Input {request_id}] Sanitized data: {sanitized_data}")
        
        # Process based on input type
        input_type = data.get('type', 'text')
        logger.info(f"[JSON Input {request_id}] Input type: {input_type}")
        
        if input_type == 'text':
            text = data.get('text', '')
            logger.info(f"[JSON Input {request_id}] Text input received. Length: {len(text)}")
            
            if not text:
                error_msg = 'No text provided in JSON data'
                logger.error(f"[JSON Input {request_id}] {error_msg}")
                return {
                    'error': error_msg,
                    'citations': [],
                    'clusters': [],
                    'request_id': request_id,
                    'success': False,
                    'metadata': {}
                }
                
            logger.info(f"[JSON Input {request_id}] Processing text input...")
            try:
                result = _process_text_input(
                    service=service,
                    request_id=request_id,
                    text=text,
                    source_name="api-input"
                )
                logger.info(f"[_handle_json_input] [Request {request_id}] Text processing completed successfully")
                return result
            except Exception as e:
                logger.error(f"[_handle_json_input] [Request {request_id}] Error in _process_text_input: {str(e)}", exc_info=True)
                raise
            
        elif input_type == 'url':
            url = data.get('url', '')
            logger.info(f"[_handle_json_input] [Request {request_id}] URL input received: {url}")
            
            if not url:
                logger.error(f"[_handle_json_input] [Request {request_id}] No URL provided")
                return jsonify({
                    'error': 'No URL provided', 
                    'citations': [], 
                    'clusters': [],
                    'request_id': request_id
                }), 400
                
            logger.info(f"[_handle_json_input] [Request {request_id}] Processing URL input...")
            try:
                result = await _process_url_input(url)
                logger.info(f"[_handle_json_input] [Request {request_id}] URL processing completed successfully")
                return result
            except Exception as e:
                logger.error(f"[_handle_json_input] [Request {request_id}] Error in _process_url_input: {str(e)}", exc_info=True)
                raise
            
        else:
            error_msg = f"Invalid input type: {input_type}"
            logger.error(f"[_handle_json_input] [Request {request_id}] {error_msg}")
            return jsonify({
                'error': error_msg,
                'citations': [], 
                'clusters': [],
                'request_id': request_id
            }), 400
            
    except Exception as e:
        error_msg = f"Error processing JSON input: {str(e)}"
        logger.error(f"[_handle_json_input] [Request {request_id}] {error_msg}", exc_info=True)
        
        # Include more detailed error information for debugging
        error_details = {
            'error': 'Internal server error',
            'type': type(e).__name__,
            'message': str(e),
            'request_id': request_id,
            'citations': [],
            'clusters': []
        }
        
        # Include traceback in the response in development mode
        if current_app.config.get('DEBUG', False):
            import traceback
            error_details['traceback'] = traceback.format_exc()
        
        return jsonify(error_details), 500

async def _handle_form_input(service, request_id):
    """
    Handle form input processing with CitationService integration
    
    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
    """
    try:
        # Handle form data processing
        form_data = request.form.to_dict()
        text = form_data.get('text', '')
        
        if not text:
            return jsonify({
                'error': 'No text provided in form data',
                'citations': [],
                'clusters': [],
                'request_id': request_id
            }), 400
        
        # Process text input
        result = await _process_text_input(service, request_id, text)
        return result
        
    except Exception as e:
        logger.error(f"[Form Input {request_id}] Error: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Error processing form input: {str(e)}',
            'citations': [],
            'clusters': [],
            'request_id': request_id
        }), 500

async def _process_text_input(service, request_id, text, source_name="form-input"):
    """Process text input with citation service."""
    try:
        logger.info(f"[Text Input {request_id}] Processing text of length: {len(text)}")
        
        # Process text with citation service
        result = await service.process_text(text)
        
        return {
            'citations': result.get('citations', []),
            'clusters': result.get('clusters', []),
            'request_id': request_id,
            'success': True,
            'metadata': {
                'source': source_name,
                'text_length': len(text),
                'processing_time': time.time()
            }
        }
    except Exception as e:
        logger.error(f"[Text Input {request_id}] Error: {str(e)}", exc_info=True)
        raise

async def _process_url_input(url):
    """Process URL input with citation service."""
    try:
        logger.info(f"[URL Input] Processing URL: {url}")
        
        # Import citation service
        from src.api.services.citation_service import CitationService
        service = CitationService()
        
        # Process URL with citation service - use text processing for now
        # TODO: Implement proper URL processing
        result = await service.process_citations_from_text(f"URL content from: {url}")
        
        return {
            'citations': result.get('citations', []),
            'clusters': result.get('clusters', []),
            'success': True,
            'metadata': {
                'source': 'url-input',
                'url': url,
                'processing_time': time.time()
            }
        }
    except Exception as e:
        logger.error(f"[URL Input] Error: {str(e)}", exc_info=True)
        raise