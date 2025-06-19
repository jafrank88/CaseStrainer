"""
Vue.js API Endpoints for CaseStrainer

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
from citation_extractor import extract_all_citations, verify_citation
from file_utils import extract_text_from_file
from citation_utils import deduplicate_citations
from enhanced_validator_production import make_error_response
import tempfile
from citation_verification import CitationVerifier
from rq import Queue
from redis import Redis
from rq import get_current_job
from citation_processor import CitationProcessor

# PATCH: Disable RQ death penalty on Windows before any RQ import
from src.rq_windows_patch import patch_rq_for_windows
patch_rq_for_windows()

# Configure logging first, before anything else
def configure_logging():
    """Configure logging for the application."""
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'backend_{timestamp}.log')
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file)
            ]
        )
        
        # Create logger for this module
        logger = logging.getLogger(__name__)
        logger.info("=== Logging Configuration ===")
        logger.info(f"Log file: {log_file}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        return logger
        
    except Exception as e:
        print(f"Failed to configure logging: {str(e)}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(message)s'
        )
        return logging.getLogger(__name__)

# Configure logging and get logger
logger = configure_logging()

logger.info("=== Backend Startup ===")
logger.info("Importing required modules...")

try:
    # Create Blueprint instead of Flask app
    logger.info("Creating Flask Blueprint...")
    vue_api = Blueprint('vue_api', __name__)
    
    logger.info("Flask Blueprint created successfully")
    
except Exception as e:
    logger.error(f"Failed to create Flask Blueprint: {str(e)}\n{traceback.format_exc()}")
    raise

# Initialize global variables
logger.info("Initializing global variables...")
try:
    active_requests = {}
    request_timestamps = []
    request_timestamps_lock = Lock()
    
    # Constants - OPTIMIZED for better performance
    COURTLISTENER_RATE_LIMIT = 180  # requests per minute
    COURTLISTENER_RATE_WINDOW = 60  # seconds
    COURTLISTENER_BATCH_SIZE = 20   # citations per batch (increased from 10)
    COURTLISTENER_BATCH_INTERVAL = 1  # seconds between batches (reduced from 3)
    COURTLISTENER_CITATIONS_PER_MINUTE = 150  # citations per minute for timeout calculation (increased from 90)
    DEFAULT_TIMEOUT = 300  # 5 minutes default timeout
    
    logger.info("Global variables initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize global variables: {str(e)}\n{traceback.format_exc()}")
    raise

# Add a health check endpoint
@vue_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the backend is running."""
    try:
        worker_status = "unknown"
        queue_size = 0
        
        if not RQ_AVAILABLE:
            try:
                worker_status = "running" if worker_thread.is_alive() and worker_running else "stopped"
                queue_size = task_queue.qsize()
            except:
                worker_status = "error"
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'active_requests': len(active_requests),
            'worker_status': worker_status,
            'queue_size': queue_size,
            'rq_available': RQ_AVAILABLE
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
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
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_db = int(os.environ.get('REDIS_DB', 0))
    
    redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db)
    queue = Queue('casestrainer', connection=redis_conn)
    
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
    queue = None

# Windows-compatible fallback: Simple threading-based task queue
if not RQ_AVAILABLE:
    import threading
    import queue as python_queue
    
    # Simple in-memory task queue for Windows compatibility
    task_queue = python_queue.Queue()
    worker_thread = None
    worker_running = False
    
    def worker_loop():
        global worker_running
        worker_running = True
        print("[WORKER] Thread-based worker started")  # Immediate output
        logger.info("[WORKER] Thread-based worker started")
        
        while worker_running:
            try:
                # Get next task from queue (with timeout)
                try:
                    task = task_queue.get(timeout=1.0)
                    print(f"[WORKER] Got task from queue: {task[0]} (queue size now: {task_queue.qsize()})")  # Immediate output
                    logger.info(f"[WORKER] Got task from queue: {task[0]} (queue size now: {task_queue.qsize()})")
                except python_queue.Empty:
                    # Log every 30 seconds that we're still alive
                    if int(time.time()) % 30 == 0:
                        print("[WORKER] No tasks in queue, waiting...")  # Immediate output
                        logger.debug("[WORKER] No tasks in queue, waiting...")
                    continue
                
                task_id, task_type, task_data = task
                print(f"[WORKER] Processing task {task_id} of type {task_type}")  # Immediate output
                logger.info(f"[WORKER] Processing task {task_id} of type {task_type}")
                
                # Update task status to processing
                if task_id in active_requests:
                    active_requests[task_id]['status'] = 'processing'
                    active_requests[task_id]['progress'] = 10
                
                try:
                    # Process the task using the same function
                    print(f"[WORKER] Calling process_citation_task for {task_id}")  # Immediate output
                    result = process_citation_task(task_id, task_type, task_data)
                    
                    # Update task status with results
                    if task_id in active_requests:
                        active_requests[task_id].update({
                            'status': 'completed',
                            'citations': result.get('citations', []),
                            'end_time': time.time(),
                            'progress': 100,
                            'total_citations': result.get('total_citations', 0),
                            'verified_citations': result.get('verified_citations', 0)
                        })
                    
                    print(f"[WORKER] Task {task_id} completed successfully")  # Immediate output
                    logger.info(f"[WORKER] Task {task_id} completed successfully")
                    
                except Exception as e:
                    print(f"[WORKER] Error processing task {task_id}: {e}")  # Immediate output
                    logger.error(f"[WORKER] Error processing task {task_id}: {e}")
                    if task_id in active_requests:
                        active_requests[task_id].update({
                            'status': 'failed',
                            'error': str(e),
                            'end_time': time.time(),
                            'progress': 0
                        })
                
                finally:
                    task_queue.task_done()
                    
            except Exception as e:
                print(f"[WORKER] Worker loop error: {e}")  # Immediate output
                logger.error(f"[WORKER] Worker loop error: {e}")
                time.sleep(1)
        
        print("[WORKER] Thread-based worker stopped")  # Immediate output
        logger.info("[WORKER] Thread-based worker stopped")
    
    # Start worker thread
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    logger.info("[WORKER] Thread-based worker started")

    # Add a function to check if worker is running
    def is_worker_running():
        return worker_thread.is_alive() and worker_running

def process_citation_task(task_id, task_type, task_data):
    import time
    import logging
    import os
    import tempfile
    import json
    from datetime import datetime
    
    print(f"[PROCESS] Starting process_citation_task for {task_id} of type {task_type}")  # Immediate output
    
    # Initialize RQ connection for job updates
    try:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_db = int(os.environ.get('REDIS_DB', 0))
        
        redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db)
        rq_queue = Queue('casestrainer', connection=redis_conn)
        job = rq_queue.fetch_job(task_id)
    except Exception as e:
        logger.warning(f"Could not connect to Redis for job updates: {e}")
        job = None
    
    logger = logging.getLogger(__name__)
    
    try:
        print(f"[PROCESS] Task {task_id} of type {task_type} - starting processing")  # Immediate output
        logger.info(f"[RQ WORKER] Starting task {task_id} of type {task_type}")
        
        # Initialize progress tracking
        if job:
            job.meta['progress'] = 0
            job.meta['status'] = 'Starting...'
            job.meta['current_step'] = 'Initializing'
            job.save_meta()
        
        if task_type == 'file':
            file_path = task_data.get('file_path')
            logger.info(f"[RQ WORKER] Task {task_id} file_path: {file_path}")
            if not file_path or not os.path.exists(file_path):
                logger.error(f"[RQ WORKER] File not found: {file_path}")
                raise ValueError(f"File not found: {file_path}")
            
            # Update progress: File validation
            if job:
                job.meta['progress'] = 10
                job.meta['status'] = 'Validating file...'
                job.meta['current_step'] = 'File validation'
                job.save_meta()
            
            from file_utils import extract_text_from_file
            from citation_processor import CitationProcessor
            from citation_verification import CitationVerifier
            
            # Extract text from file
            text_result = extract_text_from_file(file_path)
            if isinstance(text_result, dict):
                if not text_result.get('success', True):
                    logger.error(f"[RQ WORKER] File extraction error: {text_result.get('error')}")
                    return {'status': 'error', 'error': text_result.get('error', 'Failed to extract text from file')}
                text = text_result.get('text', '')
            else:
                text = text_result
            
            # Use enhanced citation processor
            processor = CitationProcessor()
            citations = processor.extract_citations(text, extract_case_names=True)
            
            # Pass extracted case names to verification
            verifier = CitationVerifier()
            results = []
            for c in citations:
                citation_text = c['citation']
                extracted_case_name = c.get('case_name')
                result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                result['case_name_extracted'] = extracted_case_name
                results.append(result)
            return {'citations': results, 'status': 'success'}
            
        elif task_type == 'text':
            text = task_data.get('text')
            logger.info(f"[RQ WORKER] Task {task_id} processing text input")
            if not text:
                logger.error(f"[RQ WORKER] No text provided for task {task_id}")
                raise ValueError("No text provided")
            
            # Update progress: Text validation
            if job:
                job.meta['progress'] = 15
                job.meta['status'] = 'Processing text...'
                job.meta['current_step'] = 'Text processing'
                job.save_meta()
            
            from citation_processor import CitationProcessor
            from citation_verification import CitationVerifier
            
            processor = CitationProcessor()
            citations = processor.extract_citations(text, extract_case_names=True)
            verifier = CitationVerifier()
            results = []
            for c in citations:
                citation_text = c['citation']
                extracted_case_name = c.get('case_name')
                result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                result['case_name_extracted'] = extracted_case_name
                results.append(result)
            return {'citations': results, 'status': 'success'}
            
        elif task_type == 'url':
            url = task_data.get('url')
            logger.info(f"[RQ WORKER] Task {task_id} processing url input: {url}")
            if not url:
                logger.error(f"[RQ WORKER] No URL provided for task {task_id}")
                raise ValueError("No URL provided")
            
            # Update progress: URL validation
            if job:
                job.meta['progress'] = 5
                job.meta['status'] = 'Validating URL...'
                job.meta['current_step'] = 'URL validation'
                job.save_meta()
            
            from enhanced_validator_production import extract_text_from_url
            from citation_processor import CitationProcessor
            from citation_verification import CitationVerifier
            
            # Update progress: Downloading content
            if job:
                job.meta['progress'] = 20
                job.meta['status'] = 'Downloading content from URL...'
                job.meta['current_step'] = 'Content download'
                job.save_meta()
            
            logger.info(f"[RQ WORKER] Task {task_id} starting URL text extraction...")
            text_result = extract_text_from_url(url)
            logger.info(f"[RQ WORKER] Task {task_id} URL text extraction result: {text_result.get('status')}")
            
            if text_result.get('status') != 'success' or not text_result.get('text'):
                error_msg = f"Failed to extract text from URL: {text_result.get('error', 'Unknown error')}"
                logger.error(f"[RQ WORKER] Task {task_id} {error_msg}")
                raise ValueError(error_msg)
            
            text = text_result['text']
            logger.info(f"[RQ WORKER] Task {task_id} extracted {len(text)} characters from URL")
            
            # Update progress: Text extraction complete
            if job:
                job.meta['progress'] = 40
                job.meta['status'] = 'Extracting citations from content...'
                job.meta['current_step'] = 'Citation extraction'
                job.save_meta()
            
            logger.info(f"[RQ WORKER] Task {task_id} starting citation extraction from text...")
            processor = CitationProcessor()
            citations = processor.extract_citations(text, extract_case_names=True)
            verifier = CitationVerifier()
            results = []
            for c in citations:
                citation_text = c['citation']
                extracted_case_name = c.get('case_name')
                result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                result['case_name_extracted'] = extracted_case_name
                results.append(result)
            return {'citations': results, 'status': 'success'}
        else:
            logger.error(f"[RQ WORKER] Unknown task type: {task_type}")
            raise ValueError(f"Unknown task type: {task_type}")
            
        # Final progress update
        if job:
            job.meta['progress'] = 100
            job.meta['status'] = 'Completed successfully'
            job.meta['current_step'] = 'Complete'
            job.save_meta()
            
        logger.info(f"[RQ WORKER] Task {task_id} completed successfully")
        return result_data
    except Exception as e:
        logger.error(f"[RQ WORKER] Error processing task {task_id}: {e}")
        
        # Update progress on error
        if job:
            job.meta['progress'] = 0
            job.meta['status'] = f'Error: {str(e)}'
            job.meta['current_step'] = 'Error'
            job.save_meta()
            
        error_data = {
            'status': 'failed',
            'error': str(e),
            'end_time': time.time(),
            'task_id': task_id,
            'progress': 0
        }
        try:
            result_file = os.path.join(tempfile.gettempdir(), f"casestrainer_result_{task_id}.json")
            with open(result_file, 'w') as f:
                json.dump(error_data, f)
        except:
            pass
        raise

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
        # Log request details for debugging
        current_app.logger.info(f"[ANALYZE] Received {request.method} request to /api/analyze")
        current_app.logger.info(f"[ANALYZE] Headers: {dict(request.headers)}")
        current_app.logger.info(f"[ANALYZE] Form data: {request.form.to_dict() if request.form else 'No form data'}")
        current_app.logger.info(f"[ANALYZE] Files: {list(request.files.keys()) if request.files else 'No files'}")
        
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
        current_app.logger.info(f"[ANALYZE] Assigned task ID: {task_id}")

        # Handle file upload
        if 'file' in request.files or 'file' in request.form or (request.is_json and 'file' in data):
            file = request.files.get('file')
            if not file:
                return make_error_response(
                    "input_validation",
                    "No file provided",
                    status_code=400
                )
            
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
                active_requests[task_id] = {
                    'status': 'queued',
                    'start_time': time.time(),
                    'type': 'file',
                    'data': task['data'],
                    'metadata': {
                        'source_type': 'file',
                        'source_name': filename,
                        'file_type': file_ext,
                        'timestamp': datetime.utcnow().isoformat() + "Z",
                        'user_agent': request.headers.get("User-Agent")
                    }
                }
                
                # Enqueue task
                if RQ_AVAILABLE and queue:
                    queue.enqueue(process_citation_task, task_id, 'file', task['data'])
                    current_app.logger.info(f"[ANALYZE] Added file task {task_id} to RQ")
                else:
                    # Use fallback threading queue
                    current_app.logger.info(f"[ANALYZE] Adding file task {task_id} to threading queue (queue size: {task_queue.qsize()})")
                    task_queue.put((task_id, 'file', task['data']))
                    current_app.logger.info(f"[ANALYZE] Added file task {task_id} to threading queue (new queue size: {task_queue.qsize()})")
                
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
                # Clean up temporary file if it exists
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                return make_error_response(
                    "file_upload",
                    f"Failed to handle file upload: {str(e)}",
                    status_code=400,
                    source_type="file",
                    source_name=filename
                )

        # Handle text input
        elif input_type == 'text' or ('text' in data and data['text']):
            text = data.get('text')
            if not text or not isinstance(text, str):
                return make_error_response(
                    "input_validation",
                    "No valid text provided",
                    status_code=400,
                    source_type="text",
                    source_name="pasted_text"
                )
                
            # Add task to queue
            task = {
                'task_id': task_id,
                'type': 'text',
                'data': {
                    'text': text
                }
            }
            # Initialize task in active_requests
            active_requests[task_id] = {
                'status': 'queued',
                'start_time': time.time(),
                'type': 'text',
                'data': task['data'],
                'metadata': {
                    'source_type': 'text',
                    'source_name': 'pasted_text',
                    'timestamp': datetime.utcnow().isoformat() + "Z",
                    'user_agent': request.headers.get("User-Agent")
                }
            }
            
            # Enqueue task
            if RQ_AVAILABLE and queue:
                queue.enqueue(process_citation_task, task_id, 'text', task['data'])
                current_app.logger.info(f"[ANALYZE] Added text task {task_id} to RQ")
            else:
                # Use fallback threading queue
                current_app.logger.info(f"[ANALYZE] Adding text task {task_id} to threading queue (queue size: {task_queue.qsize()})")
                task_queue.put((task_id, 'text', task['data']))
                current_app.logger.info(f"[ANALYZE] Added text task {task_id} to threading queue (new queue size: {task_queue.qsize()})")
            
            # Return immediate response with task ID
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

        # Handle URL input
        elif input_type == 'url' or ('url' in data and data['url']):
            url = data.get('url')
            if not url or not isinstance(url, str):
                return make_error_response(
                    "input_validation",
                    "No valid URL provided",
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
            active_requests[task_id] = {
                'status': 'queued',
                'start_time': time.time(),
                'type': 'url',
                'data': task['data'],
                'metadata': {
                    'source_type': 'url',
                    'source_name': url,
                    'timestamp': datetime.utcnow().isoformat() + "Z",
                    'user_agent': request.headers.get("User-Agent")
                }
            }
            
            # Enqueue task
            if RQ_AVAILABLE and queue:
                # URL tasks can take longer due to web scraping, so use a longer timeout
                queue.enqueue(process_citation_task, task_id, 'url', task['data'], job_timeout=600)  # 10 minutes
                current_app.logger.info(f"[ANALYZE] Added URL task {task_id} to RQ with 10-minute timeout")
            else:
                # Use fallback threading queue
                current_app.logger.info(f"[ANALYZE] Adding URL task {task_id} to threading queue (queue size: {task_queue.qsize()})")
                task_queue.put((task_id, 'url', task['data']))
                current_app.logger.info(f"[ANALYZE] Added URL task {task_id} to threading queue (new queue size: {task_queue.qsize()})")
            
            # Return immediate response with task ID
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
            return make_error_response(
                "input_validation",
                "No valid input provided",
                status_code=400
            )

    except Exception as e:
        current_app.logger.error(f"[ANALYZE] Error: {str(e)}", exc_info=True)
        return make_error_response(
            "server_error",
            f"Server error: {str(e)}",
            status_code=500
        )


@vue_api.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    """
    Check the status of an asynchronous processing task.
    Returns the current status and any available results.
    """
    try:
        current_app.logger.info(f"[TASK_STATUS] Checking status for task {task_id}")
        
        # Check if task exists in active_requests
        if task_id not in active_requests:
            current_app.logger.warning(f"[TASK_STATUS] Task {task_id} not found")
            return make_error_response(
                "task_not_found",
                f"Task {task_id} not found",
                status_code=404
            )
            
        task_status = active_requests[task_id]
        current_app.logger.info(f"[TASK_STATUS] Task {task_id} status: {task_status['status']}")
        
        # Check RQ job metadata for progress updates
        try:
            from rq import Queue
            from redis import Redis
            redis_conn = Redis(host='localhost', port=6379, db=0)
            rq_queue = Queue('casestrainer', connection=redis_conn)
            
            # Find the job by task_id (we need to search through jobs)
            # For now, we'll check if there's a job with this task_id in the meta
            jobs = rq_queue.jobs
            rq_job = None
            for job in jobs:
                if hasattr(job, 'meta') and job.meta.get('task_id') == task_id:
                    rq_job = job
                    break
            
            # If we found the RQ job, get its progress
            if rq_job and rq_job.meta:
                progress = rq_job.meta.get('progress', 0)
                status_message = rq_job.meta.get('status', 'Processing...')
                current_step = rq_job.meta.get('current_step', 'Unknown')
                
                # Update active_requests with progress info
                active_requests[task_id].update({
                    'progress': progress,
                    'status_message': status_message,
                    'current_step': current_step
                })
                
                current_app.logger.info(f"[TASK_STATUS] Task {task_id} progress: {progress}% - {status_message}")
        except Exception as e:
            current_app.logger.warning(f"[TASK_STATUS] Could not get RQ progress for task {task_id}: {e}")
        
        # Check if RQ worker has completed and written results to file
        if task_status['status'] == 'queued':
            result_file = os.path.join(tempfile.gettempdir(), f"casestrainer_result_{task_id}.json")
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r') as f:
                        result_data = json.load(f)
                    
                    # Update active_requests with the result
                    if result_data.get('status') == 'completed':
                        active_requests[task_id].update({
                            'status': 'completed',
                            'citations': result_data.get('citations', []),
                            'end_time': result_data.get('end_time'),
                            'progress': result_data.get('progress', 100),
                            'total_citations': result_data.get('total_citations', 0),
                            'verified_citations': result_data.get('verified_citations', 0)
                        })
                        current_app.logger.info(f"[TASK_STATUS] Task {task_id} completed, loaded from result file")
                    elif result_data.get('status') == 'failed':
                        active_requests[task_id].update({
                            'status': 'failed',
                            'error': result_data.get('error', 'Unknown error'),
                            'end_time': result_data.get('end_time'),
                            'progress': result_data.get('progress', 0)
                        })
                        current_app.logger.error(f"[TASK_STATUS] Task {task_id} failed: {result_data.get('error')}")
                    
                    # Clean up the result file
                    try:
                        os.remove(result_file)
                        current_app.logger.info(f"[TASK_STATUS] Cleaned up result file for task {task_id}")
                    except Exception as e:
                        current_app.logger.warning(f"[TASK_STATUS] Failed to clean up result file for task {task_id}: {e}")
                        
                except Exception as e:
                    current_app.logger.error(f"[TASK_STATUS] Error reading result file for task {task_id}: {e}")
        
        # Get updated task status
        task_status = active_requests[task_id]
        
        # If task is complete, return results
        if task_status['status'] == 'completed':
            return jsonify({
                'status': 'completed',
                'task_id': task_id,
                'citations': task_status.get('citations', []),
                'metadata': task_status.get('metadata', {}),
                'progress': task_status.get('progress', 100),
                'total_citations': task_status.get('total_citations', 0),
                'verified_citations': task_status.get('verified_citations', 0)
            })
            
        # If task failed, return error
        elif task_status['status'] == 'failed':
            return make_error_response(
                "task_error",
                task_status.get('error', 'Unknown error occurred'),
                status_code=500,
                metadata=task_status.get('metadata', {})
            )
            
        # Task is still processing or queued - return progress info
        return jsonify({
            'status': task_status['status'],  # This will be 'queued', 'processing', etc.
            'task_id': task_id,
            'message': f"Task is {task_status['status']}",
            'metadata': task_status.get('metadata', {}),
            'progress': task_status.get('progress', 0),
            'status_message': task_status.get('status_message', 'Processing...'),
            'current_step': task_status.get('current_step', 'Unknown'),
            'estimated_time_remaining': _estimate_time_remaining(task_status)
        })
        
    except Exception as e:
        current_app.logger.error(f"[TASK_STATUS] Error checking task status: {str(e)}", exc_info=True)
        return make_error_response(
            "server_error",
            f"Error checking task status: {str(e)}",
            status_code=500
        )

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
