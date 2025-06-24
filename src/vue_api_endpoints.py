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
from citation_processor import CitationProcessor
import sqlite3

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

# Use EnhancedMultiSourceVerifier for multi-source citation verification
try:
    from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    CitationVerifier = EnhancedMultiSourceVerifier  # Alias for compatibility
    logger.info("Using EnhancedMultiSourceVerifier for multi-source citation verification")
except ImportError as e:
    logger.warning(f"Could not import EnhancedMultiSourceVerifier: {e}")
    logger.warning("Falling back to CitationVerifier")
    from citation_verification import CitationVerifier

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
    
    WORKER_ENV = os.environ.get("CASTRAINER_ENV", "production").lower()
    WORKER_LABEL = ""  # Remove misleading [DEV] labels
    
    logger.info("Global variables initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize global variables: {str(e)}\n{traceback.format_exc()}")
    raise

def check_redis():
    try:
        redis_conn.ping()
        return "ok"
    except Exception:
        return "down"

def check_db():
    try:
        conn = sqlite3.connect(os.path.join(os.getcwd(), 'data', 'citations.db'))
        conn.execute('SELECT 1')
        conn.close()
        return "ok"
    except Exception:
        return "down"

def check_rq_worker():
    try:
        if RQ_AVAILABLE:
            from rq import Worker
            workers = Worker.all(connection=redis_conn)
            return "ok" if workers else "down"
        else:
            return "ok" if worker_thread and worker_thread.is_alive() else "down"
    except Exception:
        return "down"

@vue_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the backend is running and all components are healthy."""
    try:
        worker_status = check_rq_worker()
        queue_size = 0
        server_stats = {}
        flask_status = "ok"  # If this endpoint responds, Flask is running
        redis_status = check_redis()
        db_status = check_db()

        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime_seconds = time.time() - server_start_time if 'server_start_time' in globals() else 0
        uptime = get_uptime() if 'get_uptime' in globals() else "unknown"

        response_data = {
            'status': 'healthy' if all([flask_status=="ok", redis_status=="ok", worker_status=="ok", db_status=="ok"]) else 'degraded',
            'timestamp': time.time(),
            'current_time': current_time,
            'uptime': uptime,
            'uptime_seconds': uptime_seconds,
            'flask_app': flask_status,
            'redis': redis_status,
            'rq_worker': worker_status,
            'database': db_status,
            'active_requests': len(active_requests),
            'rq_available': RQ_AVAILABLE
        }
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@vue_api.route('/server_stats', methods=['GET'])
def server_stats():
    """Detailed server statistics and restart tracking endpoint."""
    try:
        stats = {
            'timestamp': time.time(),
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'active_requests': len(active_requests),
            'rq_available': RQ_AVAILABLE
        }
        
        if not RQ_AVAILABLE and 'get_server_stats' in globals():
            try:
                server_stats = get_server_stats()
                stats.update(server_stats)
                
                # Add detailed worker info
                stats['worker_thread_alive'] = worker_thread.is_alive() if worker_thread else False
                stats['worker_running'] = worker_running
                stats['queue_size'] = task_queue.qsize() if task_queue else 0
                
                # Calculate uptime in different formats
                uptime_seconds = stats.get('uptime_seconds', 0)
                stats['uptime_hours'] = round(uptime_seconds / 3600, 2)
                stats['uptime_days'] = round(uptime_seconds / 86400, 2)
                
                # Add stability indicators
                stats['stability_score'] = 'excellent' if uptime_seconds > 3600 else 'good' if uptime_seconds > 300 else 'starting'
                stats['needs_restart'] = uptime_seconds > 86400  # Flag if running more than 24 hours
                
            except Exception as e:
                logger.error(f"Error getting server stats: {e}")
                stats['error'] = str(e)
        
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
    
    # Restart tracking
    server_start_time = time.time()
    restart_count = 0
    
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_uptime():
        uptime_seconds = time.time() - server_start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def worker_loop():
        global worker_running
        worker_running = True
        timestamp = get_timestamp()
        uptime = get_uptime()
        print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Thread-based worker started (uptime: {uptime})")  # Immediate output
        logger.info(f"{WORKER_LABEL} [WORKER] Thread-based worker started (uptime: {uptime})")
        
        # Initialize the verifier for database expansion
        try:
            from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
            logger.info(f"{WORKER_LABEL} [WORKER] Initialized EnhancedMultiSourceVerifier for database expansion")
        except Exception as e:
            logger.error(f"{WORKER_LABEL} [WORKER] Failed to initialize verifier for database expansion: {e}")
            verifier = None
        
        # Track when we last expanded the database to avoid too frequent calls
        last_expansion_time = 0
        expansion_interval = 300  # 5 minutes between expansion attempts
        
        while worker_running:
            try:
                # Get next task from queue (with timeout)
                try:
                    task = task_queue.get(timeout=1.0)
                    timestamp = get_timestamp()
                    uptime = get_uptime()
                    print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Got task from queue: {task[0]} (queue size now: {task_queue.qsize()}) (uptime: {uptime})")  # Immediate output
                    logger.info(f"{WORKER_LABEL} [WORKER] Got task from queue: {task[0]} (queue size now: {task_queue.qsize()}) (uptime: {uptime})")
                except python_queue.Empty:
                    # Check if we should expand the database (only if enough time has passed)
                    current_time = time.time()
                    if (verifier and 
                        current_time - last_expansion_time > expansion_interval and 
                        task_queue.qsize() == 0):
                        
                        try:
                            timestamp = get_timestamp()
                            uptime = get_uptime()
                            print(f"{WORKER_LABEL} [{timestamp}] [WORKER] No tasks in queue, expanding database... (uptime: {uptime})")
                            logger.info(f"{WORKER_LABEL} [WORKER] No tasks in queue, expanding database... (uptime: {uptime})")
                            
                            # Try to expand database with up to 5 new verifications
                            expanded_count = verifier.expand_database_from_unverified(limit=5)
                            
                            if expanded_count > 0:
                                timestamp = get_timestamp()
                                uptime = get_uptime()
                                print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Expanded database with {expanded_count} new verifications (uptime: {uptime})")
                                logger.info(f"{WORKER_LABEL} [WORKER] Expanded database with {expanded_count} new verifications (uptime: {uptime})")
                            
                            last_expansion_time = current_time
                            
                        except Exception as e:
                            timestamp = get_timestamp()
                            uptime = get_uptime()
                            print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Database expansion failed: {e} (uptime: {uptime})")
                            logger.error(f"{WORKER_LABEL} [WORKER] Database expansion failed: {e} (uptime: {uptime})")
                    
                    # Log every 30 seconds that we're still alive
                    if int(time.time()) % 30 == 0:
                        timestamp = get_timestamp()
                        uptime = get_uptime()
                        print(f"{WORKER_LABEL} [{timestamp}] [WORKER] No tasks in queue, waiting... (uptime: {uptime})")  # Immediate output
                        logger.debug(f"{WORKER_LABEL} [WORKER] No tasks in queue, waiting... (uptime: {uptime})")
                    continue
                
                task_id, task_type, task_data = task
                timestamp = get_timestamp()
                uptime = get_uptime()
                print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Processing task {task_id} of type {task_type} (uptime: {uptime})")  # Immediate output
                logger.info(f"{WORKER_LABEL} [WORKER] Processing task {task_id} of type {task_type} (uptime: {uptime})")
                
                # Update task status to processing
                if task_id in active_requests:
                    active_requests[task_id]['status'] = 'processing'
                    active_requests[task_id]['progress'] = 10
                
                try:
                    # Process the task using the same function
                    timestamp = get_timestamp()
                    uptime = get_uptime()
                    print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Calling process_citation_task for {task_id} (uptime: {uptime})")  # Immediate output
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
                    
                    timestamp = get_timestamp()
                    uptime = get_uptime()
                    print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Task {task_id} completed successfully (uptime: {uptime})")  # Immediate output
                    logger.info(f"{WORKER_LABEL} [WORKER] Task {task_id} completed successfully (uptime: {uptime})")
                    
                except Exception as e:
                    timestamp = get_timestamp()
                    uptime = get_uptime()
                    print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Error processing task {task_id}: {e} (uptime: {uptime})")  # Immediate output
                    logger.error(f"{WORKER_LABEL} [WORKER] Error processing task {task_id}: {e} (uptime: {uptime})")
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
                timestamp = get_timestamp()
                uptime = get_uptime()
                print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Worker loop error: {e} (uptime: {uptime})")  # Immediate output
                logger.error(f"{WORKER_LABEL} [WORKER] Worker loop error: {e} (uptime: {uptime})")
                time.sleep(1)
        
        timestamp = get_timestamp()
        uptime = get_uptime()
        print(f"{WORKER_LABEL} [{timestamp}] [WORKER] Thread-based worker stopped (uptime: {uptime})")  # Immediate output
        logger.info(f"{WORKER_LABEL} [WORKER] Thread-based worker stopped (uptime: {uptime})")
    
    # Start worker thread
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    timestamp = get_timestamp()
    uptime = get_uptime()
    logger.info(f"{WORKER_LABEL} [WORKER] Thread-based worker started (uptime: {uptime})")

    # Add a function to check if worker is running
    def is_worker_running():
        return worker_thread.is_alive() and worker_running
    
    # Add restart tracking function
    def get_server_stats():
        return {
            'start_time': server_start_time,
            'uptime': get_uptime(),
            'uptime_seconds': time.time() - server_start_time,
            'restart_count': restart_count,
            'worker_alive': is_worker_running()
        }

def process_citation_task(task_id, task_type, task_data):
    import logging
    logger = logging.getLogger(__name__)
    import time
    import os
    import tempfile
    import json
    from datetime import datetime
    
    print(f"{WORKER_LABEL} [PROCESS] Starting process_citation_task for {task_id} of type {task_type}")  # Immediate output
    
    # Initialize RQ connection for job updates
    try:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_db = int(os.environ.get('REDIS_DB', 0))
        
        redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db)
        rq_queue = Queue('casestrainer', connection=redis_conn)
        job = rq_queue.fetch_job(task_id)
    except Exception as e:
        logger.warning(f"{WORKER_LABEL} [PROCESS] Could not connect to Redis for job updates: {e}")
        job = None
    
    logger = logging.getLogger(__name__)
    
    try:
        print(f"{WORKER_LABEL} [PROCESS] Task {task_id} of type {task_type} - starting processing")  # Immediate output
        logger.info(f"{WORKER_LABEL} [RQ WORKER] Starting task {task_id} of type {task_type}")
        
        # Initialize progress tracking
        if job:
            job.meta['progress'] = 0
            job.meta['status'] = 'Starting...'
            job.meta['current_step'] = 'Initializing'
            job.save_meta()
        
        if task_type == 'file':
            file_path = task_data.get('file_path')
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} file_path: {file_path}")
            if not file_path or not os.path.exists(file_path):
                logger.error(f"{WORKER_LABEL} [RQ WORKER] File not found: {file_path}")
                raise ValueError(f"File not found: {file_path}")
            
            # Update progress: File validation
            if job:
                job.meta['progress'] = 10
                job.meta['status'] = 'Validating file...'
                job.meta['current_step'] = 'File validation'
                job.save_meta()
            
            from file_utils import extract_text_from_file
            from citation_processor import CitationProcessor
            
            # Extract text from file
            text_result = extract_text_from_file(file_path)
            if isinstance(text_result, dict):
                if not text_result.get('success', True):
                    logger.error(f"{WORKER_LABEL} [RQ WORKER] File extraction error: {text_result.get('error')}")
                    return {'status': 'error', 'error': text_result.get('error', 'Failed to extract text from file')}
                text = text_result.get('text', '')
            else:
                text = text_result
            
            # Use enhanced citation processor
            processor = CitationProcessor()
            citations = processor.extract_citations(text, extract_case_names=True)
            
            # Use enhanced multi-source verifier for all task types
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
            results = []
            for c in citations:
                citation_text = c['citation']
                extracted_case_name = c.get('case_name')
                canonical_case_name = c.get('canonical_case_name')
                confidence = c.get('confidence', 0.0)
                method = c.get('method', 'none')
                
                # Verify citation with enhanced verifier
                result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                
                # Add enhanced case name information
                result.update({
                    'case_name_extracted': extracted_case_name,  # From document text
                    'canonical_case_name': canonical_case_name,  # From API
                    'extraction_confidence': confidence,
                    'extraction_method': method,
                    'verified_in_text': c.get('verified', False),
                    'similarity_score': c.get('similarity'),
                    'position': c.get('position'),
                    'citation_url': processor.enhanced_case_name_extractor.get_citation_url(citation_text) if processor.enhanced_case_name_extractor else None,
                    'canonical_source': c.get('canonical_source', 'none'),  # Track source of canonical name
                    'url_source': c.get('url_source', 'none')  # Track source of citation URL
                })
                results.append(result)
            return {'citations': results, 'status': 'success'}
            
        elif task_type == 'text':
            text = task_data.get('text')
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} processing text input")
            if not text:
                logger.error(f"{WORKER_LABEL} [RQ WORKER] No text provided for task {task_id}")
                raise ValueError("No text provided")
            
            # Update progress: Text validation
            if job:
                job.meta['progress'] = 15
                job.meta['status'] = 'Processing text...'
                job.meta['current_step'] = 'Text processing'
                job.save_meta()
            
            from citation_processor import CitationProcessor
            
            processor = CitationProcessor()
            citations = processor.extract_citations(text, extract_case_names=True)
            
            # Use enhanced multi-source verifier for all task types
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
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
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} processing url input: {url}")
            if not url:
                logger.error(f"{WORKER_LABEL} [RQ WORKER] No URL provided for task {task_id}")
                raise ValueError("No URL provided")
            
            # Update progress: URL validation
            if job:
                job.meta['progress'] = 5
                job.meta['status'] = 'Validating URL...'
                job.meta['current_step'] = 'URL validation'
                job.save_meta()
            
            from enhanced_validator_production import extract_text_from_url
            from citation_processor import CitationProcessor
            
            # Update progress: Downloading content
            if job:
                job.meta['progress'] = 20
                job.meta['status'] = 'Downloading content from URL...'
                job.meta['current_step'] = 'Content download'
                job.save_meta()
            
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} starting URL text extraction...")
            text_result = extract_text_from_url(url)
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} URL text extraction result: {text_result.get('status')}")
            
            if text_result.get('status') != 'success' or not text_result.get('text'):
                error_msg = f"Failed to extract text from URL: {text_result.get('error', 'Unknown error')}"
                logger.error(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} {error_msg}")
                raise ValueError(error_msg)
            
            text = text_result['text']
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} extracted {len(text)} characters from URL")
            
            # Update progress: Text extraction complete
            if job:
                job.meta['progress'] = 40
                job.meta['status'] = 'Extracting citations from content...'
                job.meta['current_step'] = 'Citation extraction'
                job.save_meta()
            
            logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} starting citation extraction from text...")
            processor = CitationProcessor()
            citations = processor.extract_citations(text, extract_case_names=True)
            
            # Use enhanced multi-source verifier for all task types
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
            results = []
            for c in citations:
                citation_text = c['citation']
                extracted_case_name = c.get('case_name')
                canonical_case_name = c.get('canonical_case_name')
                confidence = c.get('confidence', 0.0)
                method = c.get('method', 'none')
                
                # Verify citation with enhanced verifier
                result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                
                # Add enhanced case name information
                result.update({
                    'case_name_extracted': extracted_case_name,  # From document text
                    'canonical_case_name': canonical_case_name,  # From API
                    'extraction_confidence': confidence,
                    'extraction_method': method,
                    'verified_in_text': c.get('verified', False),
                    'similarity_score': c.get('similarity'),
                    'position': c.get('position'),
                    'citation_url': processor.enhanced_case_name_extractor.get_citation_url(citation_text) if processor.enhanced_case_name_extractor else None,
                    'canonical_source': c.get('canonical_source', 'none'),  # Track source of canonical name
                    'url_source': c.get('url_source', 'none')  # Track source of citation URL
                })
                results.append(result)
            return {'citations': results, 'status': 'success'}
        else:
            logger.error(f"{WORKER_LABEL} [RQ WORKER] Unknown task type: {task_type}")
            raise ValueError(f"Unknown task type: {task_type}")
            
        # Final progress update
        if job:
            job.meta['progress'] = 100
            job.meta['status'] = 'Completed successfully'
            job.meta['current_step'] = 'Complete'
            job.save_meta()
            
        logger.info(f"{WORKER_LABEL} [RQ WORKER] Task {task_id} completed successfully")
        return result_data
    except Exception as e:
        logger.error(f"{WORKER_LABEL} [RQ WORKER] Error processing task {task_id}: {e}")
        
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
        current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Received {request.method} request to /api/analyze")
        current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Headers: {dict(request.headers)}")
        current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Form data: {request.form.to_dict() if request.form else 'No form data'}")
        current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Files: {list(request.files.keys()) if request.files else 'No files'}")
        
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
                    current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added file task {task_id} to RQ")
                else:
                    # Use fallback threading queue
                    current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Adding file task {task_id} to threading queue (queue size: {task_queue.qsize()})")
                    task_queue.put((task_id, 'file', task['data']))
                    current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added file task {task_id} to threading queue (new queue size: {task_queue.qsize()})")
                
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
            
            # Check if this is a single citation (likely a single citation format)
            # Single citations are typically short and contain specific patterns
            text_trimmed = text.strip()
            if (len(text_trimmed) < 50 and  # Short text
                any(char.isdigit() for char in text_trimmed) and  # Contains numbers
                any(word in text_trimmed.upper() for word in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL']) and  # Contains citation patterns
                len(text_trimmed.split()) <= 10):  # Few words
                
                # Handle as single citation synchronously
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Detected single citation: {text_trimmed}")
                
                try:
                    # Import the enhanced validator
                    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
                    verifier = EnhancedMultiSourceVerifier()
                    
                    # Validate the citation
                    result = verifier.verify_citation(text_trimmed, extracted_case_name=None)
                    processing_time = time.time() - start_time
                    
                    # Format the response
                    response_data = {
                        'citation': text_trimmed,
                        'valid': result.get('verified', False),
                        'verified': result.get('verified', False),
                        'case_name': result.get('case_name', ''),
                        'confidence': result.get('confidence', 0.0),
                        'source': result.get('source', 'Unknown'),
                        'details': result.get('details', {}),
                        'metadata': {
                            'source_type': 'citation',
                            'source_name': 'single_citation',
                            'processing_time': processing_time,
                            'timestamp': datetime.utcnow().isoformat() + "Z",
                            'user_agent': request.headers.get("User-Agent")
                        }
                    }
                    
                    current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Single citation '{text_trimmed}' validation result: {result.get('verified', False)}")
                    
                    return jsonify(response_data)
                    
                except Exception as e:
                    current_app.logger.error(f"{WORKER_LABEL} [ANALYZE] Error validating single citation '{text_trimmed}': {str(e)}")
                    # Fall back to async processing
                    current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Falling back to async processing for citation: {text_trimmed}")
                
            # Continue with async processing for longer text or if single citation validation failed
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
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added text task {task_id} to RQ")
            else:
                # Use fallback threading queue
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Adding text task {task_id} to threading queue (queue size: {task_queue.qsize()})")
                task_queue.put((task_id, 'text', task['data']))
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added text task {task_id} to threading queue (new queue size: {task_queue.qsize()})")
            
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
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added URL task {task_id} to RQ with 10-minute timeout")
            else:
                # Use fallback threading queue
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Adding URL task {task_id} to threading queue (queue size: {task_queue.qsize()})")
                task_queue.put((task_id, 'url', task['data']))
                current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Added URL task {task_id} to threading queue (new queue size: {task_queue.qsize()})")
            
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
        current_app.logger.error(f"{WORKER_LABEL} [ANALYZE] Error: {str(e)}", exc_info=True)
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
        current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Checking status for task {task_id}")
        
        # Check if task exists in active_requests
        if task_id not in active_requests:
            current_app.logger.warning(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} not found")
            return make_error_response(
                "task_not_found",
                f"Task {task_id} not found",
                status_code=404
            )
            
        task_status = active_requests[task_id]
        current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} status: {task_status['status']}")
        
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
                
                current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} progress: {progress}% - {status_message}")
        except Exception as e:
            current_app.logger.warning(f"{WORKER_LABEL} [TASK_STATUS] Could not get RQ progress for task {task_id}: {e}")
        
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
                        current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} completed, loaded from result file")
                    elif result_data.get('status') == 'failed':
                        active_requests[task_id].update({
                            'status': 'failed',
                            'error': result_data.get('error', 'Unknown error'),
                            'end_time': result_data.get('end_time'),
                            'progress': result_data.get('progress', 0)
                        })
                        current_app.logger.error(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} failed: {result_data.get('error')}")
                    
                    # Clean up the result file
                    try:
                        os.remove(result_file)
                        current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Cleaned up result file for task {task_id}")
                    except Exception as e:
                        current_app.logger.warning(f"{WORKER_LABEL} [TASK_STATUS] Failed to clean up result file for task {task_id}: {e}")
                        
                except Exception as e:
                    current_app.logger.error(f"{WORKER_LABEL} [TASK_STATUS] Error reading result file for task {task_id}: {e}")
        
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
        current_app.logger.error(f"{WORKER_LABEL} [TASK_STATUS] Error checking task status: {str(e)}", exc_info=True)
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

@vue_api.route('/validate-citation', methods=['POST', 'OPTIONS'])
def validate_citation():
    """
    Synchronous endpoint for validating a single citation.
    Returns immediate results without async processing.
    """
    start_time = time.time()
    
    try:
        # Handle OPTIONS request for CORS preflight
        if request.method == 'OPTIONS':
            response = make_response(jsonify({'status': 'ok'}), 200)
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

        # Get citation from request
        data = request.get_json(silent=True) or {}
        citation = data.get('citation', '').strip()
        
        if not citation:
            return make_error_response(
                "input_validation",
                "No citation provided",
                status_code=400,
                source_type="citation",
                source_name="single_citation"
            )
        
        current_app.logger.info(f"{WORKER_LABEL} [VALIDATE_CITATION] Validating citation: {citation}")
        
        # Import the enhanced validator
        try:
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
        except ImportError:
            current_app.logger.error(f"{WORKER_LABEL} [VALIDATE_CITATION] Failed to import EnhancedMultiSourceVerifier")
            return make_error_response(
                "server_error",
                "Citation validation service not available",
                status_code=500
            )
        
        # Validate the citation
        try:
            result = verifier.verify_citation(citation)
            processing_time = time.time() - start_time
            
            # Format the response
            response_data = {
                'citation': citation,
                'valid': result.get('verified', False),
                'verified': result.get('verified', False),
                'case_name': result.get('case_name', ''),
                'confidence': result.get('confidence', 0.0),
                'source': result.get('source', 'Unknown'),
                'details': result.get('details', {}),
                'metadata': {
                    'source_type': 'citation',
                    'source_name': 'single_citation',
                    'processing_time': processing_time,
                    'timestamp': datetime.utcnow().isoformat() + "Z",
                    'user_agent': request.headers.get("User-Agent")
                }
            }
            
            current_app.logger.info(f"{WORKER_LABEL} [VALIDATE_CITATION] Citation '{citation}' validation result: {result.get('verified', False)}")
            
            return jsonify(response_data)
            
        except Exception as e:
            current_app.logger.error(f"{WORKER_LABEL} [VALIDATE_CITATION] Error validating citation '{citation}': {str(e)}")
            return make_error_response(
                "validation_error",
                f"Error validating citation: {str(e)}",
                status_code=500,
                source_type="citation",
                source_name="single_citation"
            )
            
    except Exception as e:
        current_app.logger.error(f"{WORKER_LABEL} [VALIDATE_CITATION] Server error: {str(e)}", exc_info=True)
        return make_error_response(
            "server_error",
            f"Server error: {str(e)}",
            status_code=500
        )

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
