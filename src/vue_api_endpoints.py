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
                # Type: ignore for coroutine access
                result = citation_service.process_citation_task(
                    task_id, 
                    'text', 
                    {'text': text}
                )  # type: ignore
            
            # Type: ignore for coroutine access
            if result['status'] == 'completed':  # type: ignore
                # Type: ignore for coroutine access
                return jsonify({
                    'citations': result['citations'],  # type: ignore
                    'clusters': result.get('clusters', []),  # type: ignore
                    'success': True,
                    'statistics': result.get('statistics', {}),  # type: ignore
                    'metadata': result.get('metadata', {})  # type: ignore
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

@vue_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Check the status of a queued task"""
    try:
        from rq import Queue
        from redis import Redis
        
        # Get Redis connection
        redis_url = os.environ.get('REDIS_URL', 'redis://casestrainer-redis-prod:6379/0')
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
            # Job completed successfully
            result = job.result
            if result and result.get('status') in ['success', 'completed']:
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
                return jsonify({
                    'status': 'failed',
                    'task_id': task_id,
                    'error': result.get('error', 'Processing failed') if result else 'Unknown error',
                    'success': False
                })
        
        elif job.is_failed:
            # Job failed
            return jsonify({
                'status': 'failed',
                'task_id': task_id,
                'error': str(job.exc_info) if job.exc_info else 'Job failed',
                'success': False
            })
        
        elif job.is_started:
            # Job is currently running
            return jsonify({
                'status': 'processing',
                'task_id': task_id,
                'message': 'Task is currently being processed',
                'success': True
            })
        
        else:
            # Job is queued but not started yet
            return jsonify({
                'status': 'queued',
                'task_id': task_id,
                'message': 'Task is queued and waiting to be processed',
                'position': queue.get_job_position(task_id),
                'success': True
            })
            
    except Exception as e:
        logger.error(f"Error checking task status for {task_id}: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to check task status',
            'details': str(e),
            'task_id': task_id
        }), 500

def _handle_file_upload():
    """Handle file upload with proper async RQ worker processing"""
    try:
        # Get Redis connection for async processing
        from rq import Queue
        from redis import Redis
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'txt', 'doc', 'docx', 'rtf'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'}), 400
        
        # Generate unique filename
        filename = file.filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ensure uploads directory exists
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file temporarily
        temp_file_path = os.path.join(uploads_dir, unique_filename)
        file.save(temp_file_path)
        
        try:
            # Generate task ID for async processing
            task_id = str(uuid.uuid4())
            
            # Get Redis connection
            redis_url = os.environ.get('REDIS_URL', 'redis://casestrainer-redis-prod:6379/0')
            redis_conn = Redis.from_url(redis_url)
            queue = Queue('casestrainer', connection=redis_conn)
            
            # Queue the task for background processing
            job = queue.enqueue(
                citation_service.process_citation_task,
                task_id,
                'file',
                {
                    'file_path': temp_file_path,
                    'filename': filename,
                    'file_ext': file_ext
                },
                job_id=task_id,
                job_timeout='10m',
                result_ttl=3600  # Keep results for 1 hour
            )
            
            logger.info(f"Queued file processing task {task_id} for background processing")
            
            # Return immediately with task ID for polling
            return jsonify({
                'status': 'processing',
                'task_id': task_id,
                'message': 'File uploaded and queued for processing',
                'job_id': job.id,
                'success': True
            }), 202  # 202 Accepted
            
        except Exception as e:
            # Ensure cleanup even if queuing fails
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
    """Process text input with proper async RQ worker processing for longer texts"""
    try:
        # Check if should process immediately (short texts)
        if citation_service.should_process_immediately({'type': 'text', 'text': text}):
            logger.info("Processing short text immediately")
            result = citation_service.process_immediately({'type': 'text', 'text': text})
            
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
        else:
            # Process longer texts asynchronously with RQ workers
            logger.info("Processing longer text asynchronously with RQ workers")
            task_id = str(uuid.uuid4())
            
            # Queue the task for RQ worker processing
            from rq import Queue
            from redis import Redis
            
            # Get Redis connection
            redis_url = os.environ.get('REDIS_URL', 'redis://casestrainer-redis-prod:6379/0')
            redis_conn = Redis.from_url(redis_url)
            queue = Queue('casestrainer', connection=redis_conn)
            
            # Queue the task for background processing
            job = queue.enqueue(
                citation_service.process_citation_task,
                task_id,
                'text',
                {'text': text, 'source_name': source_name},
                job_id=task_id,
                job_timeout='10m',
                result_ttl=3600  # Keep results for 1 hour
            )
            
            logger.info(f"Queued text processing task {task_id} for background processing")
            
            # Return immediately with task ID for polling
            return jsonify({
                'status': 'processing',
                'task_id': task_id,
                'message': 'Text queued for processing',
                'job_id': job.id,
                'success': True
            }), 202  # 202 Accepted
            
    except Exception as e:
        logger.error(f"Error processing text input: {e}", exc_info=True)
        return jsonify({'error': 'Text processing failed', 'details': str(e)}), 500

def _process_url_input(url):
    """Process URL input with proper async RQ worker processing"""
    try:
        # Generate task ID for async processing
        task_id = str(uuid.uuid4())
        
        # Queue the task for RQ worker processing
        from rq import Queue
        from redis import Redis
        
        # Get Redis connection
        redis_url = os.environ.get('REDIS_URL', 'redis://casestrainer-redis-prod:6379/0')
        redis_conn = Redis.from_url(redis_url)
        queue = Queue('casestrainer', connection=redis_conn)
        
        # Queue the task for background processing
        job = queue.enqueue(
            citation_service.process_citation_task,
            task_id,
            'url',
            {'url': url},
            job_id=task_id,
            job_timeout='10m',
            result_ttl=3600  # Keep results for 1 hour
        )
        
        logger.info(f"Queued URL processing task {task_id} for background processing")
        
        # Return immediately with task ID for polling
        return jsonify({
            'status': 'processing',
            'task_id': task_id,
            'message': 'URL queued for processing',
            'job_id': job.id,
            'success': True
        }), 202  # 202 Accepted
        
    except Exception as e:
        logger.error(f"Error queuing URL input: {e}", exc_info=True)
        return jsonify({'error': 'URL processing failed', 'details': str(e)}), 500
