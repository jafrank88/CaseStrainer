"""
CaseStrainer Canonical API Endpoints
===================================

POST   /casestrainer/api/analyze         - Analyze and validate citations (file, text, or URL input)
GET    /casestrainer/api/task_status/<task_id> - Check processing status/results for async tasks
GET    /casestrainer/api/health          - Health check endpoint
GET    /casestrainer/api/version         - Application version info
GET    /casestrainer/api/server_stats    - (Optional) Server statistics
GET    /casestrainer/api/db_stats        - (Optional) Database statistics

All other endpoints are deprecated and should not be used in production.

This module provides the API endpoints needed by the Vue.js frontend
for the Multitool Confirmed and Unconfirmed Citations tabs.
"""

import logging
import sys
import os
import traceback
from datetime import datetime
import uuid
import json
import flask
from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    make_response,
    after_this_request
)
from werkzeug.utils import secure_filename
import time
import mimetypes
import urllib.parse
import hashlib
from functools import lru_cache, wraps
import shutil
from statistics import mean, median
from queue import Queue
from threading import Lock, Thread
import backoff
from math import ceil
from flask import Flask
from waitress import serve
import asyncio
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
import requests
from src.citation_utils import extract_all_citations
from src.file_utils import extract_text_from_file
from src.citation_utils import deduplicate_citations
from src.enhanced_validator_production import make_error_response
import tempfile
# Use EnhancedMultiSourceVerifier for multi-source citation verification
# try:
#     from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
#     CitationVerifier = EnhancedMultiSourceVerifier  # Alias for compatibility
#     logger.info("Using EnhancedMultiSourceVerifier for multi-source citation verification")
# except ImportError as e:
#     logger.warning(f"Could not import EnhancedMultiSourceVerifier: {e}")
#     logger.warning("Falling back to CitationVerifier")
#     from citation_verification import CitationVerifier
from rq import Queue
from redis import Redis
from rq import get_current_job
from src.citation_processor import CitationProcessor
import sqlite3
import redis
import threading
from src.document_processing import process_document_input, extract_and_verify_citations
from src.config import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH

# PATCH: Disable RQ death penalty on Windows before any RQ import
import os
if os.name == 'nt':  # Windows
    os.environ['RQ_DISABLE_SIGALRM'] = '1'

# Configure logging first, before anything else
def configure_logging():
    """Configure logging for the application using centralized configuration."""
    try:
        # Import and use the centralized logging configuration
        from src.config import configure_logging as config_configure_logging
        config_configure_logging()
        
        # Create logger for this module
        logger = logging.getLogger(__name__)
        logger.info("=== Logging Configuration ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        return logger
        
    except Exception as e:
        print(f"Failed to configure logging: {str(e)}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s'
        )
        return logging.getLogger(__name__)

# Configure logging and get logger
logger = configure_logging()

logger.info("=== Backend Startup ===")
logger.info("Importing required modules...")

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
            
            # Limit response data to 200 characters for logging
            truncated_data = response_data[:200] + "..." if len(response_data) > 200 else response_data
            
            # Log minimal information
            logger.info(f"[RESPONSE] {request.method} {request.endpoint} -> {response.status_code} ({len(response_data)} chars)")
            if len(response_data) > 200:
                logger.info(f"[RESPONSE] Body (truncated): {truncated_data}")
                
        return response
        
    except Exception as e:
        logger.error(f"Error in log_json_responses: {str(e)}")
        return response

# Use EnhancedMultiSourceVerifier for multi-source citation verification
try:
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier, RateLimitError
    CitationVerifier = EnhancedMultiSourceVerifier  # Alias for compatibility
    logger.info("Using EnhancedMultiSourceVerifier for multi-source citation verification")
except ImportError as e:
    logger.warning(f"Could not import EnhancedMultiSourceVerifier: {e}")
    logger.warning("Falling back to CitationVerifier")
    from src.citation_verification import CitationVerifier
    RateLimitError = Exception  # Fallback for compatibility

try:
    # Create Blueprint instead of Flask app
    logger.info("Creating Flask Blueprint...")
    vue_api = Blueprint('vue_api', __name__)
    
    # Register the after_request handler to log all JSON responses
    vue_api.after_request(log_json_responses)
    
    logger.info("Flask Blueprint created successfully")
    
except Exception as e:
    logger.error(f"Failed to create Flask Blueprint: {str(e)}\n{traceback.format_exc()}")
    raise

# Initialize global variables
logger.info("Initializing global variables...")
try:
    # Remove active_requests for persistent state, but keep as fallback if Redis is unavailable
    active_requests = {}
    
    # Constants - OPTIMIZED for better performance
    COURTLISTENER_RATE_LIMIT = 180  # requests per minute
    COURTLISTENER_RATE_WINDOW = 60  # seconds
    COURTLISTENER_BATCH_SIZE = 20   # citations per batch (increased from 10)
    COURTLISTENER_BATCH_INTERVAL = 1  # seconds between batches (reduced from 3)
    COURTLISTENER_CITATIONS_PER_MINUTE = 150  # citations per minute for timeout calculation (increased from 90)
    DEFAULT_TIMEOUT = 300  # 5 minutes default timeout
    
    WORKER_ENV = os.environ.get("CASTRAINER_ENV", "production").lower()
    WORKER_LABEL = ""  # Remove misleading [DEV] labels
    
    # Redis configuration
    try:
        # Use REDIS_URL environment variable if available, otherwise fallback to localhost
        # Use standard Redis port 6379 for all environments
        default_redis_url = 'redis://casestrainer-redis-prod:6379/0'
        redis_url = os.environ.get('REDIS_URL', default_redis_url)
        if redis_url.startswith('redis://'):
            # Parse redis://host:port/db format
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            redis_host = parsed.hostname or 'localhost'
            redis_port = parsed.port or 6379
            redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
        else:
            # Fallback to localhost
            redis_host = 'localhost'
            redis_port = 6379
            redis_db = 0
            
        redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db)
        redis_conn.ping()  # Test connection
        REDIS_AVAILABLE = True
        logger.info(f"[REDIS] Redis connection successful to {redis_host}:{redis_port}")
    except Exception as e:
        logger.warning(f"[REDIS] Redis not available: {e}")
        REDIS_AVAILABLE = False
        redis_conn = None
    
    # Set Redis task tracking based on Redis availability
    REDIS_TASK_TRACKING = REDIS_AVAILABLE
    
    TASK_CLEANUP_INTERVAL = 60  # seconds
    TASK_TTL = 300  # seconds (5 minutes in memory)
    REDIS_TASK_TTL = 600  # seconds (10 minutes in Redis)
    
    # Note: Task cleanup is now handled by the centralized background tasks system
    # in src/background_tasks.py
    
    logger.info("Global variables initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize global variables: {str(e)}\n{traceback.format_exc()}")
    raise

def check_redis():
    try:
        # Add timeout to prevent hanging
        redis_conn.ping()
        return "ok"
    except Exception as e:
        logger.warning(f"Redis check failed: {e}")
        return "down"

def check_db():
    try:
        conn = sqlite3.connect(os.path.join(os.getcwd(), 'data', 'citations.db'), timeout=3)
        conn.execute('SELECT 1')
        conn.close()
        return "ok"
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        return "down"

def check_rq_worker():
    try:
        if RQ_AVAILABLE:
            from rq import Worker
            import threading
            import time
            
            # Use threading-based timeout for Windows compatibility
            result = {"status": "down", "error": None}
            
            def worker_check():
                try:
                    workers = Worker.all(connection=redis_conn)
                    result["status"] = "ok" if workers else "down"
                except Exception as e:
                    result["status"] = "down"
                    result["error"] = str(e)
            
            # Start the check in a separate thread
            thread = threading.Thread(target=worker_check)
            thread.daemon = True
            thread.start()
            
            # Wait for up to 3 seconds
            thread.join(timeout=3)
            
            if thread.is_alive():
                logger.warning("RQ worker check timed out")
                return "timeout"
            else:
                if result["error"]:
                    logger.warning(f"RQ worker check failed: {result['error']}")
                return result["status"]
        else:
            return "ok" if worker_thread and worker_thread.is_alive() else "down"
    except Exception as e:
        logger.warning(f"check_rq_worker exception: {e}")
        return "down"

def is_rq_available():
    """Dynamically check if Redis and at least one RQ worker are available."""
    try:
        # Check Redis connection
        redis_conn.ping()
        # Check for at least one RQ worker
        from rq import Worker
        workers = Worker.all(connection=redis_conn)
        return bool(workers)
    except Exception as e:
        logger.warning(f"is_rq_available check failed: {e}")
        return False

@vue_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the Vue API."""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'CaseStrainer Vue API',
            'timestamp': datetime.now().isoformat(),
            'redis': check_redis(),
            'database': check_db(),
            'rq_worker': check_rq_worker(),
            'environment': WORKER_ENV,
            'version': '0.5.6'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'service': 'CaseStrainer Vue API',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@vue_api.route('/process-text', methods=['POST'])
def process_text():
    """
    Deprecated: Forwards text input to /analyze endpoint. Use /analyze instead.
    """
    try:
        # Accept both JSON and form data
        if request.is_json:
            data = request.get_json()
            text = data.get('text', '')
        else:
            text = request.form.get('text', '')
        if not text.strip():
            return jsonify({'error': 'No text provided', 'deprecated': True, 'message': 'This endpoint is deprecated. Please use /analyze.'}), 400
        # Forward the text to /analyze as JSON
        analyze_url = request.url_root.rstrip('/') + '/casestrainer/api/analyze'
        headers = {"Content-Type": "application/json", "X-Forwarded-For": "internal-process-text"}
        resp = requests.post(analyze_url, json={"type": "text", "text": text}, headers=headers)
        
        # Check if the response is valid JSON
        try:
            response_json = resp.json()
        except ValueError as e:
            # If response is not valid JSON, return the raw response with error info
            return jsonify({
                'error': f'Invalid JSON response from /analyze: {str(e)}',
                'raw_response': resp.text,
                'status_code': resp.status_code,
                'deprecated': True,
                'message': 'This endpoint is deprecated. Please use /analyze.'
            }), 500
        
        response_json['deprecated'] = True
        response_json['message'] = 'This endpoint is deprecated. Please use /analyze.'
        return make_response(jsonify(response_json), resp.status_code)
    except Exception as e:
        return jsonify({'error': str(e), 'deprecated': True, 'message': 'This endpoint is deprecated. Please use /analyze.'}), 500

@vue_api.route('/server_stats', methods=['GET'])
def server_stats():
    """Detailed server statistics and restart tracking endpoint."""
    try:
        stats = {
            'timestamp': time.time(),
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rq_available': is_rq_available(),
            'queue_length': queue.count if RQ_AVAILABLE and queue else 'N/A',
            'worker_health': check_rq_worker(),
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Server stats failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': time.time(),
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

# Add error handlers
@vue_api.errorhandler(Exception)
def handle_error(error):
    """Global error handler for the Flask application."""
    logger.error(f"Unhandled error: {str(error)}\n{traceback.format_exc()}")
    return jsonify({
        'error': str(error),
        'status': 'error'
    }), getattr(error, 'code', 500)

# Set up Redis connection and RQ queue
try:
    # Use REDIS_URL environment variable if available, otherwise fallback to localhost
    # Use standard Redis port 6379 for all environments
    default_redis_url = 'redis://casestrainer-redis-prod:6379/0'
    redis_url = os.environ.get('REDIS_URL', default_redis_url)
    if redis_url.startswith('redis://'):
        # Parse redis://host:port/db format
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        redis_host = parsed.hostname or 'localhost'
        redis_port = parsed.port or 6379
        redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
    else:
        # Fallback to localhost
        redis_host = 'localhost'
        redis_port = 6379
        redis_db = 0
    
    redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db)
    queue = Queue('casestrainer', connection=redis_conn, result_ttl=3600)  # Keep results for 1 hour
    
    # Force threading fallback on Windows due to RQ compatibility issues
    import platform
    if platform.system() == 'Windows':
        RQ_AVAILABLE = False
        logger.info("RQ queue initialized but using threading fallback for Windows compatibility")
    else:
        RQ_AVAILABLE = True
        logger.info(f"RQ queue initialized successfully with Redis at {redis_host}:{redis_port}")
    
    # Configure RQ for Windows compatibility (if we were using it)
    if platform.system() == 'Windows':
        # Disable death penalty timeout on Windows (uses SIGALRM which doesn't exist)
        from rq.timeouts import BaseDeathPenalty
        class WindowsDeathPenalty(BaseDeathPenalty):
            def setup_death_penalty(self):
                # Do nothing on Windows - no SIGALRM available
                pass
            
            def cancel_death_penalty(self):
                # Do nothing on Windows
                pass
        
        # Set the death penalty class for Windows
        import rq.timeouts
        rq.timeouts.DeathPenalty = WindowsDeathPenalty
        logger.info("Configured RQ for Windows compatibility (disabled SIGALRM)")
        
except Exception as e:
    logger.error(f"Failed to initialize RQ queue: {e}")
    RQ_AVAILABLE = False


# FIX: Disable worker thread to prevent blocking
# This is a temporary fix to allow the API endpoints to work

# Disable the problematic worker thread
worker_thread = None
worker_running = False
task_queue = None

# Override the worker initialization
def initialize_worker():
    """Initialize worker thread (disabled for now)"""
    global worker_thread, worker_running, task_queue
    
    # Disable worker thread to prevent blocking
    worker_thread = None
    worker_running = False
    task_queue = None
    
    print("Worker thread disabled to prevent blocking")
    return True

# Override the worker loop
def worker_loop():
    """Worker loop (disabled)"""
    print("Worker loop disabled")
    return

# Override the is_worker_running function
def is_worker_running():
    """Check if worker is running (always False for now)"""
    return False

# Override the get_server_stats function
def get_server_stats():
    """Get server stats (simplified)"""
    return {
        'start_time': time.time(),
        'uptime': '00:00:00',
        'uptime_seconds': 0,
        'restart_count': 0,
        'worker_alive': False,
        'worker_disabled': True
    }

def process_citation_task(task_id, task_type, task_data):
    """
    Unified citation verification task with progress tracking for file, url, and text.
    Now supports chunked progress and ETA for large documents.
    """
    logger.info(f"[TASK] Starting citation verification task {task_id}")
    print(f"[DEBUG] process_citation_task called with task_id={task_id}, task_type={task_type}")
    print(f"[DEBUG] task_data: {task_data}")
    import math
    try:
        result = None
        text = None
        total_chunks = 1
        chunk_size = 3000  # characters per chunk (tune as needed)
        start_time = time.time()
        if task_type == 'file':
            file_path = task_data.get('file_path')
            filename = task_data.get('filename', 'unknown')
            file_ext = task_data.get('file_ext', '')
            logger.info(f"[TASK] Processing file: {filename} at {file_path}")
            from src.file_utils import extract_text_from_file
            text = extract_text_from_file(file_path, file_ext=file_ext)
        elif task_type == 'text':
            text = task_data.get('text', '')
            logger.info(f"[TASK] Processing text input (length: {len(text)})")
        elif task_type == 'url':
            url = task_data.get('url', '')
            logger.info(f"[TASK] Processing URL: {url}")
            if not url:
                result = {
                    'status': 'failed',
                    'error': 'No URL provided',
                    'citations': [],
                    'case_names': []
                }
            else:
                from src.enhanced_validator_production import extract_text_from_url
                url_result = extract_text_from_url(url)
                text = url_result.get('text', '')
        # If text is available, process in chunks
        if text is not None:
            if not text.strip():
                result = {
                    'status': 'failed',
                    'error': 'No text content extracted',
                    'citations': [],
                    'case_names': []
                }
            else:
                # Split text into chunks
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                total_chunks = len(chunks)
                all_citations = []
                all_case_names = []
                for idx, chunk in enumerate(chunks):
                    from src.document_processing import process_document
                    chunk_result = process_document(content=chunk, extract_case_names=True)
                    all_citations.extend(chunk_result.get('citations', []))
                    all_case_names.extend(chunk_result.get('case_names', []))
                    # Update progress in Redis
                    progress = int(((idx+1)/total_chunks)*100)
                    set_task_status(task_id, 'processing', {
                        'progress': progress,
                        'current_chunk': idx+1,
                        'total_chunks': total_chunks,
                        'start_time': start_time,
                        'type': task_type
                    })
                # After all chunks, aggregate results
                result = {
                    'status': 'success',
                    'citations': all_citations,
                    'case_names': list(set(all_case_names)),
                    'statistics': {},
                    'summary': {},
                    'extraction_metadata': {
                        'text_length': len(text),
                        'total_chunks': total_chunks
                    }
                }
        # Debug log the result before deciding what to do
        logger.info(f"[DEBUG] process_citation_task result for {task_id}: {result}")
        print(f"[DEBUG] process_citation_task result for {task_id}: {result}")
        # CRITICAL DEBUG: This should definitely show up
        print(f"CRITICAL DEBUG: Task {task_id} result status: {result.get('status') if result else 'None'}")
        logger.error(f"CRITICAL DEBUG: Task {task_id} result status: {result.get('status') if result else 'None'}")
        # Always update status and result in Redis (or fallback)
        if result and result.get('status') == 'failed':
            set_task_status(task_id, 'failed', {'error': result.get('error', 'Unknown error')})
            logger.error(f"[WORKER] Task {task_id} failed, error written to Redis: {result.get('error', 'Unknown error')}")
            logger.info(f"[WORKER] Set task {task_id} status to failed")
        else:
            set_task_status(task_id, 'completed', {'progress': 100, 'current_step': 'Complete'})
            logger.info(f"[DEBUG] Calling set_task_result for {task_id} with result: {result}")
            print(f"[DEBUG] Calling set_task_result for {task_id} with result: {result}")
            # Create the task result data structure
            task_result_data = {
                'task_id': task_id,
                'type': task_type,
                'status': 'completed',
                'results': result.get('citations', []),
                'citations': result.get('citations', []),
                'case_names': result.get('case_names', []),
                'metadata': result.get('extraction_metadata', {}),
                'statistics': result.get('statistics', {}),
                'summary': result.get('summary', {}),
                'start_time': start_time,
                'end_time': time.time(),
                'progress': 100,
                'current_step': 'Complete',
                'total_chunks': total_chunks
            }
            # Debug: Check if the data is JSON serializable
            try:
                import json
                test_json = json.dumps(task_result_data)
                logger.info(f"[DEBUG] Task result data is JSON serializable: {test_json[:200]}...")
                print(f"[DEBUG] Task result data is JSON serializable: {test_json[:200]}...")
            except Exception as json_error:
                logger.error(f"[DEBUG] Task result data is NOT JSON serializable: {json_error}")
                print(f"[DEBUG] Task result data is NOT JSON serializable: {json_error}")
                # Try to identify the problematic field
                for key, value in task_result_data.items():
                    try:
                        json.dumps({key: value})
                    except Exception as field_error:
                        logger.error(f"[DEBUG] Field '{key}' is not JSON serializable: {field_error}")
                        print(f"[DEBUG] Field '{key}' is not JSON serializable: {field_error}")
            set_task_result(task_id, task_result_data)
            logger.info(f"[WORKER] Task {task_id} completed, result written to Redis")
            logger.info(f"[WORKER] Set task {task_id} status to completed and stored result")
        return result
    except Exception as e:
        logger.error(f"Error processing citation task {task_id}: {str(e)}")
        set_task_status(task_id, 'failed', {'error': str(e)})
        return {'status': 'failed', 'error': str(e)}

@vue_api.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    """
    Unified API endpoint for document analysis and citation verification.
    Handles file uploads, direct text, URLs, and single citation analysis.
    Implements asynchronous processing for improved response time.
    """
    start_time = time.time()
    source_type = None
    source_name = None
    file_ext = None
    content_type = None
    text = None

    try:
        logger = current_app.logger
        logger.info(f"[ANALYZE] Request method: {request.method}")
        logger.info(f"[ANALYZE] Request headers: {dict(request.headers)}")
        try:
            logger.info(f"[ANALYZE] Request body: {request.get_data(as_text=True)[:1000]}")
        except Exception as e:
            logger.warning(f"[ANALYZE] Could not log request body: {e}")
        
        # Handle OPTIONS request for CORS preflight
        if request.method == 'OPTIONS':
            response = make_response(jsonify({'status': 'ok'}), 200)
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

        # Parse input type and data
        input_type = None
        data = None
        if request.is_json:
            data = request.get_json(silent=True) or {}
            input_type = data.get('type')
        elif request.form:
            data = request.form.to_dict()
            input_type = data.get('type')
        else:
            data = {}

        # Initialize task ID for asynchronous processing
        task_id = str(uuid.uuid4())
        current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Assigned task ID: {task_id}")

        # Handle file upload
        if 'file' in request.files or 'file' in request.form or (request.is_json and 'file' in data):
            file = request.files.get('file')
            if not file:
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided'
                }), 400
            # Comprehensive file validation
            is_valid, error_message = validate_file_upload(file)
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': error_message
                }), 400
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            temp_file_path = None
            try:
                # Save uploaded file to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                # Add task to queue
                task = {
                    'task_id': task_id,
                    'type': 'file',
                    'data': {
                        'file_path': temp_file_path,
                        'filename': filename,
                        'file_ext': file_ext
                    }
                }
                # Initialize task in active_requests
                set_task_status(task_id, 'queued', task['data'])
                # Enqueue task
                current_app.logger.info(f"[ANALYZE] RQ_AVAILABLE={RQ_AVAILABLE}, queue={queue}")
                if RQ_AVAILABLE and queue:
                    job = queue.enqueue(process_citation_task, task_id, 'file', task['data'])
                    logger.info(f"[ANALYZE] Enqueued job for task {task_id}: job_id={getattr(job, 'id', None)}")
                    if not job:
                        logger.error(f"[ANALYZE] Failed to enqueue task {task_id}: job is None")
                        return make_error_response(
                            "enqueue_error",
                            f"Failed to enqueue task {task_id}",
                            status_code=500
                        )
                    # Store the job ID mapping in Redis using the global connection
                    try:
                        redis_conn.setex(f"task_to_job:{task_id}", 3600, job.id)  # Store for 1 hour
                        logger.info(f"{WORKER_LABEL} [ANALYZE] Stored task {task_id} -> job {job.id} mapping")
                    except Exception as e:
                        logger.error(f"[ANALYZE] Failed to store job mapping for {task_id}: {e}")
                    logger.info(f"[ANALYZE] Added file task {task_id} to RQ")
                else:
                    queue_size = task_queue.qsize() if task_queue else 'N/A'
                    current_app.logger.info(f"[ANALYZE] Adding file task {task_id} to threading queue (queue size: {queue_size})")
                    if task_queue:
                        task_queue.put((task_id, 'file', task['data']))
                    new_queue_size = task_queue.qsize() if task_queue else 'N/A'
                    current_app.logger.info(f"[ANALYZE] Added file task {task_id} to threading queue (new queue size: {new_queue_size})")
                # Return immediate response with task ID
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'File upload received, processing started',
                    'metadata': {
                        'source_type': 'file',
                        'source_name': filename,
                        'file_type': file_ext,
                        'timestamp': datetime.utcnow().isoformat() + "Z",
                        'user_agent': request.headers.get("User-Agent")
                    }
                })
            except Exception as e:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to handle file upload: {str(e)}',
                    'source_type': 'file',
                    'source_name': filename
                }), 400

        # Handle text input
        elif input_type == 'text' or ('text' in data and data['text']):
            text = data.get('text')
            
            # Comprehensive text validation
            is_valid, error_message = validate_text_input(text)
            if not is_valid:
                return make_error_response(
                    "input_validation",
                    error_message,
                    status_code=400,
                    source_type="text",
                    source_name="pasted_text"
                )
            
            # --- Immediate vs Async Response Logic ---
            # If the input is a short, single citation (less than 50 chars, contains numbers, matches known citation patterns, <= 10 words),
            # process it synchronously for instant feedback. Otherwise, queue for async processing.
            # This logic is tuned for optimal user experience and can be adjusted as needed.
            text_trimmed = text.strip()
            current_app.logger.info(f"[ANALYZE] Immediate/Async decision: text_len={len(text_trimmed)}, words={len(text_trimmed.split())}, patterns={[w for w in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'L.ED.2D', 'L.ED.3D', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL', 'WN.2D', 'WN.APP.', 'WN. APP.', 'WASH.2D', 'WASH.APP.', 'WASH. APP.'] if w in text_trimmed.upper()]}")
            if (len(text_trimmed) < 50 and  # Short text
                any(char.isdigit() for char in text_trimmed) and  # Contains numbers
                any(word in text_trimmed.upper() for word in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'L.ED.2D', 'L.ED.3D', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL', 'WN.2D', 'WN.APP.', 'WN. APP.', 'WASH.2D', 'WASH.APP.', 'WASH. APP.']) and  # Contains citation patterns
                len(text_trimmed.split()) <= 10):  # Few words
                # Immediate (synchronous) response
                current_app.logger.info(f"[ANALYZE] Using immediate (synchronous) response for citation: {text_trimmed}")
                
                try:
                    # Import the enhanced validator and complex citation integration
                    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
                    try:
                        from src.complex_citation_integration import ComplexCitationIntegrator, format_complex_citation_for_frontend
                        integrator = ComplexCitationIntegrator()
                        results = integrator.process_text_with_complex_citations_original(text_trimmed)
                    except ImportError as import_error:
                        current_app.logger.warning(f"[ANALYZE] ComplexCitationIntegrator not available: {import_error}")
                        # Fallback to simple verification
                        verifier = EnhancedMultiSourceVerifier()
                        results = verifier.verify_citation(text_trimmed)
                        if isinstance(results, dict):
                            results = [results]
                        # Simple formatting for fallback
                        def format_complex_citation_for_frontend(result):
                            return {
                                'display_text': result.get('citation', ''),
                                'complex_features': {},
                                'parallel_info': {}
                            }
                    
                    processing_time = time.time() - start_time
                    
                    # Extract results and statistics
                    # The method returns a list directly, not a dictionary
                    statistics = {
                        'total_citations': len(results),
                        'verified_citations': len([r for r in results if r.get('verified') == 'true']),
                        'unverified_citations': len([r for r in results if r.get('verified') != 'true']),
                        'parallel_citations': len([r for r in results if r.get('is_parallel_citation')]),
                        'unique_cases': len(set(r.get('canonical_name', '') for r in results if r.get('canonical_name')))
                    }
                    summary = {
                        'total_citations': len(results),
                        'verified_citations': len([r for r in results if r.get('verified') == 'true']),
                        'unverified_citations': len([r for r in results if r.get('verified') != 'true']),
                        'parallel_citations': len([r for r in results if r.get('is_parallel_citation')]),
                        'unique_cases': len(set(r.get('canonical_name', '') for r in results if r.get('canonical_name')))
                    }
                    
                    # Format results for frontend
                    formatted_citations = []
                    for result in results:
                        formatted_result = format_complex_citation_for_frontend(result)
                        formatted_citations.append({
                            'citation': result.get('citation', text_trimmed),
                            'valid': result.get('verified', 'false'),
                            'verified': result.get('verified', 'false'),
                            'case_name': result.get('case_name', ''),
                            'extracted_case_name': result.get('extracted_case_name', ''),
                            'canonical_name': result.get('canonical_name', ''),
                            'hinted_case_name': result.get('hinted_case_name', ''),
                            'canonical_date': result.get('canonical_date', ''),
                            'extracted_date': result.get('extracted_date', ''),
                            'court': result.get('court', ''),
                            'docket_number': result.get('docket_number', ''),
                            'confidence': result.get('confidence', 0.0),
                            'source': result.get('source', 'Unknown'),
                            'url': result.get('url', ''),
                            'details': result.get('details', {}),
                            'is_complex_citation': result.get('is_complex_citation', False),
                            'is_parallel_citation': result.get('is_parallel_citation', False),
                            'complex_metadata': result.get('complex_metadata', {}),
                            'display_text': formatted_result.get('display_text', ''),
                            'complex_features': formatted_result.get('complex_features', {}),
                            'parallel_info': formatted_result.get('parallel_info', {}),
                            'parallel_citations': result.get('parallel_citations', []),
                            'metadata': {
                                'source_type': 'citation',
                                'source_name': 'single_citation',
                                'processing_time': processing_time,
                                'timestamp': datetime.utcnow().isoformat() + "Z",
                                'user_agent': request.headers.get("User-Agent")
                            }
                        })
                    
                    response_data = {
                        'citations': formatted_citations,
                        'statistics': statistics,
                        'summary': summary
                    }
                    
                    # Log results
                    for result in results:
                        current_app.logger.info(f"[ANALYZE] Citation '{result.get('citation', text_trimmed)}' validation result: {result.get('verified', False)}")
                        current_app.logger.info(f"[ANALYZE] Is complex citation: {result.get('is_complex_citation', False)}")
                        current_app.logger.info(f"[ANALYZE] Extracted case name: {result.get('extracted_case_name', 'None')}")
                        current_app.logger.info(f"[ANALYZE] Canonical case name: {result.get('canonical_name', 'None')}")
                    # Log the full response_data sent to the frontend
                    current_app.logger.info(f"[ANALYZE] Response to frontend: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                    return jsonify(response_data)
                    
                except Exception as e:
                    current_app.logger.error(f"[ANALYZE] Error validating single citation '{text_trimmed}': {str(e)}")
                    # Fall back to async processing
                    current_app.logger.info(f"[ANALYZE] Falling back to async processing for citation: {text_trimmed}")
                
            # Continue with async processing for longer text or if single citation validation failed
            # Async (queued) response
            current_app.logger.info(f"[ANALYZE] Using async (queued) response for text input: {text_trimmed[:60]}...")
            
            # Add task to queue
            task = {
                'task_id': task_id,
                'type': 'text',
                'data': {
                    'text': text
                }
            }
            # Initialize task in active_requests
            set_task_status(task_id, 'queued', task['data'])
            
            # Enqueue task
            current_app.logger.info(f"[ANALYZE] RQ_AVAILABLE={RQ_AVAILABLE}, queue={queue}")
            if RQ_AVAILABLE and queue:
                try:
                    job = queue.enqueue(process_citation_task, task_id, 'text', task['data'])
                    logger.info(f"[ANALYZE] Enqueued job for task {task_id}: job_id={getattr(job, 'id', None)}")
                    if not job:
                        logger.error(f"[ANALYZE] Failed to enqueue task {task_id}: job is None")
                        return make_error_response(
                            "enqueue_error",
                            f"Failed to enqueue task {task_id}",
                            status_code=500
                        )
                    # Store the job ID mapping in Redis using the global connection
                    try:
                        redis_conn.setex(f"task_to_job:{task_id}", 3600, job.id)  # Store for 1 hour
                        logger.info(f"{WORKER_LABEL} [ANALYZE] Stored task {task_id} -> job {job.id} mapping")
                    except Exception as e:
                        logger.error(f"[ANALYZE] Failed to store job mapping for {task_id}: {e}")
                    logger.info(f"[ANALYZE] Added text task {task_id} to RQ")
                except Exception as e:
                    logger.error(f"[ANALYZE] Exception during enqueue for {task_id}: {e}", exc_info=True)
                    return make_error_response(
                        "enqueue_error",
                        f"Exception during enqueue: {e}",
                        status_code=500
                    )
                # Return immediate response with task ID for queued tasks
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'Text received, processing started',
                    'metadata': {
                        'source_type': 'text',
                        'source_name': 'pasted_text',
                        'timestamp': datetime.utcnow().isoformat() + "Z",
                        'user_agent': request.headers.get("User-Agent")
                    }
                })
            elif task_queue is not None:
                # Use fallback threading queue
                queue_size = task_queue.qsize() if task_queue else 'N/A'
                current_app.logger.info(f"[ANALYZE] Adding text task {task_id} to threading queue (queue size: {queue_size})")
                if task_queue:
                    task_queue.put((task_id, 'text', task['data']))
                new_queue_size = task_queue.qsize() if task_queue else 'N/A'
                current_app.logger.info(f"[ANALYZE] Added text task {task_id} to threading queue (new queue size: {new_queue_size})")
                # Return immediate response with task ID for queued tasks
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'Text received, processing started',
                    'metadata': {
                        'source_type': 'text',
                        'source_name': 'pasted_text',
                        'timestamp': datetime.utcnow().isoformat() + "Z",
                        'user_agent': request.headers.get("User-Agent")
                    }
                })
            else:
                # Worker thread is disabled, process immediately
                current_app.logger.info(f"[ANALYZE] Worker thread disabled, processing task {task_id} immediately")
                try:
                    # Process the task immediately
                    result = process_citation_task(task_id, 'text', task['data'])
                    if result and result.get('status') == 'success':
                        return jsonify({
                            'status': 'completed',
                            'task_id': task_id,
                            'results': result.get('results', []),
                            'citations': result.get('citations', []),
                            'case_names': result.get('case_names', []),
                            'metadata': result.get('metadata', {}),
                            'statistics': result.get('statistics', {}),
                            'summary': result.get('summary', {})
                        })
                    else:
                        return make_error_response(
                            "processing_error",
                            f"Task processing failed: {result.get('error', 'Unknown error')}",
                            status_code=500
                        )
                except Exception as e:
                    current_app.logger.error(f"[ANALYZE] Error processing task {task_id} immediately: {str(e)}")
                    return make_error_response(
                        "processing_error",
                        f"Error processing task: {str(e)}",
                        status_code=500
                    )

        # Handle URL input
        elif input_type == 'url' or ('url' in data and data['url']):
            url = data.get('url')
            
            # Comprehensive URL validation
            is_valid, error_message = validate_url_input(url)
            if not is_valid:
                return make_error_response(
                    "input_validation",
                    error_message,
                    status_code=400,
                    source_type="url",
                    source_name=url
                )
                
            # Add task to queue
            task = {
                'task_id': task_id,
                'type': 'url',
                'data': {
                    'url': url
                }
            }
            # Initialize task in active_requests
            set_task_status(task_id, 'queued', task['data'])
            
            # Enqueue task
            current_app.logger.info(f"[ANALYZE] RQ_AVAILABLE={RQ_AVAILABLE}, queue={queue}")
            if RQ_AVAILABLE and queue:
                # URL tasks can take longer due to web scraping, so use a longer timeout
                job = queue.enqueue(process_citation_task, task_id, 'url', task['data'], job_timeout=600)  # 10 minutes
                # Store the job ID mapping in Redis using the global connection
                try:
                    redis_conn.setex(f"task_to_job:{task_id}", 3600, job.id)  # Store for 1 hour
                    logger.info(f"{WORKER_LABEL} [ANALYZE] Stored task {task_id} -> job {job.id} mapping")
                except Exception as e:
                    logger.error(f"[ANALYZE] Failed to store job mapping for {task_id}: {e}")
                logger.info(f"{WORKER_LABEL} [ANALYZE] Added URL task {task_id} to RQ with 10-minute timeout")
            elif task_queue is not None:
                # Use fallback threading queue
                queue_size = task_queue.qsize() if task_queue else 'N/A'
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Adding URL task {task_id} to threading queue (queue size: {queue_size})")
                if task_queue:
                    task_queue.put((task_id, 'url', task['data']))
                new_queue_size = task_queue.qsize() if task_queue else 'N/A'
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added URL task {task_id} to threading queue (new queue size: {new_queue_size})")
            else:
                # Worker thread is disabled, process immediately
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Worker thread disabled, processing URL task {task_id} immediately")
                try:
                    # Process the task immediately
                    result = process_citation_task(task_id, 'url', task['data'])
                    if result and result.get('status') == 'success':
                        return jsonify({
                            'status': 'completed',
                            'task_id': task_id,
                            'results': result.get('results', []),
                            'citations': result.get('citations', []),
                            'case_names': result.get('case_names', []),
                            'metadata': result.get('metadata', {}),
                            'statistics': result.get('statistics', {}),
                            'summary': result.get('summary', {})
                        })
                    else:
                        return make_error_response(
                            "processing_error",
                            f"URL task processing failed: {result.get('error', 'Unknown error')}",
                            status_code=500
                        )
                except Exception as e:
                    current_app.logger.error(f"{WORKER_LABEL} [ANALYZE] Error processing URL task {task_id} immediately: {str(e)}")
                    return make_error_response(
                        "processing_error",
                        f"Error processing URL task: {str(e)}",
                        status_code=500
                    )
            
            # Return immediate response with task ID (only for queued tasks)
            if (RQ_AVAILABLE and queue) or (task_queue is not None):
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'URL received, processing started',
                    'metadata': {
                        'source_type': 'url',
                        'source_name': url,
                        'timestamp': datetime.utcnow().isoformat() + "Z",
                        'user_agent': request.headers.get("User-Agent")
                    }
                })
            
        else:
            # Fallback: if no valid input was processed, return an error response
            return jsonify({
                'status': 'error',
                'message': 'Invalid or missing input. Please provide text, file, or URL.'
            }), 400

    except Exception as e:
        current_app.logger.error(f"{WORKER_LABEL} [ANALYZE] Error: {str(e)}", exc_info=True)
        return make_error_response(
            "server_error",
            f"Server error: {str(e)}",
            status_code=500
        )


@vue_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """
    Get the status and result of an async analysis task.
    Always return a consistent response structure.
    Now includes progress and ETA fields when processing.
    """
    try:
        # 1. Check Redis for completed result first
        try:
            redis_result = redis_conn.get(f"task_result:{task_id}")
            if redis_result:
                result_data = json.loads(redis_result)
                current_app.logger.info(f"[TASK_STATUS] Redis result for {task_id}: status={result_data.get('status')}, progress={result_data.get('progress')}, step={result_data.get('current_step')}")
                is_completed = (
                    result_data.get('status') == 'completed' or
                    result_data.get('progress') == 100 or
                    result_data.get('current_step') == 'Complete'
                )
                if is_completed:
                    current_app.logger.info(f"[TASK_STATUS] Task {task_id} is completed, returning result from Redis")
                    return jsonify({
                        'status': 'completed',
                        'task_id': task_id,
                        'citations': result_data.get('citations', []),
                        'statistics': result_data.get('statistics', {}),
                        'summary': result_data.get('summary', {}),
                        'progress': 100,
                        'eta_seconds': 0,
                        'message': 'Analysis completed'
                    })
                else:
                    # Still processing, show progress and ETA
                    eta = _estimate_time_remaining(result_data)
                    return jsonify({
                        'status': 'processing',
                        'task_id': task_id,
                        'progress': result_data.get('progress', 0),
                        'current_chunk': result_data.get('current_chunk', 0),
                        'total_chunks': result_data.get('total_chunks', 1),
                        'eta_seconds': eta,
                        'message': 'Task is still processing',
                        'citations': [],
                        'statistics': {},
                        'summary': {}
                    })
        except Exception as redis_error:
            current_app.logger.warning(f"Redis check failed for task {task_id}: {redis_error}")

        # 2. Then check if task exists in active_requests
        if task_id in active_requests:
            task_info = active_requests[task_id]
            # If still processing
            if task_info['status'] in ('queued', 'processing'):
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'Task is still processing',
                    'citations': [],
                    'statistics': {},
                    'summary': {}
                })
            # If completed
            if task_info['status'] == 'completed':
                result = task_info.get('result', {})
                return jsonify({
                    'status': 'completed',
                    'task_id': task_id,
                    'citations': result.get('citations', []),
                    'statistics': result.get('statistics', {}),
                    'summary': result.get('summary', {}),
                    'message': result.get('message', 'Analysis completed')
                })
            # If failed
            if task_info['status'] == 'failed':
                return jsonify({
                    'status': 'error',
                    'task_id': task_id,
                    'message': task_info.get('error', 'Task failed'),
                    'citations': [],
                    'statistics': {},
                    'summary': {}
                }), 500

        # 3. If not in active_requests, check RQ job result as fallback
        try:
            job_id = redis_conn.get(f"task_to_job:{task_id}")
            if job_id:
                job_id = job_id.decode('utf-8') if isinstance(job_id, bytes) else job_id
                current_app.logger.info(f"[TASK_STATUS] Found job ID {job_id} for task {task_id}")
                job = queue.fetch_job(job_id)
            else:
                current_app.logger.info(f"[TASK_STATUS] No job ID mapping found for task {task_id}, trying direct fetch")
                job = queue.fetch_job(task_id)

            if job and job.is_finished:
                result = job.result
                if result and isinstance(result, dict):
                    return jsonify({
                        'status': 'completed',
                        'task_id': task_id,
                        'citations': result.get('citations', []),
                        'statistics': result.get('statistics', {}),
                        'summary': result.get('summary', {}),
                        'message': 'Analysis completed'
                    })
                elif result and isinstance(result, list):
                    return jsonify({
                        'status': 'completed',
                        'task_id': task_id,
                        'citations': result,
                        'statistics': {},
                        'summary': {},
                        'message': 'Analysis completed'
                    })
            elif job and job.is_failed:
                return jsonify({
                    'status': 'error',
                    'task_id': task_id,
                    'message': f'Task failed: {job.exc_info}',
                    'citations': [],
                    'statistics': {},
                    'summary': {}
                }), 500
            elif job and job.is_started:
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'Task is still processing',
                    'citations': [],
                    'statistics': {},
                    'summary': {}
                })
            elif job:
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'Task is still processing',
                    'citations': [],
                    'statistics': {},
                    'summary': {}
                })
        except Exception as redis_error:
            current_app.logger.warning(f"Redis check failed for task {task_id}: {redis_error}")

        # 4. Task not found
        return jsonify({
            'status': 'error',
            'message': 'Task ID not found',
            'task_id': task_id,
            'citations': [],
            'statistics': {},
            'summary': {}
        }), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'task_id': task_id,
            'message': f'Exception: {str(e)}',
            'citations': [],
            'statistics': {},
            'summary': {}
        }), 500

def _estimate_time_remaining(task_status):
    """
    Estimate time remaining based on task type and current progress.
    Returns estimated seconds remaining or None if cannot estimate.
    """
    try:
        task_type = task_status.get('type', 'unknown')
        progress = task_status.get('progress', 0)
        start_time = task_status.get('start_time', time.time())
        current_time = time.time()
        elapsed = current_time - start_time
        
        if progress <= 0:
            return None
            
        # Estimate based on task type and progress
        if task_type == 'file':
            # File processing: 30-120 seconds typical
            estimated_total = 60
        elif task_type == 'text':
            # Text processing: 10-30 seconds typical
            estimated_total = 20
        elif task_type == 'url':
            # URL processing: 60-300 seconds typical (includes download)
            estimated_total = 120
        else:
            estimated_total = 60
            
        if progress >= 100:
            return 0
            
        remaining = (estimated_total * (100 - progress) / 100) - elapsed
        return max(0, int(remaining))
        
    except Exception:
        return None

@vue_api.route('/version', methods=['GET'])
def version():
    """Version endpoint to return the current application version."""
    try:
        from src import __version__
        return jsonify({
            'version': __version__,
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Version endpoint error: {str(e)}")
        return jsonify({
            'version': 'unknown',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@vue_api.route('/processing_progress', methods=['GET'])
def processing_progress():
    """
    Compatibility endpoint for old static JavaScript frontend.
    Returns a simplified progress response that matches the expected format.
    """
    try:
        # Get the total parameter from the request (used by old frontend)
        total_citations = request.args.get('total', 0, type=int)
        
        # Check if there are any active requests
        if not active_requests:
            # No active processing
            return jsonify({
                'status': 'success',
                'processed_citations': 0,
                'total_citations': total_citations,
                'is_complete': True
            })
        
        # Find the most recent active request
        latest_task_id = None
        latest_start_time = 0
        
        for task_id, task_status in active_requests.items():
            start_time = task_status.get('start_time', 0)
            if start_time > latest_start_time:
                latest_start_time = start_time
                latest_task_id = task_id
        
        if not latest_task_id:
            return jsonify({
                'status': 'success',
                'processed_citations': 0,
                'total_citations': total_citations,
                'is_complete': True
            })
        
        # Get the latest task status
        task_status = active_requests[latest_task_id]
        status = task_status.get('status', 'unknown')
        
        # Calculate progress based on status
        if status == 'completed':
            # Task is complete
            citations = task_status.get('results', []) or task_status.get('citations', [])
            processed_count = len(citations) if citations else 0
            
            return jsonify({
                'status': 'success',
                'processed_citations': processed_count,
                'total_citations': max(total_citations, processed_count),
                'is_complete': True
            })
        
        elif status == 'failed':
            # Task failed
            return jsonify({
                'status': 'success',
                'processed_citations': 0,
                'total_citations': total_citations,
                'is_complete': True
            })
        
        elif status in ['queued', 'processing']:
            # Task is still processing
            # Estimate progress based on elapsed time
            start_time = task_status.get('start_time', time.time())
            elapsed_time = time.time() - start_time
            
            task_type = task_status.get('type', 'text')
            if task_type == 'file':
                estimated_total = 60  # 60 seconds for file processing
            elif task_type == 'url':
                estimated_total = 120  # 120 seconds for URL processing
            else:  # text
                estimated_total = 20  # 20 seconds for text processing
            
            # Calculate estimated progress (cap at 90% until complete)
            estimated_progress = min(int((elapsed_time / estimated_total) * 90), 90)
            processed_count = int((estimated_progress / 100) * total_citations) if total_citations > 0 else 0
            
            return jsonify({
                'status': 'success',
                'processed_citations': processed_count,
                'total_citations': total_citations,
                'is_complete': False
            })
        
        else:
            # Unknown status
            return jsonify({
                'status': 'success',
                'processed_citations': 0,
                'total_citations': total_citations,
                'is_complete': False
            })
            
    except Exception as e:
        logger.error(f"Processing progress endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'processed_citations': 0,
            'total_citations': 0,
            'is_complete': False
        }), 500

# Add comprehensive file upload security validation
def validate_file_upload(file):
    """
    Comprehensive file upload security validation.
    Returns (is_valid, error_message) tuple.
    """
    try:
        if not file or not file.filename:
            return False, "No file provided"
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_CONTENT_LENGTH:
            return False, f"File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB"
        if file_size == 0:
            return False, "File is empty"
        filename = secure_filename(file.filename)
        if not filename or filename == '':
            return False, "Invalid filename"
        # Check file extension (allow multiple dots, only check final extension)
        if '.' not in filename:
            return False, "Invalid file type. Allowed types: .pdf, .doc, .docx, .txt"
        file_ext = filename.rsplit('.', 1)[1].lower()
        allowed_exts = {'pdf', 'doc', 'docx', 'txt'}
        if file_ext not in allowed_exts:
            return False, "Invalid file type. Allowed types: .pdf, .doc, .docx, .txt"
        # Additional security checks
        suspicious_patterns = ['..', '\\', '/', ':', '*', '?', '"', '<', '>', '|']
        if any(pattern in file.filename for pattern in suspicious_patterns):
            return False, "Invalid filename: contains suspicious characters"
        # Check file content type (basic validation)
        allowed_mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
        }
        if file_ext in allowed_mime_types:
            expected_mime = allowed_mime_types[file_ext]
            if hasattr(file, 'content_type') and file.content_type:
                if file.content_type != expected_mime:
                    logger.warning(f"File content type mismatch: expected {expected_mime}, got {file.content_type}")
        return True, None
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False, f"File validation failed: {str(e)}"

# Add utility function for masking sensitive data in logs
def mask_sensitive_data(data, mask_char='*', visible_chars=4):
    """
    Safely mask sensitive data like API keys in logs.
    Shows only the first and last few characters.
    """
    if not data or len(data) <= visible_chars * 2:
        return mask_char * len(data) if data else ''
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars * 2) + data[-visible_chars:]

def safe_log_sensitive_data(logger_func, message, sensitive_data, mask_char='*', visible_chars=4):
    """
    Safely log messages that might contain sensitive data.
    """
    if sensitive_data:
        masked_data = mask_sensitive_data(sensitive_data, mask_char, visible_chars)
        logger_func(f"{message}: {masked_data}")
    else:
        logger_func(f"{message}: None")

# Add comprehensive input validation functions
def validate_text_input(text):
    """
    Comprehensive text input validation.
    Returns (is_valid, error_message) tuple.
    """
    try:
        # Check if text exists and is a string
        if not text or not isinstance(text, str):
            return False, "No valid text provided"
        
        # Check text length (reasonable limits for legal documents)
        text_trimmed = text.strip()
        if len(text_trimmed) == 0:
            return False, "Text is empty after trimming"
        
        if len(text_trimmed) > 1000000:  # 1MB limit for text
            return False, "Text is too long. Maximum length is 1,000,000 characters"
        
        # Check for suspicious patterns (basic XSS prevention)
        suspicious_patterns = [
            '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
            'data:text/html', 'data:application/javascript'
        ]
        
        text_lower = text_trimmed.lower()
        for pattern in suspicious_patterns:
            if pattern in text_lower:
                return False, f"Text contains suspicious content: {pattern}"
        
        # Check for excessive whitespace or control characters
        if len(text_trimmed) > 0 and text_trimmed.isspace():
            return False, "Text contains only whitespace"
        
        # Count control characters (excluding newlines and tabs)
        control_chars = sum(1 for c in text_trimmed if ord(c) < 32 and c not in '\n\r\t')
        if control_chars > len(text_trimmed) * 0.1:  # More than 10% control chars
            return False, "Text contains too many control characters"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Text validation error: {str(e)}")
        return False, f"Text validation failed: {str(e)}"

def validate_url_input(url):
    """
    Comprehensive URL input validation.
    Returns (is_valid, error_message) tuple.
    """
    try:
        # Check if URL exists and is a string
        if not url or not isinstance(url, str):
            return False, "No valid URL provided"
        
        url_trimmed = url.strip()
        if len(url_trimmed) == 0:
            return False, "URL is empty after trimming"
        
        if len(url_trimmed) > 2048:  # Standard URL length limit
            return False, "URL is too long. Maximum length is 2048 characters"
        
        # Basic URL format validation
        if not url_trimmed.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'javascript:', 'vbscript:', 'data:', 'file:', 'ftp://',
            'localhost', '127.0.0.1', '0.0.0.0', '::1'
        ]
        
        url_lower = url_trimmed.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                return False, f"URL contains suspicious content: {pattern}"
        
        # Try to parse the URL to ensure it's valid
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url_trimmed)
            if not parsed.netloc:
                return False, "Invalid URL format"
        except Exception:
            return False, "Invalid URL format"
        
        return True, None
        
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        return False, f"URL validation failed: {str(e)}"

def enrich_citation_with_database_fields(citation_result):
    """
    Enrich a citation result with all available database fields.
    
    Args:
        citation_result (dict): The citation result from verification
        
    Returns:
        dict: Enriched citation result with database fields
    """
    try:
        from src.database_manager import get_database_manager
        
        db_manager = get_database_manager()
        citation_text = citation_result.get('citation', '')
        
        logger.info(f"[enrich_citation_with_database_fields] Incoming citation: {citation_text}, verified: {citation_result.get('verified')}")
        
        if not citation_text:
            return citation_result
        
        # Query the database for this citation with flexible column handling
        query = """
            SELECT id, citation_text, case_name, year, court, reporter, volume, page,
                   parallel_citations, verification_result, verification_source, 
                   verification_confidence, found, is_verified
            FROM citations 
            WHERE citation_text = ?
        """
        
        # Add timestamp columns if they exist
        try:
            # Try to get timestamp columns
            timestamp_query = """
                SELECT created_at, updated_at, last_verified_at, verification_count, error_count
                FROM citations 
                WHERE citation_text = ?
            """
            timestamp_results = db_manager.execute_query(timestamp_query, (citation_text,))
            if timestamp_results:
                # Add timestamp fields to the main query
                query = """
                    SELECT id, citation_text, case_name, year, court, reporter, volume, page,
                           parallel_citations, verification_result, verification_source, 
                           verification_confidence, found, is_verified,
                           created_at, updated_at, last_verified_at, verification_count, error_count
                    FROM citations 
                    WHERE citation_text = ?
                """
        except Exception as e:
            logger.debug(f"Timestamp columns not available: {e}")
        
        results = db_manager.execute_query(query, (citation_text,))
        
        if results:
            db_record = results[0]
            
            logger.info(f"[enrich_citation_with_database_fields] Database record for {citation_text}: is_verified={db_record.get('is_verified')}, verification_result={db_record.get('verification_result')}")
            
            # Add database fields to the citation result, but DO NOT overwrite 'verified'
            enriched_result = citation_result.copy()
            enriched_result.update({
                'db_id': db_record.get('id'),
                'db_case_name': db_record.get('case_name'),
                'db_year': db_record.get('year'),
                'db_court': db_record.get('court'),
                'db_reporter': db_record.get('reporter'),
                'db_volume': db_record.get('volume'),
                'db_page': db_record.get('page'),
                'db_parallel_citations': db_record.get('parallel_citations'),
                'db_verification_result': db_record.get('verification_result'),
                'db_verification_source': db_record.get('verification_source'),
                'db_verification_confidence': db_record.get('verification_confidence'),
                'db_found': db_record.get('found'),
                'db_is_verified': db_record.get('is_verified'),
                'db_created_at': db_record.get('created_at'),
                'db_updated_at': db_record.get('updated_at'),
                'db_last_verified_at': db_record.get('last_verified_at'),
                'db_verification_count': db_record.get('verification_count'),
                'db_error_count': db_record.get('error_count')
            })
            # DO NOT overwrite 'verified' field
            logger.info(f"[enrich_citation_with_database_fields] Final result for {citation_text}: verified={enriched_result.get('verified')}, db_is_verified={enriched_result.get('db_is_verified')}")
            return enriched_result
        else:
            logger.info(f"[enrich_citation_with_database_fields] No database record found for {citation_text}, returning original result")
            return citation_result
            
    except Exception as e:
        logger.warning(f"Could not enrich citation with database fields: {e}")
        return citation_result

# Helper functions for Redis task status/results

def set_task_status(task_id, status, data=None):
    if REDIS_TASK_TRACKING and redis_conn:
        try:
            key = f"task_status:{task_id}"
            value = {"status": status}
            if data:
                value.update(data)
            redis_conn.setex(key, 3600, json.dumps(value))
        except Exception as e:
            logger.warning(f"[REDIS] Failed to set task status for {task_id}: {e}")
    else:
        active_requests[task_id] = {"status": status, **(data or {})}

def get_task_status(task_id):
    if REDIS_TASK_TRACKING and redis_conn:
        try:
            key = f"task_status:{task_id}"
            value = redis_conn.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"[REDIS] Failed to get task status for {task_id}: {e}")
    return active_requests.get(task_id)

def set_task_result(task_id, result):
    logger.info(f"[DEBUG] set_task_result called for {task_id} with result: {result}")
    print(f"[DEBUG] set_task_result called for {task_id} with result: {result}")
    
    if REDIS_TASK_TRACKING and redis_conn:
        try:
            key = f"task_result:{task_id}"
            logger.info(f"[DEBUG] About to serialize result to JSON for {task_id}")
            print(f"[DEBUG] About to serialize result to JSON for {task_id}")
            
            # Try to serialize the result
            try:
                json_str = json.dumps(result)
                logger.info(f"[DEBUG] JSON serialization successful for {task_id}: {json_str[:100]}...")
                print(f"[DEBUG] JSON serialization successful for {task_id}: {json_str[:100]}...")
            except Exception as json_error:
                logger.error(f"[DEBUG] JSON serialization failed for {task_id}: {json_error}")
                print(f"[DEBUG] JSON serialization failed for {task_id}: {json_error}")
                # Try to identify the problematic field
                for key_name, value in result.items():
                    try:
                        json.dumps({key_name: value})
                    except Exception as field_error:
                        logger.error(f"[DEBUG] Field '{key_name}' is not JSON serializable: {field_error}")
                        print(f"[DEBUG] Field '{key_name}' is not JSON serializable: {field_error}")
                raise json_error
            
            # Store in Redis
            redis_conn.setex(key, 3600, json_str)
            logger.info(f"[DEBUG] set_task_result wrote result to Redis key {key}")
            print(f"[DEBUG] set_task_result wrote result to Redis key {key}")
            
            # Verify it was stored
            stored_value = redis_conn.get(key)
            if stored_value:
                logger.info(f"[DEBUG] Verified result stored in Redis for {task_id}")
                print(f"[DEBUG] Verified result stored in Redis for {task_id}")
            else:
                logger.error(f"[DEBUG] Failed to verify result storage for {task_id}")
                print(f"[DEBUG] Failed to verify result storage for {task_id}")
                
        except Exception as e:
            logger.error(f"[REDIS] Failed to set task result for {task_id}: {e}")
            print(f"[REDIS] Failed to set task result for {task_id}: {e}")
            import traceback
            logger.error(f"[REDIS] Traceback: {traceback.format_exc()}")
            print(f"[REDIS] Traceback: {traceback.format_exc()}")
    else:
        logger.info(f"[DEBUG] Using in-memory storage for {task_id}")
        print(f"[DEBUG] Using in-memory storage for {task_id}")
        active_requests[task_id] = {"status": "completed", "result": result}

def get_task_result(task_id):
    if REDIS_TASK_TRACKING and redis_conn:
        try:
            key = f"task_result:{task_id}"
            value = redis_conn.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"[REDIS] Failed to get task result for {task_id}: {e}")
    task = active_requests.get(task_id)
    if task and task.get("status") == "completed":
        return task.get("result")
    return None
