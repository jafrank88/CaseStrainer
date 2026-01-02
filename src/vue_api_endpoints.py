"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

# Simplified processor imports
from src.simplified_citation_processor import create_processor, ProcessingConfig
import os


import sys
import uuid
import logging
import time
import json
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g, Response
from werkzeug.utils import secure_filename

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.api.services.citation_service import CitationService

logger = logging.getLogger(__name__)

vue_api = Blueprint('vue_api', __name__)

citation_service = CitationService()



def should_use_simplified_processor():
    """Check if simplified processor should be used based on feature flags."""
    use_simplified = os.getenv('USE_SIMPLIFIED_PROCESSOR', 'false').lower() == 'true'
    percentage = float(os.getenv('SIMPLIFIED_PROCESSOR_PERCENTAGE', '0'))
    
    if use_simplified:
        return True, 1.0
    
    if percentage > 0:
        import random
        if random.random() < percentage / 100:
            return True, percentage / 100
    
    return False, 0


def process_with_simplified_processor(text, request_id, enable_verification=True):
    """Process text using simplified processor."""
    config = ProcessingConfig(
        enable_verification=enable_verification,
        enable_clustering=True,
        timeout_seconds=300,
        cache_results=True
    )
    
    processor = create_processor(config)
    
    input_data = {
        'type': 'text',
        'text': text
    }
    
    result = processor.process(input_data, request_id)
    
    # Convert to legacy format for compatibility
    if result.mode.value == 'synchronous':
        return {
            'status': 'completed',
            'citations': result.citations,
            'clusters': result.clusters,
            'verification_results': result.verification_results,
            'processing_time': result.processing_time,
            'method': 'simplified_optimized'
        }
    else:
        return {
            'status': 'processing',
            'task_id': result.task_id,
            'message': 'Processing asynchronously with optimized engine',
            'method': 'simplified_optimized_async'
        }


@vue_api.route('/health', methods=['GET'])
@vue_api.route('/health_check', methods=['GET'])
def health_check():
    """Health check endpoint for Docker health monitoring and external access."""
    try:
        health_status = {
            'status': 'healthy',
            'message': 'Vue API is running',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'CaseStrainer Backend',
            'version': '1.0.0',
            'checks': {}
        }
        
        try:
            import redis
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            health_status['checks']['redis'] = 'healthy'
        except Exception as e:
            health_status['checks']['redis'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        critical_dirs = ['./src', './data', './logs', './uploads']
        for dir_path in critical_dirs:
            if os.path.exists(dir_path):
                health_status['checks'][f'directory_{dir_path}'] = 'healthy'
            else:
                health_status['checks'][f'directory_{dir_path}'] = 'unhealthy'
                health_status['status'] = 'degraded'
        
        if health_status['status'] == 'healthy':
            return jsonify(health_status), 200
        elif health_status['status'] == 'degraded':
            return jsonify(health_status), 200  # Still 200 but status shows degraded
        else:
            return jsonify(health_status), 500
            
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@vue_api.route('/analyze', methods=['POST'])
def analyze_text():
    """Analyze text for citations using optimized or legacy processor."""
    try:
        # Check if we should use simplified processor
        use_simplified, rollout_percentage = should_use_simplified_processor()
        
        # CRITICAL FIX: Handle file uploads (FormData) vs JSON requests
        if request.files:
            # File upload via FormData
            file = request.files.get('file')
            input_type = request.form.get('type', 'file')
            enable_verification = request.form.get('enable_verification', 'true').lower() == 'true'
            
            if not file:
                return jsonify({
                    'error': 'No file provided',
                    'message': 'Please provide a file to analyze'
                }), 400
            
            logger.info(f"Processing file upload: {file.filename}")
            
            # Use UnifiedInputProcessor to handle file extraction and processing
            from src.unified_input_processor import UnifiedInputProcessor
            processor = UnifiedInputProcessor()
            
            request_id = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(file.filename) % 10000:04d}"
            
            if use_simplified:
                # For simplified processor, extract text first then process
                result = processor._extract_from_file(file, request_id)
                if not result.get('success'):
                    return jsonify(result), 400
                
                text = result.get('text', '')
                if not text or len(text.strip()) < 10:
                    return jsonify({
                        'error': 'File extraction failed',
                        'message': 'Could not extract readable text from file'
                    }), 400
                
                logger.info(f"[{request_id}] Using simplified processor for file upload")
                result = process_with_simplified_processor(text, request_id, enable_verification)
                
                if result.get('status') == 'processing':
                    return jsonify(result), 202
                else:
                    return jsonify(result), 200
            else:
                # Use legacy processor for file uploads
                logger.info(f"[{request_id}] Using legacy processor for file upload")
                force_mode = request.form.get('force_mode')  # Get force_mode from form data
                result = processor.process_any_input(
                    file, 'file', request_id, 'api_endpoint', force_mode=force_mode
                )
                return jsonify(result), 200
        
        # Handle JSON requests (text, URL, etc.)
        data = request.get_json() or {}
        input_type = data.get('type', 'text')
        text = data.get('text', '')
        url = data.get('url', '')
        enable_verification = data.get('enable_verification', True)
        
        # Handle URL requests
        if input_type == 'url' and url:
            logger.info(f"Processing URL request: {url}")
            try:
                # Extract text from URL using CitationService
                extracted_text = citation_service.extract_text_from_input({
                    'type': 'url',
                    'url': url
                })
                
                if not extracted_text or len(extracted_text.strip()) < 10:
                    logger.warning(f"URL returned insufficient content: {len(extracted_text) if extracted_text else 0} chars")
                    return jsonify({
                        'error': 'URL returned empty or insufficient content for analysis',
                        'message': 'Please provide a URL with readable content'
                    }), 400
                
                text = extracted_text
                logger.info(f"Successfully extracted {len(text)} characters from URL")
            except Exception as e:
                logger.error(f"Failed to extract text from URL: {e}", exc_info=True)
                return jsonify({
                    'error': 'Failed to fetch URL content',
                    'message': str(e)
                }), 400
        elif not text:
            return jsonify({
                'error': 'No text provided',
                'message': 'Please provide text to analyze'
            }), 400
        
        request_id = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000:04d}"
        
        if use_simplified:
            logger.info(f"[{request_id}] Using simplified processor (rollout: {rollout_percentage:.0%})")
            result = process_with_simplified_processor(text, request_id, enable_verification)
            
            if result['status'] == 'processing':
                return jsonify(result), 202
            else:
                return jsonify(result), 200
        else:
            # Use legacy processor
            logger.info(f"[{request_id}] Using legacy processor")
            
            # Legacy processing logic (existing code)
            from src.unified_input_processor import UnifiedInputProcessor
            processor = UnifiedInputProcessor()
            
            result = processor.process_any_input(
                text, 'text', request_id, 'api_endpoint'
            )
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in analyze_text: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Processing failed',
            'message': str(e)
        }), 500

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
        from rq import Queue
        from redis import Redis
        
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        redis_conn = Redis.from_url(redis_url)
        queue = Queue('casestrainer', connection=redis_conn)
        
        job = queue.fetch_job(task_id)
        
        if not job:
            return jsonify({
                'error': 'Task not found',
                'task_id': task_id
            }), 404
        
        # Force refresh job status from Redis
        job.refresh()
        
        # Debug logging
        logger.info(f"[Request {task_id}] Job status: {job.get_status()}, is_finished: {job.is_finished}, is_failed: {job.is_failed}")
        
        if job.is_finished:
            result = job.result
            logger.info(f"[Request {task_id}] Task completed successfully")
            
            # Flatten the result structure to match the sync response format
            if result and isinstance(result, dict):
                # Handle nested result structure from worker
                actual_result = result.get('result', result)  # Get nested result if it exists
                
                flattened_result = {
                    'task_id': task_id,
                    'status': 'completed',
                    'citations': actual_result.get('citations', []),
                    'clusters': actual_result.get('clusters', []),
                    'success': actual_result.get('success', True),
                    'message': actual_result.get('message', 'Task completed successfully'),
                    'metadata': actual_result.get('metadata', {}),
                    'processing_time_ms': actual_result.get('processing_time_ms', 0),
                    'document_length': actual_result.get('document_length', 0),
                    'progress_data': actual_result.get('progress_data', {}),
                    'statistics': actual_result.get('statistics', {})
                }
                logger.info(f"[Request {task_id}] Returning flattened result with {len(flattened_result.get('citations', []))} citations")
                return jsonify(flattened_result)
            else:
                return jsonify({
                    'task_id': task_id,
                    'status': 'completed',
                    'citations': [],
                    'clusters': [],
                    'success': False,
                    'message': 'Task completed but no valid result found',
                    'metadata': {}
                })
        elif job.is_failed:
            logger.error(f"[Request {task_id}] Task failed: {job.exc_info}")
            return jsonify({
                'task_id': task_id,
                'status': 'failed',
                'error': str(job.exc_info) if job.exc_info else 'Unknown error'
            }), 500
        else:
            logger.info(f"[Request {task_id}] Task still processing")
            
            # Try to get REAL progress information from progress tracker
            progress_info = {}
            progress = 10  # Default fallback
            current_step = "Initialize"
            message = "Initializing async processing..."
            
            try:
                from src.progress_tracker import get_progress_tracker
                tracker = get_progress_tracker(task_id)
                
                if tracker:
                    progress_data = tracker.get_progress_data()
                    logger.info(f"[Request {task_id}] Retrieved progress data: {progress_data}")
                    
                    if progress_data:
                        # Use real progress data from the async worker
                        progress = progress_data.get('overall_progress', 10)
                        
                        # FIXED: Use correct field names from progress tracker
                        current_step_index = progress_data.get('current_step', 0)
                        steps = progress_data.get('steps', [])
                        if current_step_index < len(steps):
                            current_step = steps[current_step_index].get('name', 'Initialize')
                        else:
                            current_step = 'Initialize'
                            
                        message = progress_data.get('current_message', 'Processing...')
                        progress_info = progress_data
                        
                        logger.info(f"[Request {task_id}] Using REAL progress: {progress}% - {current_step}: {message}")
                    else:
                        logger.warning(f"[Request {task_id}] Progress tracker exists but no progress data available")
                else:
                    logger.warning(f"[Request {task_id}] No progress tracker found for task")
                    
            except Exception as e:
                logger.error(f"[Request {task_id}] Error getting real progress data: {e}")
                
            # Fallback to job meta if available
            if hasattr(job, 'meta') and job.meta and not progress_info:
                progress_info = job.meta
                logger.info(f"[Request {task_id}] Using job meta as fallback: {progress_info}")
                
            # Only use simulated progress as last resort if no real data available
            if not progress_info or progress <= 10:
                import time
                job_age = time.time() - (job.created_at.timestamp() if job.created_at else time.time())
                
                logger.warning(f"[Request {task_id}] Falling back to simulated progress (job age: {job_age:.1f}s)")
                
                # Simulate progress phases based on elapsed time (fallback only)
                if job_age < 5:
                    progress = max(progress, 15)
                    current_step = "Extract"
                    message = "Extracting citations from document..."
                elif job_age < 10:
                    progress = max(progress, 30)
                    current_step = "Analyze"
                    message = "Analyzing citation patterns..."
                elif job_age < 15:
                    progress = max(progress, 50)
                    current_step = "Extract Names"
                    message = "Extracting case names and dates..."
                elif job_age < 20:
                    progress = max(progress, 70)
                    current_step = "Verify"
                    message = "Verifying citations with legal databases..."
                else:
                    progress = max(progress, 85)
                    current_step = "Cluster"
                    message = "Creating citation clusters..."
            
            # Calculate elapsed time
            import time
            elapsed_time = int(time.time() - (job.created_at.timestamp() if job.created_at else time.time()))
            
            return jsonify({
                'task_id': task_id,
                'status': 'processing',
                'message': message,
                'progress': progress,
                'current_step': current_step,
                'elapsed_time': elapsed_time,  # Keep for backward compatibility
                'elapsedTime': elapsed_time,   # FIXED: Add camelCase version for Vue.js
                'progress_data': {
                    'phase': current_step.lower(),
                    'progress': progress,
                    'message': message,
                    'elapsed_time': elapsed_time,
                    'elapsedTime': elapsed_time,  # FIXED: Add camelCase version
                    'real_progress': bool(progress_info),  # Indicate if using real or simulated progress
                    'full_progress_data': progress_info  # Include full progress data for debugging
                }
            })
            
    except Exception as e:
        logger.error(f"[Request {task_id}] Exception checking task status: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to check task status',
            'task_id': task_id,
            'details': str(e) if current_app.debug else None
        }), 500


@vue_api.route('/analyze/verification-status/<request_id>', methods=['GET'])
def get_verification_status(request_id):
    """
    Get the verification status for a request.
    
    Args:
        request_id: The request ID to check
        
    Returns:
        JSON response with verification status
    """
    logger.info(f"[Request {request_id}] Checking verification status")
    
    try:
        from verification_manager import VerificationManager
        
        verification_manager = VerificationManager()
        
        status = verification_manager.get_verification_status(request_id)
        
        if status:
            return jsonify(status)
        else:
            return jsonify({
                'error': 'Verification not found',
                'request_id': request_id
            }), 404
            
    except Exception as e:
        logger.error(f"[Request {request_id}] Exception checking verification status: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to check verification status',
            'request_id': request_id,
            'details': str(e) if current_app.debug else None
        }), 500


@vue_api.route('/analyze/verification-results/<request_id>', methods=['GET'])
def get_verification_results(request_id):
    """
    Get the verification results for a completed request.
    Handles both VerificationManager results and Redis-based async task results.
    
    Args:
        request_id: The request ID to get results for
        
    Returns:
        JSON response with verification results
    """
    logger.info(f"[Request {request_id}] Getting verification results")
    
    try:
        # First, try to get results from Redis (for async tasks)
        redis_results = _get_redis_task_results(request_id)
        if redis_results:
            logger.info(f"[Request {request_id}] Found results in Redis")
            return jsonify(redis_results)
        
        # Fallback to VerificationManager (for legacy verification workflow)
        try:
            from verification_manager import VerificationManager
            
            verification_manager = VerificationManager()
            results = verification_manager.get_verification_results(request_id)
            
            if results:
                logger.info(f"[Request {request_id}] Found results in VerificationManager")
                return jsonify(results)
        except Exception as vm_error:
            logger.warning(f"[Request {request_id}] VerificationManager error: {vm_error}")
        
        # No results found in either location
        return jsonify({
            'error': 'Verification results not found or not completed',
            'request_id': request_id,
            'status': 'not_found'
        }), 404
            
    except Exception as e:
        logger.error(f"[Request {request_id}] Exception getting verification results: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to get verification results',
            'request_id': request_id,
            'details': str(e) if current_app.debug else None
        }), 500

def _get_redis_task_results(task_id):
    """
    Get task results from Redis (for async processing).
    
    Args:
        task_id: The task ID to get results for
        
    Returns:
        Dict with task results or None if not found
    """
    try:
        import redis
        import json
        import os
        import pickle
        
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        redis_conn = redis.from_url(redis_url)
        
        # FIXED: Try Redis stream first (RQ stores results as streams)
        try:
            result_stream_key = f'rq:results:{task_id}'
            stream_type = redis_conn.type(result_stream_key)
            
            if stream_type == b'stream':
                logger.info(f"Found Redis stream for task {task_id}")
                # Read from the stream
                stream_data = redis_conn.xread({result_stream_key: '0'}, count=1)
                
                if stream_data:
                    # Extract the result from the stream
                    for stream_name, messages in stream_data:
                        for message_id, fields in messages:
                            # The result is typically in the 'return_value' field
                            if b'return_value' in fields:
                                result_data = fields[b'return_value']
                                try:
                                    # Try to unpickle the result
                                    result = pickle.loads(result_data)
                                    logger.info(f"[SUCCESS] Successfully retrieved task result from Redis stream: {result_stream_key}")
                                    return result
                                except Exception as pickle_error:
                                    logger.debug(f"Failed to unpickle stream result: {pickle_error}")
                                    # Try JSON as fallback
                                    try:
                                        result = json.loads(result_data.decode('utf-8'))
                                        logger.info(f"[SUCCESS] Successfully retrieved task result from Redis stream (JSON): {result_stream_key}")
                                        return result
                                    except Exception as json_error:
                                        logger.debug(f"Failed to parse stream result as JSON: {json_error}")
                                        
        except Exception as stream_error:
            logger.debug(f"Error reading Redis stream: {stream_error}")
        
        # FIX #21: Try RQ's actual result key first (pickled data)
        try:
            result_key = f'rq:results:{task_id}'
            result_data = redis_conn.get(result_key)
            if result_data:
                result = pickle.loads(result_data)
                logger.info(f"[FIX #21] Found pickled task result in Redis: {result_key}")
                return result
        except Exception as pickle_error:
            logger.debug(f"No pickled result found: {pickle_error}")
        
        # Try different Redis keys where results might be stored
        keys_to_try = [
            f'rq:job:{task_id}:result',  # Direct result key
            f'rq:job:{task_id}'          # Job hash key
        ]
        
        for key in keys_to_try:
            try:
                if key.endswith(':result'):
                    # Direct result key
                    result_data = redis_conn.get(key)
                    if result_data:
                        result = json.loads(result_data)
                        logger.info(f"Found task result in Redis key: {key}")
                        return result
                else:
                    # Job hash key
                    result_data = redis_conn.hget(key, 'result')
                    if result_data:
                        result = json.loads(result_data)
                        logger.info(f"Found task result in Redis hash: {key}")
                        return result
                        
                    # Also check job status
                    status = redis_conn.hget(key, 'status')
                    if status:
                        status_str = status.decode('utf-8') if isinstance(status, bytes) else str(status)
                        logger.info(f"Task {task_id} status: {status_str}")
                        
                        if status_str == 'failed':
                            exc_info = redis_conn.hget(key, 'exc_info')
                            error_msg = exc_info.decode('utf-8') if exc_info else 'Task failed'
                            return {
                                'status': 'failed',
                                'error': error_msg,
                                'task_id': task_id
                            }
                        elif status_str in ['queued', 'started']:
                            return {
                                'status': status_str,
                                'task_id': task_id,
                                'message': f'Task is {status_str}'
                            }
                            
            except Exception as key_error:
                logger.debug(f"Error checking Redis key {key}: {key_error}")
                continue
        
        # Check if task exists at all
        job_exists = redis_conn.exists(f'rq:job:{task_id}')
        if job_exists:
            logger.info(f"Task {task_id} exists in Redis but no result found yet")
            return {
                'status': 'running',
                'task_id': task_id,
                'message': 'Task is still processing'
            }
        else:
            logger.info(f"Task {task_id} not found in Redis")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Redis task results for {task_id}: {e}")
        return None


@vue_api.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    """Get current progress for a task."""
    try:
        from src.progress_tracker import get_progress_data
        
        progress_data = get_progress_data(task_id)
        
        if progress_data:
            return jsonify({
                'success': True,
                'progress': progress_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Task not found or progress not available'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting progress for task {task_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vue_api.route('/analyze/progress/<task_id>', methods=['GET'])
def get_analyze_progress(task_id):
    """Get current progress for an analyze task (frontend-compatible endpoint)."""
    return get_progress(task_id)

@vue_api.route('/analyze/progress-stream/<task_id>', methods=['GET'])
def analyze_progress_stream(task_id):
    """Server-Sent Events stream for real-time progress updates (frontend-compatible endpoint)."""
    return progress_stream(task_id)

@vue_api.route('/processing_progress', methods=['GET'])
def get_processing_progress():
    """Get current processing progress for both sync and async operations."""
    try:
        import time
        import json
        
        # Check if we have a request_id parameter (for async tasks)
        request_id = request.args.get('request_id')
        
        if request_id:
            # Try to get real progress data from Redis for async tasks
            try:
                from redis import Redis
                from src.config import REDIS_URL
                
                redis_conn = Redis.from_url(REDIS_URL)
                
                # Check for progress data in Redis
                progress_key = f"progress:{request_id}"
                progress_data_str = redis_conn.get(progress_key)
                
                if progress_data_str:
                    progress_data = json.loads(progress_data_str)
                    logger.info(f"[SUCCESS] Found real progress data for {request_id}: {progress_data}")
                    
                    return jsonify({
                        'status': progress_data.get('status', 'processing'),
                        'current_step': progress_data.get('status', 'Processing...'),
                        'progress': progress_data.get('progress', 0),
                        'progress_percent': progress_data.get('progress', 0),  # Frontend expects this field
                        'total_progress': progress_data.get('progress', 0),
                        'current_message': progress_data.get('message', 'Processing...'),
                        'message': progress_data.get('message', 'Processing...'),
                        'elapsed_time': 0,  # Will be calculated by frontend
                        'elapsedTime': 0,
                        'is_complete': progress_data.get('progress', 0) >= 100,
                        'processing_mode': 'async',
                        'taskId': request_id,
                        'stepProgress': progress_data.get('progress', 0),
                        'real_progress': True  # Flag to indicate this is real progress data
                    })
                else:
                    logger.warning(f"No progress data found in Redis for {request_id}")
                    
            except Exception as e:
                logger.warning(f"Failed to get Redis progress data for {request_id}: {e}")
        
        # Fallback to simulated progress for sync operations or when no Redis data
        current_time = time.time()
        
        # Use a simple time-based progress simulation for sync processing
        # This gives the user visual feedback during the brief sync processing time
        progress_steps = [
            {'step': 'Initializing...', 'progress': 10, 'message': 'Starting document analysis'},
            {'step': 'Extract', 'progress': 25, 'message': 'Extracting citations from document'},
            {'step': 'Analyze', 'progress': 50, 'message': 'Analyzing citation formats'},
            {'step': 'Extract Names', 'progress': 70, 'message': 'Extracting case names'},
            {'step': 'Verify', 'progress': 85, 'message': 'Verifying citations'},
            {'step': 'Cluster', 'progress': 95, 'message': 'Clustering related citations'}
        ]
        
        # Cycle through steps based on time (change every 200ms)
        step_index = int((current_time * 5) % len(progress_steps))
        current_step_data = progress_steps[step_index]
        
        # FIXED: Add required fields for Vue.js progress component
        elapsed_time = min(5, int((current_time * 2) % 10))
        estimated_total = 8  # Estimate 8 seconds total for sync processing
        
        return jsonify({
            'status': 'processing',
            'current_step': current_step_data['step'],
            'progress': current_step_data['progress'],
            'progress_percent': current_step_data['progress'],  # Frontend expects this field
            'total_progress': current_step_data['progress'],
            'current_message': current_step_data['message'],
            'message': current_step_data['message'],
            'elapsed_time': elapsed_time,  # Keep for backward compatibility
            'elapsedTime': elapsed_time,   # FIXED: Add camelCase version for Vue.js
            'is_complete': False,
            'processing_mode': 'sync',
            # REQUIRED FIELDS for Vue.js progress component:
            'startTime': (current_time - elapsed_time) * 1000,  # Convert to milliseconds
            'estimatedTotalTime': estimated_total,  # Must be > 0 for progress bar to show
            'isActive': True,
            'taskId': request_id or 'sync-processing',
            'stepProgress': current_step_data['progress'],
            'processingSteps': [
                {'step': step['step'], 'completed': step['progress'] <= current_step_data['progress']} 
                for step in progress_steps
            ],
            'real_progress': False  # Flag to indicate this is simulated progress data
        })
    except Exception as e:
        logger.error(f"Error getting processing progress: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'is_complete': True
        }), 500

@vue_api.route('/progress-stream/<task_id>', methods=['GET'])
def progress_stream(task_id):
    """Server-Sent Events stream for real-time progress updates."""
    try:
        from src.progress_tracker import get_progress_tracker
        import json
        
        def generate_progress_events():
            """Generate Server-Sent Events for progress updates."""
            tracker = get_progress_tracker(task_id)
            
            if not tracker:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                return
            
            # Send initial progress
            initial_data = tracker.get_progress_data()
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            # Set up callback for real-time updates
            update_queue = []
            
            def progress_callback(progress_data):
                update_queue.append(progress_data)
            
            tracker.add_update_callback(progress_callback)
            
            # Stream updates until completion
            last_update_time = time.time()
            while tracker.status not in ['completed', 'failed']:
                # Send any queued updates
                while update_queue:
                    update_data = update_queue.pop(0)
                    yield f"data: {json.dumps(update_data)}\n\n"
                
                # Send periodic heartbeat
                current_time = time.time()
                if current_time - last_update_time > 5:  # Every 5 seconds
                    heartbeat_data = tracker.get_progress_data()
                    yield f"data: {json.dumps(heartbeat_data)}\n\n"
                    last_update_time = current_time
                
                time.sleep(0.5)  # Check for updates every 500ms
            
            # Send final update
            final_data = tracker.get_progress_data()
            yield f"data: {json.dumps(final_data)}\n\n"
        
        return Response(
            generate_progress_events(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in progress stream for task {task_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vue_api.route('/analyze/verification-stream/<request_id>', methods=['GET'])
def verification_stream(request_id):
    """
    Server-Sent Events stream for real-time verification updates.
    
    Args:
        request_id: The request ID to stream updates for
        
    Returns:
        SSE stream of verification updates
    """
    logger.info(f"[Request {request_id}] Starting verification stream")
    
    def generate_verification_events():
        """Generator for SSE verification events"""
        try:
            from verification_manager import VerificationManager
            
            verification_manager = VerificationManager()
            
            yield f"data: {json.dumps({'type': 'status', 'request_id': request_id, 'message': 'Starting verification stream'})}\n\n"
            
            last_status = None
            max_wait_time = 300  # 5 minutes timeout
            waited_time = 0
            
            while waited_time < max_wait_time:
                try:
                    status = verification_manager.get_verification_status(request_id)
                    
                    if status and status != last_status:
                        yield f"data: {json.dumps({'type': 'status_update', 'request_id': request_id, 'status': status})}\n\n"
                        last_status = status
                        
                        if status.get('status') == 'completed':
                            results = verification_manager.get_verification_results(request_id)
                            if results:
                                yield f"data: {json.dumps({'type': 'verification_complete', 'request_id': request_id, 'results': results})}\n\n"
                            break
                        elif status.get('status') == 'failed':
                            yield f"data: {json.dumps({'type': 'verification_failed', 'request_id': request_id, 'error': status.get('error_message', 'Unknown error')})}\n\n"
                            break
                    
                    time.sleep(1)
                    waited_time += 1
                    
                except Exception as e:
                    logger.error(f"Error in verification stream for {request_id}: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'request_id': request_id, 'error': str(e)})}\n\n"
                    break
            
            yield f"data: {json.dumps({'type': 'stream_complete', 'request_id': request_id})}\n\n"
            
        except Exception as e:
            logger.error(f"Error generating verification events for {request_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'request_id': request_id, 'error': str(e)})}\n\n"
    
    return Response(
        generate_verification_events(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )


if __name__ == '__main__':
    pass


