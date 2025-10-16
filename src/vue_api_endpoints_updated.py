"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
import uuid
import logging
import traceback
import time
import json
import copy
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List, Union
from flask import Blueprint, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
from src.api.services.citation_service import CitationService
from src.database_manager import get_database_manager
from src.data_separation_validator import validate_data_separation, enforce_data_separation, restore_extracted_name_if_contaminated

from src.rq_worker import process_citation_task_direct
# UnifiedInputProcessor is imported locally where needed to avoid startup issues

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Simple progress tracking for real-time updates."""
    
    def __init__(self):
        self.progress_store = {}
        self.progress_lock = {}
    
    def start_progress(self, request_id: str, steps: List[Dict[str, Any]]):
        """Start progress tracking for a request."""
        self.progress_store[request_id] = {
            'steps': steps,
            'current_step': 0,
            'current_progress': 0,
            'start_time': time.time(),
            'status': 'active'
        }
        self.progress_lock[request_id] = False
    
    def update_progress(self, request_id: str, step_index: int, progress: int, message: str = ""):
        """Update progress for a specific step."""
        if request_id in self.progress_store:
            self.progress_store[request_id]['current_step'] = step_index
            self.progress_store[request_id]['current_progress'] = progress
            if message:
                self.progress_store[request_id]['steps'][step_index]['message'] = message
    
    def get_progress(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a request."""
        return self.progress_store.get(request_id)
    
    def complete_progress(self, request_id: str):
        """Mark progress as completed."""
        if request_id in self.progress_store:
            self.progress_store[request_id]['status'] = 'completed'
            self.progress_store[request_id]['current_progress'] = 100
    
    def cleanup_progress(self, request_id: str):
        """Clean up progress data for a request."""
        if request_id in self.progress_store:
            del self.progress_store[request_id]
        if request_id in self.progress_lock:
            del self.progress_lock[request_id]

progress_tracker = ProgressTracker()

vue_api = Blueprint('vue_api', __name__)

citation_service = CitationService()


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
        try:
            version_path = os.path.join('/app', 'VERSION')
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

        try:
            from api.services.citation_service import CitationService
            health_data['components']['citation_processor'] = 'healthy'
        except Exception as e:
            health_data['status'] = 'degraded'
            health_data['components']['citation_processor'] = f'error: {str(e)}'
            logger.error(f"Citation processor check failed: {e}")

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
def analyze():
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
    # Generate initial request_id (will be replaced if client provides one)
    request_id = str(uuid.uuid4())
    
    if _is_test_environment_request(request):
        error_msg = 'Test environment detected. Please use the production interface.'
        logger.warning(f"[Request {request_id}] Test environment request detected and rejected")
        return jsonify({
            'error': error_msg,
            'citations': [],
            'clusters': [],
            'request_id': request_id,
            'success': False,
            'metadata': {
                'rejected_reason': 'test_environment_detected',
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'referer': request.headers.get('Referer', 'unknown')
            }
        }), 403
    
    
    logger.info(f"=== ANALYZE ENDPOINT CALLED [Request ID: {request_id}] ===")
    logger.info(f"[Request {request_id}] Method: {request.method}")
    logger.info(f"[Request {request_id}] URL: {request.url}")
    logger.info(f"[Request {request_id}] Content-Type: {request.content_type}")
    
    start_time = time.time()
    metadata = {
        'request_id': request_id,
        'endpoint': '/analyze',
        'timestamp': datetime.utcnow().isoformat(),
        'processing_mode': 'unknown',
        'input_type': 'unknown',
        'input_size': len(request.data) if request.data else 0,
        'content_type': request.content_type or 'not_specified'
    }
    
    try:
        if True:

            pass  # Empty block

        
            pass  # Empty block

        
        if request.files:
            logger.info(f"[Request {request_id}] Files received: {[f.filename for f in request.files.values()]}")
        
        service = CitationService()
        
        progress_steps = [
            {"name": "Initializing...", "progress": 0, "message": "Starting unified processing..."},
            {"name": "Extract", "progress": 20, "message": "Extracting citations..."},
            {"name": "Analyze", "progress": 40, "message": "Citations analyzed and normalized..."},
            {"name": "Extract Names", "progress": 60, "message": "Case names and years extracted..."},
            {"name": "Cluster", "progress": 80, "message": "Citations clustered successfully..."},
            {"name": "Verify", "progress": 90, "message": "Verification completed..."}
        ]
        progress_tracker.start_progress(request_id, progress_steps)
        
        json_data = None
        if request.data:
            try:
                json_data = request.get_json(silent=True, force=True)
                if json_data:
                    # Check if client provided a request_id for progress tracking
                    if 'client_request_id' in json_data:
                        request_id = json_data['client_request_id']
                        logger.info(f"[Request {request_id}] Using client-provided request_id for progress tracking")
                    
                    sanitized_data = {}
                    for k, v in json_data.items():
                        if isinstance(v, str) and len(v) > 100:
                            sanitized_data[k] = f"[content of length {len(v)}]"
                        else:
                            sanitized_data[k] = v
            except Exception as e:
                logger.warning(f"[Request {request_id}] Failed to parse JSON data: {str(e)}")
        
        input_data = None
        input_type = None
        
        if 'file' in request.files and request.files['file'].filename:
            logger.info(f"[Request {request_id}] Processing file upload")
            logger.info(f"[Request {request_id}] File details: name={request.files['file'].filename}, size={request.files['file'].content_length}, type={request.files['file'].content_type}")
            
            file_obj = request.files['file']
            input_data = {
                'type': 'file',
                'file': file_obj,
                'filename': file_obj.filename,
                'content_type': file_obj.content_type or 'application/octet-stream',
                'file_size': getattr(file_obj, 'content_length', 0) or 0
            }
            input_type = 'file'
            metadata.update({
                'input_type': 'file',
                'filename': file_obj.filename,
                'content_type': file_obj.content_type or 'application/octet-stream',
                'file_size': getattr(file_obj, 'content_length', 0) or 0
            })
        
        elif request.is_json or json_data:
            logger.info(f"[Request {request_id}] Processing JSON input")
            data = json_data or request.get_json()
            
            if data and isinstance(data, dict):
                if data.get('type') == 'url' and data.get('url'):
                    input_data = data['url']
                    input_type = 'url'
                    metadata.update({
                        'input_type': 'url',
                        'url': data['url']
                    })
                elif data.get('type') == 'text' and data.get('text'):
                    text_data = data['text']
                    input_dict = {'type': 'text', 'text': text_data}
                    
                    if service.should_process_immediately(input_dict):
                        logger.info(f"[Request {request_id}] Processing JSON text immediately (short text)")
                        try:
                            result = service.process_immediately(input_dict)
                            
                            result['request_id'] = request_id
                            if 'metadata' not in result:
                                result['metadata'] = {}
                            result['metadata'].update({
                                'processing_mode': 'immediate',
                                'input_type': 'text',
                                'text_length': len(text_data)
                            })
                            
                            return _format_response(result, request_id, metadata, start_time)
                        except Exception as e:
                            logger.error(f"[Request {request_id}] Error in immediate processing: {str(e)}", exc_info=True)
                    
                    input_data = text_data
                    input_type = 'text'
                    metadata.update({
                        'input_type': 'text',
                        'text_length': len(text_data)
                    })
                elif data.get('text'):  # Legacy format
                    text_data = data['text']
                    input_dict = {'type': 'text', 'text': text_data}
                    
                    if service.should_process_immediately(input_dict):
                        logger.info(f"[Request {request_id}] Processing legacy JSON text immediately (short text)")
                        try:
                            result = service.process_immediately(input_dict)
                            
                            result['request_id'] = request_id
                            if 'metadata' not in result:
                                result['metadata'] = {}
                            result['metadata'].update({
                                'processing_mode': 'immediate',
                                'input_type': 'text',
                                'text_length': len(text_data)
                            })
                            
                            return _format_response(result, request_id, metadata, start_time)
                        except Exception as e:
                            logger.error(f"[Request {request_id}] Error in immediate processing: {str(e)}", exc_info=True)
                    
                    input_data = text_data
                    input_type = 'text'
                    metadata.update({
                        'input_type': 'text',
                        'text_length': len(text_data)
                    })
        
        elif request.form:
            logger.info(f"[Request {request_id}] Processing form input")
            if 'url' in request.form:
                input_data = request.form['url']
                input_type = 'url'
                metadata.update({
                    'input_type': 'url',
                    'url': request.form['url']
                })
            elif 'text' in request.form:
                input_data = request.form['text']
                input_type = 'text'
                metadata.update({
                    'input_type': 'text',
                    'text_length': len(request.form['text'])
                })
        
        elif request.data and isinstance(request.data, (str, bytes)):
            try:
                url = request.data.decode('utf-8').strip() if isinstance(request.data, bytes) else request.data.strip()
                if url.startswith(('http://', 'https://')):
                    logger.info(f"[Request {request_id}] Processing raw URL input")
                    input_data = url
                    input_type = 'url'
                    metadata.update({
                        'input_type': 'url',
                        'url': url
                    })
            except Exception as e:
                logger.warning(f"[Request {request_id}] Failed to process raw data as URL: {str(e)}")
        
        if input_data is not None and input_type is not None:
            logger.info(f"[Request {request_id}] Processing {input_type} input")
            
            try:
                from src.unified_input_processor import UnifiedInputProcessor
                
                progress_data = {
                    'current_step': 0,
                    'total_steps': 5,
                    'current_message': 'Initializing...',
                    'start_time': time.time(),
                    'steps': [
                        {'name': 'Initializing...', 'progress': 0, 'status': 'pending'},
                        {'name': 'Extract', 'progress': 0, 'status': 'pending'},
                        {'name': 'Analyze', 'progress': 0, 'status': 'pending'},
                        {'name': 'Extract Names', 'progress': 0, 'status': 'pending'},
                        {'name': 'Cluster', 'progress': 0, 'status': 'pending'},
                        {'name': 'Verify', 'progress': 0, 'status': 'pending'}
                    ]
                }
                
                def progress_callback(progress: int, step: str, message: str):
                    """Progress callback to update frontend progress."""
                    try:
                        for i, step_info in enumerate(progress_data['steps']):
                            if step_info['name'] == step:
                                step_info['progress'] = progress
                                step_info['status'] = 'completed' if progress == 100 else 'in-progress'
                                step_info['message'] = message
                                break
                        
                        progress_data['current_step'] = progress
                        progress_data['current_message'] = message
                        
                        logger.info(f"[Request {request_id}] Progress: {progress}% - {step}: {message}")
                        
                    except Exception as e:
                        logger.warning(f"[Request {request_id}] Progress callback error: {e}")
                
                processor = UnifiedInputProcessor()
                
                logger.info(f"[Request {request_id}] Using UnifiedInputProcessor for {input_type} input")
                
                progress_tracker.update_progress(request_id, 0, 20, "Started processing")
                time.sleep(0.1)  # Small delay for frontend to see progress
                
                result = processor.process_any_input(input_data, input_type, request_id)
                
                progress_tracker.update_progress(request_id, 1, 40, "Citations extracted successfully")
                time.sleep(0.1)  # Small delay for frontend to see progress
                
                progress_tracker.update_progress(request_id, 2, 60, "Citations normalized locally")
                time.sleep(0.1)  # Small delay for frontend to see progress
                
                progress_tracker.update_progress(request_id, 3, 80, "Case names and years extracted")
                time.sleep(0.1)  # Small delay for frontend to see progress
                
                progress_tracker.update_progress(request_id, 4, 90, "Citations clustered successfully")
                time.sleep(0.1)  # Small delay for frontend to see progress
                
                progress_tracker.complete_progress(request_id)
                
                if result.get('success') is False or result.get('error'):
                    return _format_error(
                        result.get('error', 'Unknown error'),
                        status_code=400,
                        request_id=request_id,
                        metadata={
                            **metadata,
                            **result.get('metadata', {})
                        }
                    )
                
                result['request_id'] = request_id
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata'].update({
                    'processing_mode': result.get('processing_mode', 'enhanced_sync'),
                    'input_type': input_type,
                    'text_length': len(str(input_data)) if hasattr(input_data, '__len__') else 0,
                    'async_verification_queued': result.get('async_verification_queued', False),
                    'progress_data': {
                        'current_step': 100,
                        'total_steps': 5,
                        'current_message': 'Processing completed successfully',
                        'start_time': start_time,
                        'steps': [
                            {'name': 'Initializing...', 'progress': 100, 'status': 'completed', 'message': 'Started enhanced sync processing'},
                            {'name': 'Extract', 'progress': 100, 'status': 'completed', 'message': 'Citations extracted successfully'},
                            {'name': 'Analyze', 'progress': 100, 'status': 'completed', 'message': 'Citations normalized locally'},
                            {'name': 'Extract Names', 'progress': 100, 'status': 'completed', 'message': 'Case names and years extracted'},
                            {'name': 'Cluster', 'progress': 100, 'status': 'completed', 'message': 'Citations clustered successfully'},
                            {'name': 'Verify', 'progress': 100, 'status': 'completed', 'message': 'Results prepared successfully'}
                        ]
                    }
                })
                
                if result.get('async_verification_queued') and result.get('verification_status', {}).get('verification_queued'):
                    verification_job_id = result['verification_status'].get('verification_job_id', request_id)
                    return jsonify({
                        'status': 'processing',
                        'task_id': verification_job_id,
                        'message': 'Analysis completed, verification in progress',
                        'citations': result.get('citations', []),
                        'clusters': result.get('clusters', []),
                        'request_id': request_id,
                        'processing_mode': 'enhanced_sync_with_async_verification',
                        'async_verification_queued': True,
                        'verification_job_id': verification_job_id,
                        'progress_data': {
                            'current_step': 90,
                            'total_steps': 6,
                            'current_message': 'Verification in progress',
                            'start_time': start_time,
                            'steps': [
                                {'name': 'Initializing...', 'progress': 100, 'status': 'completed', 'message': 'Started enhanced sync processing'},
                                {'name': 'Extract', 'progress': 100, 'status': 'completed', 'message': 'Citations extracted successfully'},
                                {'name': 'Analyze', 'progress': 100, 'status': 'completed', 'message': 'Citations normalized locally'},
                                {'name': 'Extract Names', 'progress': 100, 'status': 'completed', 'message': 'Case names and years extracted'},
                                {'name': 'Cluster', 'progress': 100, 'status': 'completed', 'message': 'Citations clustered successfully'},
                                {'name': 'Verify', 'progress': 90, 'status': 'in-progress', 'message': 'Verification queued for background processing'}
                            ]
                        }
                    })
                
                return _format_response(result, request_id, metadata, start_time)
                
            except Exception as e:
                error_msg = f"Error in unified processor: {str(e)}"
                logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
                return _format_error(
                    error_msg,
                    status_code=500,
                    request_id=request_id,
                    metadata={
                        **metadata,
                        'error_type': 'unified_processor_error',
                        'error_details': str(e)
                    }
                )
        
        content_type = request.content_type or 'not specified'
        error_msg = (
            f"Invalid or missing input. No file, JSON, or form data found. "
            f"Content-Type: {content_type}, Data length: {len(request.data) if request.data else 0}"
        )
        logger.error(f"[Request {request_id}] {error_msg}")
        
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
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    if not isinstance(result, dict):
        result = {}
    
    metadata.update({
        'processing_time_ms': processing_time_ms,
        'processing_mode': result.get('metadata', {}).get('processing_mode', metadata.get('processing_mode', 'unknown')),
        'status': result.get('status', 'completed'),
        'success': result.get('success', True)
    })
    
    response_data = {
        'result': {
            'citations': result.get('citations', []),
            'clusters': result.get('clusters', []),
            'statistics': result.get('statistics', {}),
        },
        'request_id': request_id,
        'success': result.get('success', True),
        'status': result.get('status', 'completed'),  # Always include status
        'metadata': {**result.get('metadata', {}), **metadata}
    }
    
    if 'progress_data' in result:
        response_data['metadata']['progress_data'] = result['progress_data']
    
    if 'task_id' in result:
        # Add task_id to both top level AND inside result for frontend compatibility
        response_data.update({
            'task_id': result['task_id'],
            'status': result.get('status', 'processing'),
            'message': result.get('message', 'Request is being processed')
        })
        response_data['result']['task_id'] = result['task_id']  # Also add inside result
    
    for key in ['message', 'warnings', 'debug', 'verification_status', 'async_verification_queued']:
        if key in result and key not in response_data:
            response_data[key] = result[key]
    
    # Perform data integrity validation before returning response
    validation_errors = _validate_api_response_data(response_data)
    if validation_errors:
        logger.error(f"[Request {request_id}] Data integrity validation failed: {validation_errors}")
        # Log the validation errors but don't fail the request - let frontend handle it
        response_data['metadata']['validation_warnings'] = validation_errors
    
    log_data = copy.deepcopy(response_data)
    
    def safe_serialize(obj):
        """Safely serialize objects to JSON, handling custom objects"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, (list, tuple)):
            return [safe_serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: safe_serialize(v) for k, v in obj.items()}
        return str(obj)  # Fallback to string representation
    
    if 'result' in log_data:
        result_data = log_data['result']
        if 'citations' in result_data:
            if len(result_data['citations']) > 5:
                result_data['citations'] = f"[list of {len(result_data['citations'])} citations]"
            else:
                result_data['citations'] = safe_serialize(result_data['citations'])
                
        if 'clusters' in result_data:
            if len(result_data['clusters']) > 3:
                result_data['clusters'] = f"[list of {len(result_data['clusters'])} clusters]"
            else:
                result_data['clusters'] = safe_serialize(result_data['clusters'])
    
    logger.info(f"[Request {request_id}] Request completed successfully in {processing_time_ms}ms")

    try:
        os.makedirs('/app/logs', exist_ok=True)
        
        serializable_data = safe_serialize(response_data)
        
        with open('/app/logs/frontend_api_results.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(serializable_data, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"Failed to write API response to log file: {e}")
    
    try:
        json.dumps(response_data)
    except (TypeError, ValueError) as e:
        logger.error(f"Response contains non-serializable data: {e}")
        try:
            if 'result' in response_data and response_data['result']:
                if 'citations' in response_data['result']:
                    response_data['result']['citations'] = [
                        cit.to_dict() if hasattr(cit, 'to_dict') else safe_serialize(cit)
                        for cit in response_data['result']['citations']
                    ]
                if 'clusters' in response_data['result']:
                    response_data['result']['clusters'] = [
                        {k: (v.to_dict() if hasattr(v, 'to_dict') else safe_serialize(v)) 
                         for k, v in cluster.items()}
                        for cluster in response_data['result']['clusters']
                    ]
            
            json.dumps(response_data)
        except (TypeError, ValueError) as e2:
            logger.error(f"Failed to fix non-serializable data: {e2}")
            response_data = safe_serialize(response_data)

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
    
    if 'request_id' not in error_data['metadata'] and request_id:
        error_data['metadata']['request_id'] = request_id
    
    if 'status' not in error_data['metadata']:
        error_data['metadata']['status'] = 'error'
    
    logger.error(f"[Request {request_id or 'unknown'}] Error: {message}")
    if details and details != message:
        logger.error(f"[Request {request_id or 'unknown'}] Details: {details}")
    
    return jsonify(error_data), status_code

@vue_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Check the status of a queued task"""
    logger.info(f"Checking status for task_id: {task_id}")
    
    try:
        from rq import Queue, Worker
        from redis import Connection
        from redis import Redis
        
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
        
        redis_conn = Redis.from_url(redis_url, socket_connect_timeout=WEBSEARCH_TIMEOUT, socket_timeout=WEBSEARCH_TIMEOUT)
        
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
        
        queue = Queue('casestrainer', connection=redis_conn)
        
        job_ids = queue.job_ids
        logger.info(f"Found {len(job_ids)} jobs in queue. Job IDs: {job_ids}")
        
        job = queue.fetch_job(task_id)
        
        if not job:
            logger.warning(f"Job {task_id} not found in queue")
            return jsonify({
                'error': 'Task not found',
                'task_id': task_id,
                'citations': [],
                'clusters': []
            }), 404
        
        logger.info(f"Job {task_id} status: {job.get_status()}")
        logger.info(f"Job {task_id} meta: {job.meta}")
        logger.info(f"Job {task_id} is_finished: {job.is_finished}")
        logger.info(f"Job {task_id} is_failed: {job.is_failed}")
        logger.info(f"Job {task_id} is_started: {job.is_started}")
        logger.info(f"Job {task_id} is_queued: {job.is_queued}")
        
        result = None
        if job.is_finished:
            try:
                result = job.result
                logger.info(f"Job {task_id} result type: {type(result)}")
            except Exception as e:
                logger.error(f"Error getting job result: {e}")
        
        if job.is_finished:
            if result and isinstance(result, dict) and (result.get('status') in ['success', 'completed'] or result.get('success') is True):
                return jsonify({
                    'status': 'completed',
                    'task_id': task_id,
                    'is_finished': True,
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
            return jsonify({
                'status': 'processing',
                'task_id': task_id,
                'message': 'Task is currently being processed',
                'success': True,
                'citations': [],
                'clusters': []
            })
        
        else:
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

@vue_api.route('/processing_progress', methods=['GET'])
def processing_progress():
    """Get current processing progress from ProgressTracker or global progress manager."""
    request_id = request.args.get('request_id') or request.args.get('task_id')
    
    if not request_id:
        return jsonify({
            'status': 'error',
            'error': 'Missing request_id or task_id parameter',
            'processed_citations': 0,
            'total_citations': 0,
            'is_complete': False
        }), 400
    
    try:
        # First try the global progress manager (for sync processing)
        from src.unified_input_processor import get_progress_manager
        global_progress_mgr = get_progress_manager()
        
        if request_id in global_progress_mgr.active_tasks:
            progress_data = global_progress_mgr.get_progress(request_id)
            logger.debug(f"[Progress API] Found progress in global manager: {progress_data}")
            
            if progress_data and 'error' not in progress_data:
                return jsonify({
                    'status': 'success',
                    'request_id': request_id,
                    'progress_percent': progress_data.get('progress', 0),
                    'current_step': progress_data.get('current_step', 0),
                    'total_steps': progress_data.get('total_steps', 100),
                    'current_message': progress_data.get('message', 'Processing...'),
                    'status_detail': progress_data.get('status', 'processing'),
                    'is_complete': progress_data.get('status') == 'Complete',
                    'processed_citations': progress_data.get('results_count', 0),
                    'total_citations': progress_data.get('results_count', 0)
                })
        
        # Fall back to local progress tracker (for async processing)
        progress_data = progress_tracker.get_progress(request_id)
        
        if progress_data:
            current_step = progress_data.get('current_step', 0)
            current_progress = progress_data.get('current_progress', 0)
            status = progress_data.get('status', 'active')
            steps = progress_data.get('steps', [])
            
            progress_percent = current_progress
            
            is_complete = status == 'completed'
            
            current_step_info = steps[current_step] if steps and current_step < len(steps) else {}
            current_message = current_step_info.get('message', 'Processing...')
            
            return jsonify({
                'status': 'success',
                'request_id': request_id,
                'processed_citations': current_step + 1,  # Use step index as processed count
                'total_citations': len(steps) if steps else 5,  # Use total steps as total count
                'is_complete': is_complete,
                'progress_percent': progress_percent,
                'current_step': current_step + 1,
                'total_steps': len(steps) if steps else 5,
                'current_message': current_message,
                'status_detail': status
            })
        else:
            return jsonify({
                'status': 'success',
                'request_id': request_id,
                'processed_citations': 5,  # Assume completed
                'total_citations': 5,
                'is_complete': True,
                'progress_percent': 100,
                'current_step': 5,
                'total_steps': 5,
                'current_message': 'Processing completed',
                'status_detail': 'completed'
            })
            
    except Exception as e:
        logger.error(f"Error getting progress for {request_id}: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Failed to get progress: {str(e)}',
            'request_id': request_id,
            'processed_citations': 0,
            'total_citations': 0,
            'is_complete': False
        }), 500

@vue_api.route('/analyze/progress-stream/<request_id>', methods=['GET'])
def progress_stream(request_id):
    """
    Server-Sent Events endpoint for real-time progress updates.
    This provides a streaming connection for progress updates during processing.
    """
    def generate_progress_stream():
        """Generate progress updates as Server-Sent Events."""
        try:
            yield 'data: {"type": "connected", "message": "Progress stream connected"}\n\n'
            
            progress_data = progress_tracker.get_progress(request_id)
            
            if progress_data and progress_data.get('status') == 'active':
                steps = progress_data.get('steps', [])
                current_step = progress_data.get('current_step', 0)
                current_progress = progress_data.get('current_progress', 0)
                
                progress_event = {
                    "type": "progress",
                    "data": {
                        "step": steps[current_step].get('name', "Processing...") if steps and current_step < len(steps) else "Processing...",
                        "progress": current_progress,
                        "message": steps[current_step].get('message', "Processing...") if steps and current_step < len(steps) else "Processing...",
                        "total_steps": len(steps) if steps else 0,
                        "current_step": current_step + 1
                    }
                }
                yield f'data: {json.dumps(progress_event)}\n\n'
                
                start_time = time.time()
                while progress_data and progress_data.get('status') == 'active' and (time.time() - start_time) < 30:  # 30 second timeout
                    time.sleep(0.5)
                    progress_data = progress_tracker.get_progress(request_id)
                    if progress_data and progress_data.get('status') == 'completed':
                        yield 'data: {"type": "complete", "message": "Processing completed successfully!"}\n\n'
                        break
                
                progress_tracker.cleanup_progress(request_id)
                
            else:
                progress_steps = [
                    {"step": "Initializing...", "progress": 0, "message": "Starting unified processing..."},
                    {"step": "Extract", "progress": 20, "message": "Extracting citations..."},
                    {"step": "Analyze", "progress": 40, "message": "Citations analyzed and normalized..."},
                    {"step": "Extract Names", "progress": 60, "message": "Case names and years extracted..."},
                    {"step": "Cluster", "progress": 80, "message": "Citations clustered successfully..."},
                    {"step": "Verify", "progress": 90, "message": "Verification completed..."},
                    {"step": "Complete", "progress": 100, "message": "Processing completed successfully!"}
                ]
                
                for i, step_data in enumerate(progress_steps):
                    progress_event = {
                        "type": "progress",
                        "data": {
                            "step": step_data["step"],
                            "progress": step_data["progress"],
                            "message": step_data["message"],
                            "total_steps": len(progress_steps),
                            "current_step": i + 1
                        }
                    }
                    yield f'data: {json.dumps(progress_event)}\n\n'
                    time.sleep(0.3)  # Faster simulation
                
                yield 'data: {"type": "complete", "message": "Progress stream completed"}\n\n'
            
        except Exception as e:
            logger.error(f"Error in progress stream for {request_id}: {e}")
            yield f'data: {{"type": "error", "message": "Progress stream error: {str(e)}"}}\n\n'
    
    return Response(
        generate_progress_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

def _handle_file_upload(service, request_id):
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
        
        filename = secure_filename(file.filename) if file.filename else 'unknown_file'
        logger.info(f"[File Upload {request_id}] Processing file: {filename}")
        logger.info(f"[File Upload {request_id}] Content type: {file.content_type}")
        
        allowed_extensions = {'pdf', 'txt', 'doc', 'docx', 'rtf', 'md', 'html', 'htm', 'xml', 'xhtml'}
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            error_msg = f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}. Got: {file_ext}'
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                'error': error_msg,
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False,
                'metadata': {}
            }
        
        unique_filename = f"{uuid.uuid4()}_{filename}"
        logger.info(f"[File Upload {request_id}] Generated secure filename: {unique_filename}")
        
        uploads_dir = os.path.join('/app', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        logger.info(f"[File Upload {request_id}] Upload directory: {uploads_dir}")
        
        file_path = os.path.join(uploads_dir, unique_filename)
        logger.info(f"[File Upload {request_id}] Saving file to: {file_path}")
        
        try:
            file.save(file_path)
            
            if not os.path.exists(file_path):
                raise IOError("File was not saved successfully")
                
            logger.info(f"[File Upload {request_id}] File saved successfully")
            
            options = {}
            if 'options' in request.form:
                try:
                    options = json.loads(request.form['options'])
                    logger.info(f"[File Upload {request_id}] Parsed options: {options}")
                except json.JSONDecodeError as e:
                    logger.warning(f"[File Upload {request_id}] Failed to parse options JSON: {e}")
            
            logger.info(f"[File Upload {request_id}] Starting file processing with CitationService")
            
            file_size = os.path.getsize(file_path)
            input_data = {'type': 'file', 'file_path': file_path, 'filename': filename, 'file_size': file_size}
            should_process_immediately = service.should_process_immediately(input_data)
            
            if not should_process_immediately:
                from rq import Queue
                from redis import Redis
                from src.rq_worker import process_citation_task_direct
                
                redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
                redis_conn = Redis.from_url(redis_url)
                queue = Queue('casestrainer', connection=redis_conn)
                
                job = queue.enqueue(
                    process_citation_task_direct,
                    args=(request_id, 'file', {
                        'file_path': file_path,
                        'filename': filename,
                        'options': options
                    }),
                    job_timeout=FILE_PROCESSING_TIMEOUT_MINUTES * 60,  # 10 minutes timeout (optimized)
                    result_ttl=86400,  # Keep results for 24 hours
                    failure_ttl=86400  # Keep failed jobs for 24 hours
                )
                
                logger.info(f"[File Upload {request_id}] File processing task enqueued with job_id: {job.id}")
                
                return {
                    'task_id': request_id,
                    'status': 'processing',
                    'message': 'File processing started',
                    'request_id': request_id,
                    'success': True,
                    'citations': [],
                    'clusters': [],
                    'metadata': {
                        'filename': filename,
                        'file_size': os.path.getsize(file_path),
                        'content_type': file.content_type,
                        'processing_mode': 'queued'
                    }
                }
            else:
                logger.info(f"[File Upload {request_id}] Processing file synchronously")
                
                if file_ext == 'pdf':
                    import PyPDF2
                    text = ''
                    logger.info(f"[File Upload {request_id}] Starting PDF text extraction from: {file_path}")
                    try:
                        with open(file_path, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            logger.info(f"[File Upload {request_id}] PDF has {len(pdf_reader.pages)} pages")
                            text = '\n'.join(page.extract_text() for page in pdf_reader.pages)
                            logger.info(f"[File Upload {request_id}] Extracted text length: {len(text)} characters")
                            logger.info(f"[File Upload {request_id}] First 200 chars: {text[:200]}")
                    except Exception as e:
                        logger.error(f"[File Upload {request_id}] PDF extraction failed: {e}")
                        text = f"[Error extracting PDF content: {str(e)}]"
                elif file_ext == 'docx':
                    try:
                        from docx import Document
                        doc = Document(file_path)
                        text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
                    except ImportError:
                        text = f"[DOCX file content could not be extracted - {filename}]"
                        logger.warning(f"[File Upload {request_id}] python-docx not available for DOCX processing")
                    except Exception as e:
                        text = f"[Error extracting DOCX content: {str(e)}]"
                        logger.error(f"[File Upload {request_id}] DOCX processing error: {e}")
                elif file_ext == 'doc':
                    text = f"[DOC files are not supported - {filename}. Please convert to DOCX or PDF.]"
                    logger.warning(f"[File Upload {request_id}] DOC file not supported: {filename}")
                elif file_ext in ['html', 'htm', 'xhtml']:
                    try:
                        from bs4 import BeautifulSoup
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            html_content = f.read()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text = soup.get_text(separator='\n', strip=True)
                        logger.info(f"[File Upload {request_id}] Successfully extracted {len(text)} characters from HTML")
                    except ImportError:
                        text = f"[HTML file content could not be extracted - {filename}]"
                        logger.warning(f"[File Upload {request_id}] BeautifulSoup not available for HTML processing")
                    except Exception as e:
                        text = f"[Error extracting HTML content: {str(e)}]"
                        logger.error(f"[File Upload {request_id}] HTML processing error: {e}")
                elif file_ext == 'xml':
                    try:
                        from bs4 import BeautifulSoup
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            xml_content = f.read()
                        soup = BeautifulSoup(xml_content, 'xml')
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text = soup.get_text(separator='\n', strip=True)
                        logger.info(f"[File Upload {request_id}] Successfully extracted {len(text)} characters from XML")
                    except ImportError:
                        text = f"[XML file content could not be extracted - {filename}]"
                        logger.warning(f"[File Upload {request_id}] BeautifulSoup not available for XML processing")
                    except Exception as e:
                        text = f"[Error extracting XML content: {str(e)}]"
                        logger.error(f"[File Upload {request_id}] XML processing error: {e}")
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                
                logger.info(f"[File Upload {request_id}] Processing extracted text synchronously")
                logger.info(f"[File Upload {request_id}] Text to process length: {len(text)} characters")
                logger.info(f"[File Upload {request_id}] Text preview: {text[:300]}...")
                
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                processor = UnifiedCitationProcessorV2()
                
                citations = processor._extract_citations_unified(text)
                
                result = {
                    'citations': [citation.__dict__ if hasattr(citation, '__dict__') else citation for citation in citations],
                    'clusters': [],  # Clustering will be handled by full async pipeline if needed
                    'statistics': {'total_citations': len(citations)}
                }
                
                logger.info(f"[File Upload {request_id}] Citation processing completed")
                logger.info(f"[File Upload {request_id}] Found {len(result.get('citations', []))} citations")
                logger.info(f"[File Upload {request_id}] Found {len(result.get('clusters', []))} clusters")
                
                formatted_result = {
                    'citations': result.get('citations', []),
                    'clusters': result.get('clusters', []),
                    'statistics': result.get('statistics', {}),
                    'request_id': request_id,
                    'success': True,
                    'metadata': {
                        'source': filename,
                        'text_length': len(text),
                        'processing_time': time.time(),
                        'processing_mode': 'sync'
                    }
                }
                
                formatted_result['metadata'].update({
                    'filename': filename,
                    'file_size': os.path.getsize(file_path),
                    'content_type': file.content_type,
                    'processing_mode': 'sync'
                })
                
                return formatted_result
                
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

def _handle_json_input(service, request_id, data=None):
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
        logger.info(f"[JSON Input {request_id}] Request URL: {request.url}")
        logger.info(f"[JSON Input {request_id}] Request method: {request.method}")
        logger.info(f"[JSON Input {request_id}] Content-Type: {request.content_type}")
        
        if data is None:
            try:
                raw_data = request.get_data(as_text=True)
                logger.info(f"[JSON Input {request_id}] Raw request data (first 1000 chars): {raw_data[:1000]}")
            except Exception as e:
                logger.warning(f"[JSON Input {request_id}] Could not read raw request data: {e}")
            
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
        
        sanitized_data = {}
        for k, v in data.items():
            if isinstance(v, str):
                sanitized_data[k] = v[:100] + '...' if len(v) > 100 else v
            else:
                sanitized_data[k] = str(v)[:200] + '...' if len(str(v)) > 200 else v
        
        logger.info(f"[JSON Input {request_id}] Processing data with keys: {list(data.keys())}")
        
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
            
            if _is_test_citation_text(text):
                error_msg = 'Test citation detected. Please provide actual document content.'
                logger.warning(f"[JSON Input {request_id}] Test citation detected and rejected: {text[:100]}...")
                return {
                    'error': error_msg,
                    'citations': [],
                    'clusters': [],
                    'request_id': request_id,
                    'success': False,
                    'metadata': {
                        'rejected_reason': 'test_citation_detected',
                        'test_pattern_found': _extract_test_pattern(text)
                    }
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
                return {
                    'error': 'No URL provided', 
                    'citations': [], 
                    'clusters': [],
                    'request_id': request_id,
                    'success': False
                }
            
            if not _validate_url(url):
                error_msg = 'Invalid or unsafe URL provided'
                logger.warning(f"[_handle_json_input] [Request {request_id}] URL validation failed: {url}")
                return {
                    'error': error_msg,
                    'citations': [],
                    'clusters': [],
                    'request_id': request_id,
                    'success': False,
                    'metadata': {
                        'rejected_reason': 'url_validation_failed',
                        'url': url
                    }
                }
                
            logger.info(f"[_handle_json_input] [Request {request_id}] Processing URL input...")
            try:
                result = _process_url_input(url, request_id)
                logger.info(f"[_handle_json_input] [Request {request_id}] URL processing completed successfully")
                return result
            except Exception as e:
                logger.error(f"[_handle_json_input] [Request {request_id}] Error in _process_url_input: {str(e)}", exc_info=True)
                raise
            
        else:
            error_msg = f"Invalid input type: {input_type}"
            logger.error(f"[_handle_json_input] [Request {request_id}] {error_msg}")
            return {
                'error': error_msg,
                'citations': [], 
                'clusters': [],
                'request_id': request_id,
                'success': False
            }
            
    except Exception as e:
        error_msg = f"Error processing JSON input: {str(e)}"
        logger.error(f"[_handle_json_input] [Request {request_id}] {error_msg}", exc_info=True)
        
        error_details = {
            'error': 'Internal server error',
            'type': type(e).__name__,
            'message': str(e),
            'request_id': request_id,
            'citations': [],
            'clusters': []
        }
        
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
        form_data = request.form.to_dict()
        text = form_data.get('text', '')
        url = form_data.get('url', '')
        
        if url:
            logger.info(f"[Form Input {request_id}] Processing URL from form: {url}")
            
            if not _validate_url(url):
                error_msg = 'Invalid or unsafe URL provided'
                logger.warning(f"[Form Input {request_id}] URL validation failed: {url}")
                return {
                    'error': error_msg,
                    'citations': [],
                    'clusters': [],
                    'request_id': request_id,
                    'success': False,
                    'metadata': {
                        'rejected_reason': 'url_validation_failed',
                        'url': url
                    }
                }
            
            result = await _process_url_input(url)
            return result
        
        if not text:
            return {
                'error': 'No text or URL provided in form data',
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False
            }
        
        result = await _process_text_input(service, request_id, text)
        return result
        
    except Exception as e:
        logger.error(f"[Form Input {request_id}] Error: {str(e)}", exc_info=True)
        return {
            'error': f'Error processing form input: {str(e)}',
            'citations': [],
            'clusters': [],
            'request_id': request_id,
            'success': False
        }

def _process_text_input(service, request_id, text, source_name="form-input"):
    """Process text input with citation service synchronously."""
    try:
        logger.info(f"[Text Input {request_id}] Processing text of length: {len(text)}")
        
        if _is_test_citation_text(text):
            error_msg = 'Test citation detected. Please provide actual document content.'
            logger.warning(f"[Text Input {request_id}] Test citation detected and rejected: {text[:100]}...")
            return {
                'error': error_msg,
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'success': False,
                'metadata': {
                    'source': source_name,
                    'rejected_reason': 'test_citation_detected',
                    'test_pattern_found': _extract_test_pattern(text),
                    'text_length': len(text)
                }
            }
        
        logger.info(f"[Text Input {request_id}] Processing text immediately")
        input_data = {'type': 'text', 'text': text}
        result = service.process_immediately(input_data)
        
        citations = result.get('citations', [])
        for citation in citations:
            citation.setdefault('extracted_case_name', None)
            citation.setdefault('extracted_date', None)
            citation.setdefault('canonical_name', None)
            citation.setdefault('canonical_date', None)
            citation.setdefault('canonical_url', None)
            citation.setdefault('verified', False)
            
            if 'case_name' not in citation and citation.get('extracted_case_name'):
                citation['case_name'] = citation['extracted_case_name']
                
            if 'year' not in citation and citation.get('extracted_date'):
                citation['year'] = citation['extracted_date']
        
        return {
            'citations': citations,
            'clusters': result.get('clusters', []),
            'request_id': request_id,
            'success': True,
            'metadata': {
                'source': source_name,
                'text_length': len(text),
                'processing_time': time.time(),
                'processing_mode': 'immediate',
                'citation_count': len(citations),
                'cluster_count': len(result.get('clusters', [])),
                'has_verified_citations': any(c.get('verified', False) for c in citations)
            }
        }
            
    except Exception as e:
        logger.error(f"[Text Input {request_id}] Error: {str(e)}", exc_info=True)
        return {
            'error': f'Error processing text: {str(e)}',
            'citations': [],
            'clusters': [],
            'request_id': request_id,
            'success': False,
            'metadata': {
                'source': source_name,
                'text_length': len(text) if 'text' in locals() else 0,
                'error_type': type(e).__name__,
                'processing_mode': 'failed'
            }
        }
        raise

def _is_test_citation_text(text: str) -> bool:
    """Check if text contains known test citations that should be rejected."""
    return False

def _extract_test_pattern(text: str) -> str:
    """Extract the test pattern that was detected."""
    if not text:
        return "no_text"
    
    text_norm = text.strip().lower()
    
    if "smith v. jones" in text_norm and "123 f.3d 456" in text_norm:
        return "smith_v_jones_123_f3d_456"
    elif "123 f.3d 456" in text_norm:
        return "123_f3d_456_pattern"
    elif "999 u.s. 999" in text_norm:
        return "999_us_999_pattern"
    elif "test citation" in text_norm:
        return "test_citation_string"
    elif "sample citation" in text_norm:
        return "sample_citation_string"
    
    return "unknown_test_pattern"

def _is_test_environment_request(request) -> bool:
    """Check if the request appears to be from a test environment."""
    return False

def _is_test_url(url: str) -> bool:
    """Check if a URL is a test URL that should be rejected."""
    if not url:
        return False
    
    url_lower = url.lower()
    
    test_url_patterns = [
        'example.com',
        'test.com',
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
        'test.local',
        'dev.local',
        'staging.local',
        'mock.com',
        'fake.com',
        'dummy.com',
        'sample.com'
    ]
    
    for pattern in test_url_patterns:
        if pattern in url_lower:
            logger.warning(f"Test URL detected: {url} (pattern: {pattern})")
            return True
    
    problematic_protocols = [
        'file://',
        'ftp://',
        'mailto:',
        'tel:',
        'javascript:',
        'data:',
        'chrome://',
        'about:',
        'moz-extension://'
    ]
    
    for protocol in problematic_protocols:
        if url_lower.startswith(protocol):
            logger.warning(f"Problematic URL protocol detected: {url} (protocol: {protocol})")
            return True
    
    return False

def _validate_url(url: str) -> bool:
    """Validate that a URL is safe and properly formatted."""
    if not url or not isinstance(url, str):
        return False
    
    if len(url) > 2048:
        logger.warning(f"URL too long: {len(url)} characters")
        return False
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        if parsed.scheme not in ['http', 'https']:
            logger.warning(f"Unsupported protocol: {parsed.scheme}")
            return False
        
        if _is_test_url(url):
            return False
        
        return True
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False

def _process_url_input(url, request_id=None):
    """Process URL input by fetching content and processing it with citation service."""
    try:
        if request_id is None:
            request_id = f"url_{int(time.time())}"
        
        logger.info(f"[URL Input {request_id}] Processing URL: {url}")
        
        if not _validate_url(url):
            error_msg = 'Invalid or unsafe URL provided'
            logger.warning(f"[URL Input {request_id}] URL validation failed: {url}")
            return {
                'citations': [],
                'clusters': [],
                'success': False,
                'error': error_msg,
                'metadata': {
                    'source': 'url-input',
                    'url': url,
                    'rejected_reason': 'url_validation_failed'
                }
            }
        
        from src.api.services.citation_service import CitationService
        from src.progress_manager import fetch_url_content
        
        service = CitationService()
        
        logger.info(f"[URL Input {request_id}] Fetching content from URL: {url}")
        try:
            content = fetch_url_content(url)
            logger.info(f"[URL Input {request_id}] Successfully fetched {len(content)} characters from URL")
        except Exception as fetch_error:
            error_msg = f'Failed to fetch content from URL: {str(fetch_error)}'
            logger.error(f"[URL Input {request_id}] {error_msg}", exc_info=True)
            return {
                'citations': [],
                'clusters': [],
                'success': False,
                'error': error_msg,
                'metadata': {
                    'source': 'url-input',
                    'url': url,
                    'rejected_reason': 'url_fetch_failed',
                    'fetch_error': str(fetch_error)
                }
            }
        
        if not content or len(content.strip()) < 10:
            error_msg = 'URL returned empty or insufficient content for analysis'
            logger.warning(f"[URL Input {request_id}] {error_msg} - Content length: {len(content)}")
            return {
                'citations': [],
                'clusters': [],
                'success': False,
                'error': error_msg,
                'metadata': {
                    'source': 'url-input',
                    'url': url,
                    'rejected_reason': 'insufficient_content',
                    'content_length': len(content)
                }
            }
        
        logger.info(f"[URL Input {request_id}] Processing fetched content with citation service")
        
        input_data = {'type': 'text', 'text': content}
        if service.should_process_immediately(input_data):
            logger.info(f"[URL Input {request_id}] Processing URL content immediately (short content)")
            result = service.process_immediately(input_data)
            
            return {
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),
                'request_id': request_id,
                'success': True,
                'metadata': {
                    'source': 'url-input',
                    'url': url,
                    'url_domain': urlparse(url).netloc,
                    'content_length': len(content),
                    'processing_time': time.time(),
                    'processing_mode': 'immediate'
                }
            }
        else:
            logger.info(f"[URL Input {request_id}] Queuing URL content for async processing")
            
            from rq import Queue
            from redis import Redis
            
            redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
            redis_conn = Redis.from_url(redis_url)
            queue = Queue('casestrainer', connection=redis_conn)
            
            job = queue.enqueue(
                process_citation_task_direct,
                args=(request_id, 'url', {'url': url, 'content': content}),
                job_timeout=FILE_PROCESSING_TIMEOUT_MINUTES * 60,  # 10 minutes timeout (optimized)
                result_ttl=86400,
                failure_ttl=86400
            )
            
            logger.info(f"[URL Input {request_id}] URL processing task enqueued with job_id: {job.id}")
            
            return {
                'task_id': request_id,
                'status': 'processing',
                'message': 'URL processing started',
                'request_id': request_id,
                'success': True,
                'metadata': {
                    'source': 'url-input',
                    'url': url,
                    'url_domain': urlparse(url).netloc,
                    'content_length': len(content),
                    'processing_mode': 'queued'
                }
            }
        
    except Exception as e:
        logger.error(f"[URL Input {request_id}] Error: {str(e)}", exc_info=True)
        raise

@vue_api.route('/analyze/verification-stream/<request_id>')
def verification_stream(request_id):
    """
    Stream verification progress and results in real-time using Server-Sent Events (SSE)
    
    Args:
        request_id: The request ID to stream verification progress for
        
    Returns:
        Server-Sent Events stream with verification updates
    """
    try:
        from verification_manager import VerificationManager
        
        verification_manager = VerificationManager()
        
        def generate():
            """Generate SSE events for verification progress"""
            try:
                # Connection established event
                connection_data = {
                    'type': 'connection_established',
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(connection_data)}\n\n"
                
                last_status = None
                last_progress = 0
                
                while True:
                    try:
                        status = verification_manager.get_verification_status(request_id)
                        
                        if not status:
                            error_data = {
                                'type': 'error',
                                'message': 'Verification not found or not started',
                                'request_id': request_id,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            yield f"data: {json.dumps(error_data)}\n\n"
                            break
                        
                        status_changed = (
                            last_status != status.get('status') or
                            last_progress != status.get('progress', 0)
                        )
                        
                        if status_changed:
                            event_data = {
                                'type': 'verification_status',
                                'request_id': request_id,
                                'status': status.get('status'),
                                'progress': status.get('progress', 0),
                                'citations_processed': status.get('citations_processed', 0),
                                'citations_count': status.get('citations_count', 0),
                                'current_method': status.get('current_method'),
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            
                            yield f"data: {json.dumps(event_data)}\n\n"
                            
                            last_status = status.get('status')
                            last_progress = status.get('progress', 0)
                        
                        if status.get('status') in ['completed', 'failed']:
                            if status.get('status') == 'completed':
                                results = verification_manager.get_verification_results(request_id)
                                if results:
                                    event_data = {
                                        'type': 'verification_complete',
                                        'request_id': request_id,
                                        'results': results,
                                        'timestamp': datetime.utcnow().isoformat()
                                    }
                                else:
                                    event_data = {
                                        'type': 'verification_complete',
                                        'request_id': request_id,
                                        'message': 'Verification completed but results not available',
                                        'timestamp': datetime.utcnow().isoformat()
                                    }
                            else:
                                event_data = {
                                    'type': 'verification_failed',
                                    'request_id': request_id,
                                    'error_message': status.get('error_message', 'Unknown error'),
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                            
                            yield f"data: {json.dumps(event_data)}\n\n"
                            break
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error in verification stream for {request_id}: {e}")
                        stream_error_data = {
                            'type': 'error',
                            'message': f'Stream error: {str(e)}',
                            'request_id': request_id,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        yield f"data: {json.dumps(stream_error_data)}\n\n"
                        break
                
                stream_end_data = {
                    'type': 'stream_end',
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(stream_end_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Fatal error in verification stream for {request_id}: {e}")
                fatal_error_data = {
                    'type': 'fatal_error',
                    'message': f'Fatal stream error: {str(e)}',
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(fatal_error_data)}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start verification stream for {request_id}: {e}")
        return jsonify({
            'error': f'Failed to start verification stream: {str(e)}',
            'request_id': request_id
        }), 500

@vue_api.route('/analyze/verification-status/<request_id>')
def verification_status(request_id):
    """
    Get current verification status for a request
    
    Args:
        request_id: The request ID to check
        
    Returns:
        Current verification status and progress
    """
    try:
        from verification_manager import VerificationManager
        
        verification_manager = VerificationManager()
        status = verification_manager.get_verification_status(request_id)
        
        if not status:
            return jsonify({
                'error': 'Verification not found',
                'request_id': request_id
            }), 404
        
        return jsonify({
            'request_id': request_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get verification status for {request_id}: {e}")
        return jsonify({
            'error': f'Failed to get verification status: {str(e)}',
            'request_id': request_id
        }), 500

@vue_api.route('/analyze/verification-results/<request_id>')
def verification_results(request_id):
    """
    Get verification results for a completed request
    
    Args:
        request_id: The request ID to get results for
        
    Returns:
        Verification results if available
    """
    try:
        from verification_manager import VerificationManager
        
        verification_manager = VerificationManager()
        results = verification_manager.get_verification_results(request_id)
        
        if not results:
            return jsonify({
                'error': 'Verification results not available',
                'request_id': request_id
            }), 404
        
        return jsonify({
            'request_id': request_id,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get verification results for {request_id}: {e}")
        return jsonify({
            'error': f'Failed to get verification results: {str(e)}',
            'request_id': request_id
        }), 500


def _validate_api_response_data(response_data):
    """
    Validate API response data for integrity issues.
    
    Args:
        response_data: The complete API response dictionary
        
    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []
    
    try:
        result = response_data.get('result', {})
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        # 1. Check for data separation violations
        if citations:
            # Validate data separation for citations
            separation_report = validate_data_separation(citations, similarity_threshold=0.85)
            if not separation_report.get('is_valid', True):
                errors.append(f"Data separation violations: {len(separation_report.get('warnings', []))} issues detected")
                errors.extend(separation_report.get('warnings', [])[:3])  # Include first 3 warnings
        
        # 2. Check for verification status contradictions
        verified_count = 0
        error_count = 0
        
        for citation in citations:
            if isinstance(citation, dict):
                if citation.get('verified') is True:
                    verified_count += 1
                    
                    # Check if verified citation has canonical data
                    if (citation.get('canonical_case_name') is None and 
                        citation.get('canonical_date') in [None, '', '']):
                        errors.append(f"Verified citation '{citation.get('citation', 'unknown')}' missing canonical data")
                    
                    # Check for verification errors
                    if citation.get('error') and 'not be verified' in str(citation.get('error', '')):
                        error_count += 1
                        errors.append(f"Verified citation '{citation.get('citation', 'unknown')}' has verification error: {citation.get('error')}")
        
        if verified_count > 0 and error_count > 0:
            errors.append(f"Verification contradiction: {verified_count} verified citations but {error_count} have verification errors")
        
        # 3. Check for missing extracted data
        missing_extracted = 0
        for citation in citations:
            if isinstance(citation, dict):
                if (citation.get('extracted_case_name') is None and 
                    citation.get('extracted_date') is None):
                    missing_extracted += 1
        
        if missing_extracted > 0:
            errors.append(f"{missing_extracted} citations missing extracted case names and dates")
        
        # 4. Check cluster consistency
        cluster_ids = set()
        citations_with_clusters = 0
        
        for citation in citations:
            if isinstance(citation, dict):
                cluster_id = citation.get('cluster_id')
                is_in_cluster = citation.get('is_in_cluster')
                
                if cluster_id:
                    cluster_ids.add(cluster_id)
                    citations_with_clusters += 1
                elif is_in_cluster:
                    errors.append(f"Citation '{citation.get('citation', 'unknown')}' marked as in cluster but has no cluster_id")
        
        # Check if clusters array matches cluster_ids from citations
        cluster_ids_from_clusters = {cluster.get('id') for cluster in clusters if isinstance(cluster, dict)}
        missing_clusters = cluster_ids - cluster_ids_from_clusters
        if missing_clusters:
            errors.append(f"Missing cluster definitions for IDs: {list(missing_clusters)[:3]}")
        
        # 5. Check for malformed citations
        malformed_count = 0
        for citation in citations:
            if isinstance(citation, dict):
                cit_text = citation.get('citation', '')
                if not cit_text or len(str(cit_text)) < 3:
                    malformed_count += 1
        
        if malformed_count > 0:
            errors.append(f"{malformed_count} citations have malformed or missing citation text")
        
        # 6. Check temporal consistency (citations from same cluster shouldn't be decades apart)
        if len(clusters) > 0:
            for cluster in clusters:
                if isinstance(cluster, dict):
                    cluster_citations = cluster.get('citations', [])
                    years = []
                    
                    for cit_text in cluster_citations:
                        # Find the citation object
                        for citation in citations:
                            if isinstance(citation, dict) and citation.get('citation') == cit_text:
                                year = citation.get('extracted_date') or citation.get('canonical_date')
                                if year and isinstance(year, (int, str)):
                                    try:
                                        years.append(int(str(year)[:4]))  # Extract year
                                    except ValueError:
                                        pass
                    
                    if len(years) > 1:
                        year_range = max(years) - min(years)
                        if year_range > 50:  # More than 50 years apart
                            errors.append(f"Cluster '{cluster.get('case_name', 'unknown')}' spans {year_range} years ({min(years)}-{max(years)})")
    
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        logger.error(f"Error during API response validation: {e}", exc_info=True)
    
    return errors