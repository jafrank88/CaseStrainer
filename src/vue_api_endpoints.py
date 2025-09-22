"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
import uuid
import logging
import time
import json
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
    request_id = str(uuid.uuid4())
    logger.info(f"[Request {request_id}] ===== Starting analyze request =====")
    logger.info(f"[Request {request_id}] Method: {request.method}")
    logger.info(f"[Request {request_id}] Content-Type: {request.content_type}")
    
    try:
        data = None
        if request.content_type and 'application/json' in request.content_type:
            logger.info(f"[Request {request_id}] Attempting to parse JSON data")
            try:
                data = request.get_json()
                logger.info(f"[Request {request_id}] JSON parsing successful: {data}")
            except Exception as e:
                logger.error(f"[Request {request_id}] JSON parsing failed: {str(e)}")
                return jsonify({
                    'error': 'Invalid JSON data',
                    'request_id': request_id,
                    'details': str(e)
                }), 400
        else:
            text_content = request.form.get('text', '')
            url_content = request.form.get('url', '')
            if text_content is None:
                text_content = ''
            if url_content is None:
                url_content = ''
            
            data = {
                'text': text_content,
                'url': url_content,
                'type': request.form.get('type', 'text')
            }
        
        # Check for file upload first
        has_file = request.files and 'file' in request.files and request.files['file'].filename
        
        # Validate that we have either text, url, or file data
        has_text = data and 'text' in data and data['text']
        has_url = data and 'url' in data and data['url']
        
        if not data and not has_file:
            return jsonify({
                'error': 'Missing or invalid request data - must provide either text, url, or file',
                'request_id': request_id,
                'content_type': request.content_type
            }), 400
            
        # Determine input type and data
        if has_file:
            # Process file upload
            file = request.files['file']
            filename = file.filename.lower() if file.filename else ''
            
            if filename.endswith('.pdf'):
                try:
                    import PyPDF2
                    import io
                    
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                    text_parts = []
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    input_data = '\n\n'.join(text_parts)
                    input_type = 'text'  # Use 'text' since we've already extracted the content
                    logger.info(f"[Request {request_id}] Starting analysis of PDF file: {file.filename} ({len(input_data)} chars)")
                except Exception as e:
                    logger.error(f"Error reading PDF: {str(e)}")
                    if "password" in str(e).lower():
                        return jsonify({'error': 'This PDF appears to be password-protected. Please provide an unprotected PDF file.'}), 400
                    elif "corrupt" in str(e).lower() or "invalid" in str(e).lower():
                        return jsonify({'error': 'The PDF file appears to be corrupted or invalid. Please try a different file.'}), 400
                    else:
                        return jsonify({'error': f'Could not process the PDF file: {str(e)}. Please ensure it is a valid PDF document.'}), 400
            else:
                try:
                    input_data = file.read().decode('utf-8')
                    input_type = 'text'  # Use 'text' since we've already extracted the content
                    logger.info(f"[Request {request_id}] Starting analysis of text file: {file.filename} ({len(input_data)} chars)")
                except UnicodeDecodeError:
                    return jsonify({'error': 'Invalid file encoding. Please use UTF-8 encoded text files.'}), 400
        elif has_url:
            # Extract text from URL first, then process as text
            url = data['url']
            logger.info(f"[Request {request_id}] Extracting content from URL: {url}")
            
            # Basic URL validation
            if not url or not isinstance(url, str) or not url.strip():
                return jsonify({'error': 'Please provide a valid URL.'}), 400
            
            if not url.startswith(('http://', 'https://')):
                return jsonify({'error': 'Please provide a complete URL starting with http:// or https://'}), 400
            
            try:
                from src.progress_manager import fetch_url_content
                input_data = fetch_url_content(url)
                input_type = 'text'  # Convert to text processing
                logger.info(f"[Request {request_id}] Extracted {len(input_data)} characters from URL, processing as text")
            except Exception as e:
                logger.error(f"[Request {request_id}] URL extraction failed: {e}")
                return jsonify({'error': f'{str(e)}'}), 400
        else:
            input_data = data['text']
            input_type = 'text'
            text_length = len(input_data) if input_data else 0
            logger.info(f"[Request {request_id}] Starting analysis of text (length: {text_length})")
        
        try:
            import time
            start_time = time.time()
            
            # Create progress tracker for this request
            from src.progress_tracker import create_progress_tracker
            progress_tracker = create_progress_tracker(request_id)
            logger.info(f"[Request {request_id}] Created progress tracker: {progress_tracker.task_id}")
            
            # Start initial step
            progress_tracker.start_step(0, 'Initializing processing...')
            logger.info(f"[Request {request_id}] Started initial step, progress: {progress_tracker.overall_progress}%")
            
            # Check if this should be processed immediately (sync) or queued (async)
            from src.api.services.citation_service import CitationService
            citation_service = CitationService()
            
            input_data_for_check = {'type': input_type}
            if input_type == 'text':
                input_data_for_check['text'] = input_data
            
            should_process_immediately = citation_service.should_process_immediately(input_data_for_check)
            
            if should_process_immediately:
                # Sync processing with real-time progress
                logger.info(f"[Request {request_id}] Processing immediately (sync) with progress tracking")
                
                progress_tracker.complete_step(0, 'Initialization complete')
                progress_tracker.start_step(1, 'Extracting citations...')
                
                from src.unified_input_processor import UnifiedInputProcessor
                processor = UnifiedInputProcessor()
                
                # Update progress during processing
                progress_tracker.update_step(1, 25, 'Starting citation extraction...')
                
                result = processor.process_any_input(
                    input_data=input_data,
                    input_type=input_type,
                    request_id=request_id
                )
                
                progress_tracker.update_step(1, 90, 'Citation extraction nearly complete...')
                
                # Update progress based on result
                if result.get('success'):
                    progress_tracker.complete_step(1, 'Citation extraction completed')
                    progress_tracker.start_step(2, 'Analyzing citations...')
                    progress_tracker.update_step(2, 50, 'Normalizing citation formats...')
                    progress_tracker.complete_step(2, 'Analysis completed')
                    
                    progress_tracker.start_step(3, 'Extracting case names...')
                    progress_tracker.update_step(3, 75, 'Processing case name patterns...')
                    progress_tracker.complete_step(3, 'Name extraction completed')
                    
                    progress_tracker.start_step(4, 'Clustering parallel citations...')
                    progress_tracker.update_step(4, 60, 'Grouping related citations...')
                    progress_tracker.complete_step(4, 'Clustering completed')
                    
                    progress_tracker.start_step(5, 'Verifying citations...')
                    progress_tracker.update_step(5, 80, 'Checking citation validity...')
                    progress_tracker.complete_step(5, 'Verification completed')
                    
                    progress_tracker.complete_all('Immediate processing completed successfully')
                else:
                    progress_tracker.fail_step(1, 'Processing failed')
                
                # Add progress data to result
                result['progress_data'] = progress_tracker.get_progress_data()
                
                # Add processing mode for frontend
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['processing_mode'] = 'immediate'
                
            else:
                # Async processing - return task info immediately
                logger.info(f"[Request {request_id}] Queuing for async processing with progress tracking")
                
                progress_tracker.update_step(0, 50, 'Queuing for background processing...')
                
                from src.unified_input_processor import UnifiedInputProcessor
                processor = UnifiedInputProcessor()
                
                result = processor.process_any_input(
                    input_data=input_data,
                    input_type=input_type,
                    request_id=request_id
                )
                
                # Check if we got a sync fallback result or actual async task
                processing_mode = result.get('metadata', {}).get('processing_mode', '')
                
                if 'task_id' in result:
                    # True async processing
                    task_id = result.get('task_id')
                    progress_tracker.complete_step(0, 'Queued for background processing')
                    
                    result['progress_data'] = progress_tracker.get_progress_data()
                    result['progress_endpoint'] = f'/casestrainer/api/analyze/progress/{task_id}'
                    result['progress_stream'] = f'/casestrainer/api/analyze/progress-stream/{task_id}'
                    
                elif processing_mode == 'sync_fallback':
                    # Sync fallback - treat like immediate processing
                    logger.info(f"[Request {request_id}] Sync fallback completed, treating as immediate processing")
                    
                    if result.get('success'):
                        progress_tracker.complete_step(0, 'Initialization complete')
                        progress_tracker.complete_step(1, 'Citation extraction completed (sync fallback)')
                        progress_tracker.complete_step(2, 'Analysis completed')
                        progress_tracker.complete_step(3, 'Name extraction completed')
                        progress_tracker.complete_step(4, 'Clustering completed')
                        progress_tracker.complete_step(5, 'Verification completed')
                        progress_tracker.complete_all('Sync fallback processing completed successfully')
                    else:
                        progress_tracker.fail_step(1, 'Sync fallback processing failed')
                    
                    result['progress_data'] = progress_tracker.get_progress_data()
                    
                else:
                    # Failed to queue and no fallback
                    progress_tracker.fail_step(0, 'Failed to queue for processing')
                    result['progress_data'] = progress_tracker.get_progress_data()
            
            process_time = time.time() - start_time
            
            if not isinstance(result, dict):
                result = {}
            result['request_id'] = request_id
            result['processing_time'] = process_time
            
            try:
                from src.data_separation_validator import validate_data_separation
                
                citations = result.get('citations', [])
                if citations:
                    separation_report = validate_data_separation(citations)
                    if not separation_report['is_valid']:
                        logger.warning(f"[Request {request_id}] Data separation issues detected:")
                        for warning in separation_report['warnings']:
                            logger.warning(f"  • {warning}")
                        
                        result['data_separation_validation'] = {
                            'contamination_detected': True,
                            'contamination_rate': separation_report['contamination_rate'],
                            'separation_health': separation_report['separation_health']
                        }
                    else:
                        logger.info(f"[Request {request_id}] Data separation validation passed")
            except Exception as e:
                logger.warning(f"[Request {request_id}] Data separation validation failed: {e}")
            
            # Calculate document length based on input type
            if has_url:
                # For URLs, use the actual content length from metadata, fallback to URL length
                document_length = result.get('metadata', {}).get('content_length', len(input_data))
            else:
                document_length = len(input_data)  # Text length
            
            # Flatten the result structure to avoid nested result.result
            restructured_result = {
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),
                'success': result.get('success', True),
                'message': result.get('message', 'Analysis completed'),
                'metadata': result.get('metadata', {}),
                'request_id': request_id,
                'processing_time_ms': int(process_time * 1000),
                'document_length': document_length,
                'progress_data': result.get('progress_data', {})
            }
            
            logger.info(f"[Request {request_id}] Request completed successfully in {0}ms")
            return jsonify(restructured_result)
            
        except Exception as e:
            error_msg = f"[Request {request_id}] Exception in text processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': 'Failed to process text',
                'request_id': request_id,
                'details': str(e) if current_app.debug else None
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
        
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        redis_conn = redis.from_url(redis_url)
        
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
    """Get current processing progress for sync operations."""
    try:
        import time
        
        # Get current time to simulate progress
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
            'total_progress': current_step_data['progress'],
            'message': current_step_data['message'],
            'elapsed_time': elapsed_time,  # Keep for backward compatibility
            'elapsedTime': elapsed_time,   # FIXED: Add camelCase version for Vue.js
            'is_complete': False,
            'processing_mode': 'sync',
            # REQUIRED FIELDS for Vue.js progress component:
            'startTime': (current_time - elapsed_time) * 1000,  # Convert to milliseconds
            'estimatedTotalTime': estimated_total,  # Must be > 0 for progress bar to show
            'isActive': True,
            'taskId': 'sync-processing',
            'stepProgress': current_step_data['progress'],
            'processingSteps': [
                {'step': step['step'], 'completed': step['progress'] <= current_step_data['progress']} 
                for step in progress_steps
            ]
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


