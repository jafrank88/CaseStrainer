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
import redis
import threading

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

# Use EnhancedMultiSourceVerifier for multi-source citation verification
try:
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
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
    
    # Redis configuration
    try:
        redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_conn.ping()  # Test connection
        REDIS_AVAILABLE = True
        logger.info("[REDIS] Redis connection successful")
    except Exception as e:
        logger.warning(f"[REDIS] Redis not available: {e}")
        REDIS_AVAILABLE = False
        redis_conn = None
    
    TASK_CLEANUP_INTERVAL = 60  # seconds
    TASK_TTL = 300  # seconds (5 minutes in memory)
    REDIS_TASK_TTL = 600  # seconds (10 minutes in Redis)
    
    def cleanup_old_tasks():
        """Background thread to clean up old completed/failed tasks from memory"""
        while True:
            try:
                now = time.time()
                to_delete = []
                for task_id, task in list(active_requests.items()):
                    if task['status'] in ('completed', 'failed'):
                        end_time = task.get('end_time', task.get('start_time', now))
                        if now - end_time > TASK_TTL:
                            to_delete.append(task_id)
                            logger.debug(f"[CLEANUP] Marking task {task_id} for deletion (age: {now - end_time:.1f}s)")
                
                for task_id in to_delete:
                    del active_requests[task_id]
                    logger.info(f"[CLEANUP] Removed task {task_id} from memory")
                
                if to_delete:
                    logger.info(f"[CLEANUP] Cleaned up {len(to_delete)} old tasks")
                    
            except Exception as e:
                logger.error(f"[CLEANUP] Error in cleanup thread: {e}")
            
            time.sleep(TASK_CLEANUP_INTERVAL)
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
    cleanup_thread.start()
    logger.info("[CLEANUP] Task cleanup thread started")
    
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
            'rq_available': is_rq_available()  # PATCH: dynamic check
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
            'rq_available': is_rq_available()  # PATCH: dynamic check
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
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
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
                        logger.info(f"{WORKER_LABEL} [WORKER] Storing results for task {task_id}")
                        logger.info(f"{WORKER_LABEL} [WORKER] Result keys: {list(result.keys())}")
                        logger.info(f"{WORKER_LABEL} [WORKER] Citations count: {len(result.get('citations', []))}")
                        
                        active_requests[task_id].update({
                            'status': 'completed',
                            'citations': result.get('citations', []),
                            'metadata': result.get('metadata', {}),
                            'end_time': time.time(),
                            'progress': 100,
                            'total_citations': result.get('total_citations', 0),
                            'verified_citations': result.get('verified_citations', 0)
                        })
                        
                        logger.info(f"{WORKER_LABEL} [WORKER] Updated active_requests[{task_id}] keys: {list(active_requests[task_id].keys())}")
                        
                        # Persist result in Redis
                        if REDIS_AVAILABLE and redis_conn:
                            try:
                                redis_conn.setex(f"task_result:{task_id}", REDIS_TASK_TTL, json.dumps(active_requests[task_id]))
                                logger.info(f"[REDIS] Persisted completed task {task_id} to Redis")
                            except Exception as e:
                                logger.warning(f"[REDIS] Failed to persist task {task_id} in Redis: {e}")
                    else:
                        logger.warning(f"{WORKER_LABEL} [WORKER] Task {task_id} not found in active_requests")
                    
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
                        
                        # Persist failed result in Redis
                        if REDIS_AVAILABLE and redis_conn:
                            try:
                                redis_conn.setex(f"task_result:{task_id}", REDIS_TASK_TTL, json.dumps(active_requests[task_id]))
                                logger.info(f"[REDIS] Persisted failed task {task_id} to Redis")
                            except Exception as redis_e:
                                logger.warning(f"[REDIS] Failed to persist failed task {task_id} in Redis: {redis_e}")
                
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
            
            # Process citations in parallel for better performance
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            results = []
            results_lock = threading.Lock()
            
            def verify_single_citation(citation_info):
                """Verify a single citation with progress tracking."""
                try:
                    citation_text = citation_info['citation']
                    extracted_case_name = citation_info.get('case_name')
                    canonical_case_name = citation_info.get('canonical_case_name')
                    confidence = citation_info.get('confidence', 0.0)
                    method = citation_info.get('method', 'none')
                    extracted_date = citation_info.get('extracted_date')
                    
                    # Verify citation with enhanced verifier
                    result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                    
                    # Add enhanced case name information
                    result.update({
                        'case_name_extracted': extracted_case_name,  # From document text
                        'canonical_case_name': canonical_case_name,  # From API
                        'extraction_confidence': confidence,
                        'extraction_method': method,
                        'verified_in_text': citation_info.get('verified', False),
                        'similarity_score': citation_info.get('similarity'),
                        'position': citation_info.get('position'),
                        'citation_url': processor.enhanced_case_name_extractor.get_citation_url(citation_text) if processor.enhanced_case_name_extractor else None,
                        'canonical_source': citation_info.get('canonical_source', 'none'),  # Track source of canonical name
                        'url_source': citation_info.get('url_source', 'none'),  # Track source of citation URL
                        'extracted_date': extracted_date,  # Date extracted from user's document
                        'date_filed': result.get('date_filed')  # Canonical date from authoritative source
                    })
                    
                    # Add detailed logging for debugging
                    logger.info(f"[CITATION_PROCESSING] Citation: {citation_text}")
                    logger.info(f"[CITATION_PROCESSING]   - Extracted case name: {extracted_case_name}")
                    logger.info(f"[CITATION_PROCESSING]   - Canonical case name: {canonical_case_name}")
                    logger.info(f"[CITATION_PROCESSING]   - Citation URL: {result.get('citation_url')}")
                    logger.info(f"[CITATION_PROCESSING]   - Date filed: {result.get('date_filed')}")
                    logger.info(f"[CITATION_PROCESSING]   - Verification status: {result.get('verified')}")
                    logger.info(f"[CITATION_PROCESSING]   - Sources used: {result.get('sources', [])}")
                    
                    # Log any missing data for debugging
                    missing_data = []
                    if not canonical_case_name:
                        missing_data.append("canonical_case_name")
                    if not result.get('citation_url'):
                        missing_data.append("citation_url")
                    if not result.get('date_filed'):
                        missing_data.append("date_filed")
                    
                    if missing_data:
                        logger.warning(f"[CITATION_PROCESSING] Missing data for {citation_text}: {missing_data}")
                    
                    return result
                except Exception as e:
                    logger.error(f"Error verifying citation {citation_info.get('citation', 'unknown')}: {e}")
                    return {
                        'citation': citation_info.get('citation', 'unknown'),
                        'verified': False,
                        'error': str(e),
                        'case_name_extracted': citation_info.get('case_name'),
                        'canonical_case_name': citation_info.get('canonical_case_name'),
                        'extraction_confidence': citation_info.get('confidence', 0.0),
                        'extraction_method': citation_info.get('method', 'none'),
                        'verified_in_text': citation_info.get('verified', False),
                        'similarity_score': citation_info.get('similarity'),
                        'position': citation_info.get('position'),
                        'extracted_date': citation_info.get('extracted_date'),
                        'date_filed': None
                    }
            
            # Use ThreadPoolExecutor for parallel processing
            max_workers = min(8, len(citations))  # Limit to 8 workers to avoid overwhelming APIs
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all verification tasks
                future_to_citation = {
                    executor.submit(verify_single_citation, citation_info): citation_info
                    for citation_info in citations
                }
                
                # Process results as they complete
                for future in as_completed(future_to_citation):
                    try:
                        result = future.result()
                        with results_lock:
                            results.append(result)
                            
                        # Update progress if job tracking is available
                        if job:
                            current_progress = len(results)
                            total_citations = len(citations)
                            progress_percentage = min(90, 40 + int((current_progress / total_citations) * 50))
                            job.meta['progress'] = progress_percentage
                            job.meta['status'] = f'Verifying citations... ({current_progress}/{total_citations})'
                            job.meta['current_step'] = 'Citation verification'
                            job.save_meta()
                            
                    except Exception as e:
                        citation_info = future_to_citation[future]
                        logger.error(f"Error processing citation {citation_info.get('citation', 'unknown')}: {e}")
                        with results_lock:
                            results.append({
                                'citation': citation_info.get('citation', 'unknown'),
                                'verified': False,
                                'error': str(e),
                                'case_name_extracted': citation_info.get('case_name'),
                                'canonical_case_name': citation_info.get('canonical_case_name'),
                                'extraction_confidence': citation_info.get('confidence', 0.0),
                                'extraction_method': citation_info.get('method', 'none'),
                                'verified_in_text': citation_info.get('verified', False),
                                'similarity_score': citation_info.get('similarity'),
                                'position': citation_info.get('position'),
                                'extracted_date': citation_info.get('extracted_date'),
                                'date_filed': None
                            })
            
            # Sort results to maintain original order, but only if both lists are non-empty and all results have a matching citation
            if results and citations:
                try:
                    results.sort(key=lambda x: citations.index(next(c for c in citations if c['citation'] == x['citation'])))
                except StopIteration:
                    logger.warning("[PATCH] Could not find a matching citation for sorting. Skipping sort.")
            else:
                logger.info("[PATCH] Skipping sort: results or citations empty.")
            
            # Add metadata for file tasks
            file_metadata = {
                'file_name': os.path.basename(file_path) if file_path else None,
                'file_type': os.path.splitext(file_path)[1].lower() if file_path else None,
                'source_type': 'file',
                'source_name': os.path.basename(file_path) if file_path else None,
                'file_size': os.path.getsize(file_path) if file_path and os.path.exists(file_path) else None
            }
            return {'citations': results, 'status': 'success', 'metadata': file_metadata}
            
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
            
            # Process citations in parallel for better performance
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            results = []
            results_lock = threading.Lock()
            
            def verify_single_citation(citation_info):
                """Verify a single citation with progress tracking."""
                try:
                    citation_text = citation_info['citation']
                    extracted_case_name = citation_info.get('case_name')
                    canonical_case_name = citation_info.get('canonical_case_name')
                    confidence = citation_info.get('confidence', 0.0)
                    method = citation_info.get('method', 'none')
                    extracted_date = citation_info.get('extracted_date')
                    
                    # Verify citation with enhanced verifier
                    result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                    
                    # Add enhanced case name information
                    result.update({
                        'case_name_extracted': extracted_case_name,  # From document text
                        'canonical_case_name': canonical_case_name,  # From API
                        'extraction_confidence': confidence,
                        'extraction_method': method,
                        'verified_in_text': citation_info.get('verified', False),
                        'similarity_score': citation_info.get('similarity'),
                        'position': citation_info.get('position'),
                        'citation_url': processor.enhanced_case_name_extractor.get_citation_url(citation_text) if processor.enhanced_case_name_extractor else None,
                        'canonical_source': citation_info.get('canonical_source', 'none'),  # Track source of canonical name
                        'url_source': citation_info.get('url_source', 'none'),  # Track source of citation URL
                        'extracted_date': extracted_date,  # Date extracted from user's document
                        'date_filed': result.get('date_filed')  # Canonical date from authoritative source
                    })
                    
                    # Add detailed logging for debugging
                    logger.info(f"[CITATION_PROCESSING] Citation: {citation_text}")
                    logger.info(f"[CITATION_PROCESSING]   - Extracted case name: {extracted_case_name}")
                    logger.info(f"[CITATION_PROCESSING]   - Canonical case name: {canonical_case_name}")
                    logger.info(f"[CITATION_PROCESSING]   - Citation URL: {result.get('citation_url')}")
                    logger.info(f"[CITATION_PROCESSING]   - Date filed: {result.get('date_filed')}")
                    logger.info(f"[CITATION_PROCESSING]   - Verification status: {result.get('verified')}")
                    logger.info(f"[CITATION_PROCESSING]   - Sources used: {result.get('sources', [])}")
                    
                    # Log any missing data for debugging
                    missing_data = []
                    if not canonical_case_name:
                        missing_data.append("canonical_case_name")
                    if not result.get('citation_url'):
                        missing_data.append("citation_url")
                    if not result.get('date_filed'):
                        missing_data.append("date_filed")
                    
                    if missing_data:
                        logger.warning(f"[CITATION_PROCESSING] Missing data for {citation_text}: {missing_data}")
                    
                    return result
                except Exception as e:
                    logger.error(f"Error verifying citation {citation_info.get('citation', 'unknown')}: {e}")
                    return {
                        'citation': citation_info.get('citation', 'unknown'),
                        'verified': False,
                        'error': str(e),
                        'case_name_extracted': citation_info.get('case_name'),
                        'canonical_case_name': citation_info.get('canonical_case_name'),
                        'extraction_confidence': citation_info.get('confidence', 0.0),
                        'extraction_method': citation_info.get('method', 'none'),
                        'verified_in_text': citation_info.get('verified', False),
                        'similarity_score': citation_info.get('similarity'),
                        'position': citation_info.get('position'),
                        'extracted_date': citation_info.get('extracted_date'),
                        'date_filed': None
                    }
            
            # Use ThreadPoolExecutor for parallel processing
            max_workers = min(8, len(citations))  # Limit to 8 workers to avoid overwhelming APIs
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all verification tasks
                future_to_citation = {
                    executor.submit(verify_single_citation, citation_info): citation_info
                    for citation_info in citations
                }
                
                # Process results as they complete
                for future in as_completed(future_to_citation):
                    try:
                        result = future.result()
                        with results_lock:
                            results.append(result)
                            
                        # Update progress if job tracking is available
                        if job:
                            current_progress = len(results)
                            total_citations = len(citations)
                            progress_percentage = min(90, 40 + int((current_progress / total_citations) * 50))
                            job.meta['progress'] = progress_percentage
                            job.meta['status'] = f'Verifying citations... ({current_progress}/{total_citations})'
                            job.meta['current_step'] = 'Citation verification'
                            job.save_meta()
                            
                    except Exception as e:
                        citation_info = future_to_citation[future]
                        logger.error(f"Error processing citation {citation_info.get('citation', 'unknown')}: {e}")
                        with results_lock:
                            results.append({
                                'citation': citation_info.get('citation', 'unknown'),
                                'verified': False,
                                'error': str(e),
                                'case_name_extracted': citation_info.get('case_name'),
                                'canonical_case_name': citation_info.get('canonical_case_name'),
                                'extraction_confidence': citation_info.get('confidence', 0.0),
                                'extraction_method': citation_info.get('method', 'none'),
                                'verified_in_text': citation_info.get('verified', False),
                                'similarity_score': citation_info.get('similarity'),
                                'position': citation_info.get('position'),
                                'extracted_date': citation_info.get('extracted_date'),
                                'date_filed': None
                            })
            
            # Sort results to maintain original order, but only if both lists are non-empty and all results have a matching citation
            if results and citations:
                try:
                    results.sort(key=lambda x: citations.index(next(c for c in citations if c['citation'] == x['citation'])))
                except StopIteration:
                    logger.warning("[PATCH] Could not find a matching citation for sorting. Skipping sort.")
            else:
                logger.info("[PATCH] Skipping sort: results or citations empty.")
            
            text_metadata = {
                'source_type': 'text',
                'source_name': 'pasted_text',
                'text_length': len(text) if text else 0
            }
            return {'citations': results, 'status': 'success', 'metadata': text_metadata}
            
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
            
            # Process citations in parallel for better performance
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            results = []
            results_lock = threading.Lock()
            
            def verify_single_citation(citation_info):
                """Verify a single citation with progress tracking."""
                try:
                    citation_text = citation_info['citation']
                    extracted_case_name = citation_info.get('case_name')
                    canonical_case_name = citation_info.get('canonical_case_name')
                    confidence = citation_info.get('confidence', 0.0)
                    method = citation_info.get('method', 'none')
                    extracted_date = citation_info.get('extracted_date')
                    
                    # Verify citation with enhanced verifier
                    result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
                    
                    # Add enhanced case name information
                    result.update({
                        'case_name_extracted': extracted_case_name,  # From document text
                        'canonical_case_name': canonical_case_name,  # From API
                        'extraction_confidence': confidence,
                        'extraction_method': method,
                        'verified_in_text': citation_info.get('verified', False),
                        'similarity_score': citation_info.get('similarity'),
                        'position': citation_info.get('position'),
                        'citation_url': processor.enhanced_case_name_extractor.get_citation_url(citation_text) if processor.enhanced_case_name_extractor else None,
                        'canonical_source': citation_info.get('canonical_source', 'none'),  # Track source of canonical name
                        'url_source': citation_info.get('url_source', 'none'),  # Track source of citation URL
                        'extracted_date': extracted_date,  # Date extracted from user's document
                        'date_filed': result.get('date_filed')  # Canonical date from authoritative source
                    })
                    
                    # Add detailed logging for debugging
                    logger.info(f"[CITATION_PROCESSING] Citation: {citation_text}")
                    logger.info(f"[CITATION_PROCESSING]   - Extracted case name: {extracted_case_name}")
                    logger.info(f"[CITATION_PROCESSING]   - Canonical case name: {canonical_case_name}")
                    logger.info(f"[CITATION_PROCESSING]   - Citation URL: {result.get('citation_url')}")
                    logger.info(f"[CITATION_PROCESSING]   - Date filed: {result.get('date_filed')}")
                    logger.info(f"[CITATION_PROCESSING]   - Verification status: {result.get('verified')}")
                    logger.info(f"[CITATION_PROCESSING]   - Sources used: {result.get('sources', [])}")
                    
                    # Log any missing data for debugging
                    missing_data = []
                    if not canonical_case_name:
                        missing_data.append("canonical_case_name")
                    if not result.get('citation_url'):
                        missing_data.append("citation_url")
                    if not result.get('date_filed'):
                        missing_data.append("date_filed")
                    
                    if missing_data:
                        logger.warning(f"[CITATION_PROCESSING] Missing data for {citation_text}: {missing_data}")
                    
                    return result
                except Exception as e:
                    logger.error(f"Error verifying citation {citation_info.get('citation', 'unknown')}: {e}")
                    return {
                        'citation': citation_info.get('citation', 'unknown'),
                        'verified': False,
                        'error': str(e),
                        'case_name_extracted': citation_info.get('case_name'),
                        'canonical_case_name': citation_info.get('canonical_case_name'),
                        'extraction_confidence': citation_info.get('confidence', 0.0),
                        'extraction_method': citation_info.get('method', 'none'),
                        'verified_in_text': citation_info.get('verified', False),
                        'similarity_score': citation_info.get('similarity'),
                        'position': citation_info.get('position'),
                        'extracted_date': citation_info.get('extracted_date'),
                        'date_filed': None
                    }
            
            # Use ThreadPoolExecutor for parallel processing
            max_workers = min(8, len(citations))  # Limit to 8 workers to avoid overwhelming APIs
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all verification tasks
                future_to_citation = {
                    executor.submit(verify_single_citation, citation_info): citation_info
                    for citation_info in citations
                }
                
                # Process results as they complete
                for future in as_completed(future_to_citation):
                    try:
                        result = future.result()
                        with results_lock:
                            results.append(result)
                            
                        # Update progress if job tracking is available
                        if job:
                            current_progress = len(results)
                            total_citations = len(citations)
                            progress_percentage = min(90, 40 + int((current_progress / total_citations) * 50))
                            job.meta['progress'] = progress_percentage
                            job.meta['status'] = f'Verifying citations... ({current_progress}/{total_citations})'
                            job.meta['current_step'] = 'Citation verification'
                            job.save_meta()
                            
                    except Exception as e:
                        citation_info = future_to_citation[future]
                        logger.error(f"Error processing citation {citation_info.get('citation', 'unknown')}: {e}")
                        with results_lock:
                            results.append({
                                'citation': citation_info.get('citation', 'unknown'),
                                'verified': False,
                                'error': str(e),
                                'case_name_extracted': citation_info.get('case_name'),
                                'canonical_case_name': citation_info.get('canonical_case_name'),
                                'extraction_confidence': citation_info.get('confidence', 0.0),
                                'extraction_method': citation_info.get('method', 'none'),
                                'verified_in_text': citation_info.get('verified', False),
                                'similarity_score': citation_info.get('similarity'),
                                'position': citation_info.get('position'),
                                'extracted_date': citation_info.get('extracted_date'),
                                'date_filed': None
                            })
            
            # Sort results to maintain original order, but only if both lists are non-empty and all results have a matching citation
            if results and citations:
                try:
                    results.sort(key=lambda x: citations.index(next(c for c in citations if c['citation'] == x['citation'])))
                except StopIteration:
                    logger.warning("[PATCH] Could not find a matching citation for sorting. Skipping sort.")
            else:
                logger.info("[PATCH] Skipping sort: results or citations empty.")
            
            url_metadata = {
                'source_type': 'url',
                'source_name': url,
                'text_length': len(text) if text else 0
            }
            return {'citations': results, 'status': 'success', 'metadata': url_metadata}
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
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        if task_id in active_requests:
            # Try to include metadata if possible
            metadata = {}
            if task_type == 'file':
                file_path = task_data.get('file_path')
                metadata = {
                    'file_name': os.path.basename(file_path) if file_path else None,
                    'file_type': os.path.splitext(file_path)[1].lower() if file_path else None,
                    'source_type': 'file',
                    'source_name': os.path.basename(file_path) if file_path else None,
                    'file_size': os.path.getsize(file_path) if file_path and os.path.exists(file_path) else None
                }
            elif task_type == 'text':
                text = task_data.get('text')
                metadata = {
                    'source_type': 'text',
                    'source_name': 'pasted_text',
                    'text_length': len(text) if text else 0
                }
            elif task_type == 'url':
                url = task_data.get('url')
                metadata = {
                    'source_type': 'url',
                    'source_name': url,
                    'text_length': len(url) if url else 0
                }
            active_requests[task_id].update({
                'status': 'failed',
                'error': error_msg,
                'metadata': metadata
            })
        return {'status': 'failed', 'error': error_msg, 'metadata': metadata}

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
            
            # Comprehensive file validation
            is_valid, error_message = validate_file_upload(file)
            if not is_valid:
                return make_error_response(
                    "file_validation",
                    error_message,
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
            current_app.logger.info(f"[ANALYZE] Immediate/Async decision: text_len={len(text_trimmed)}, words={len(text_trimmed.split())}, patterns={[w for w in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL'] if w in text_trimmed.upper()]}")
            if (len(text_trimmed) < 50 and  # Short text
                any(char.isdigit() for char in text_trimmed) and  # Contains numbers
                any(word in text_trimmed.upper() for word in ['U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WL']) and  # Contains citation patterns
                len(text_trimmed.split()) <= 10):  # Few words
                # Immediate (synchronous) response
                current_app.logger.info(f"[ANALYZE] Using immediate (synchronous) response for citation: {text_trimmed}")
                
                try:
                    # Import the enhanced validator
                    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
                    verifier = EnhancedMultiSourceVerifier()
                    
                    # Validate the citation
                    result = verifier.verify_citation(text_trimmed, extracted_case_name=None)
                    processing_time = time.time() - start_time
                    
                    # Format the response
                    response_data = {
                        'citations': [{
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
                        }]
                    }
                    
                    current_app.logger.info(f"[ANALYZE] Single citation '{text_trimmed}' validation result: {result.get('verified', False)}")
                    
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
            # Try Redis before returning 404
            if REDIS_AVAILABLE and redis_conn:
                try:
                    redis_result = redis_conn.get(f"task_result:{task_id}")
                    if redis_result:
                        task_status = json.loads(redis_result)
                        current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} loaded from Redis")
                    else:
                        current_app.logger.warning(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} not found in memory or Redis")
                        return make_error_response(
                            "task_not_found",
                            f"Task {task_id} not found",
                            status_code=404
                        )
                except Exception as e:
                    current_app.logger.error(f"[REDIS] Error loading task {task_id} from Redis: {e}")
                    return make_error_response(
                        "task_not_found",
                        f"Task {task_id} not found",
                        status_code=404
                    )
            else:
                current_app.logger.warning(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} not found")
                return make_error_response(
                    "task_not_found",
                    f"Task {task_id} not found",
                    status_code=404
                )
        else:
            task_status = active_requests[task_id]
        
        current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} status: {task_status['status']}")
        
        # Always calculate and include progress and time estimates
        start_time = task_status.get('start_time', time.time())
        elapsed_time = time.time() - start_time
        
        # Calculate progress based on status and elapsed time
        if task_status['status'] == 'queued':
            # For queued tasks, show minimal progress
            progress = 5
            status_message = 'Waiting in queue...'
            current_step = 'Queue'
        elif task_status['status'] == 'processing':
            # For processing tasks, estimate progress based on elapsed time and task type
            task_type = task_status.get('type', 'text')
            if task_type == 'file':
                estimated_total = 60  # 60 seconds for file processing
            elif task_type == 'url':
                estimated_total = 120  # 120 seconds for URL processing
            else:  # text
                estimated_total = 20  # 20 seconds for text processing
            
            progress = min(int((elapsed_time / estimated_total) * 90), 90)  # Cap at 90% until complete
            status_message = task_status.get('status_message', 'Processing citations...')
            current_step = task_status.get('current_step', 'Citation extraction and verification')
        elif task_status['status'] == 'completed':
            progress = 100
            status_message = 'Processing complete'
            current_step = 'Complete'
        elif task_status['status'] == 'failed':
            progress = 0
            status_message = task_status.get('error', 'Processing failed')
            current_step = 'Failed'
        else:
            progress = 0
            status_message = 'Unknown status'
            current_step = 'Unknown'
        
        # Calculate remaining time
        remaining_time = _estimate_time_remaining({
            'type': task_status.get('type', 'text'),
            'progress': progress,
            'start_time': start_time
        })
        
        # Define processing steps based on task type
        task_type = task_status.get('type', 'text')
        if task_type == 'file':
            steps = [
                ['File upload and validation', 5],
                ['Text extraction', 15],
                ['Citation extraction', 10],
                ['Citation verification', 25],
                ['Results compilation', 5]
            ]
        elif task_type == 'url':
            steps = [
                ['URL validation', 2],
                ['Content download', 30],
                ['Text extraction', 15],
                ['Citation extraction', 10],
                ['Citation verification', 50],
                ['Results compilation', 13]
            ]
        else:  # text
            steps = [
                ['Text validation', 2],
                ['Citation extraction', 8],
                ['Citation verification', 8],
                ['Results compilation', 2]
            ]
        
        # Calculate estimated total time
        estimated_total_time = sum(step[1] for step in steps)
        
        # Build detailed step progress for frontend
        step_progress_list = []
        step_start = 0
        for i, (step_name, step_time) in enumerate(steps):
            step_dict = {'step': step_name, 'estimated_time': step_time}
            if current_step == step_name:
                # Current step: estimate progress
                step_elapsed = elapsed_time - step_start
                progress = min(100, int((step_elapsed / step_time) * 100)) if step_time > 0 else 0
                step_dict['progress'] = progress
                step_dict['status'] = 'In Progress'
            elif current_step == 'Complete':
                # All steps are completed
                step_dict['progress'] = 100
                step_dict['status'] = 'Completed'
            elif current_step == 'Failed':
                # All steps are failed
                step_dict['progress'] = 0
                step_dict['status'] = 'Failed'
            else:
                # Check if this step is before the current step
                try:
                    current_step_index = [s[0] for s in steps].index(current_step)
                    if i < current_step_index:
                        # Completed steps
                        step_dict['progress'] = 100
                        step_dict['status'] = 'Completed'
                    else:
                        # Pending steps
                        step_dict['progress'] = 0
                        step_dict['status'] = 'Pending'
                except ValueError:
                    # Current step not found in steps list, treat as pending
                    step_dict['progress'] = 0
                    step_dict['status'] = 'Pending'
            step_progress_list.append(step_dict)
            step_start += step_time

        # Update task status with progress info
        task_status.update({
            'progress': progress,
            'status_message': status_message,
            'current_step': current_step,
            'elapsed_time': int(elapsed_time),
            'remaining_time': remaining_time,
            'estimated_total_time': estimated_total_time,
            'steps': step_progress_list  # Use detailed step progress
        })
        
        # Add progress tracking for queued tasks
        if task_status['status'] == 'queued':
            # If more than 2 seconds have passed, update status to processing
            if elapsed_time > 2:
                estimated_progress = min(int(elapsed_time * 5), 85)  # Conservative progress estimate
                active_requests[task_id].update({
                    'status': 'processing',
                    'progress': estimated_progress,
                    'status_message': 'Processing citations...',
                    'current_step': 'Citation extraction and verification'
                })
                current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} updated to processing (elapsed: {elapsed_time:.1f}s, progress: {estimated_progress}%)")
        
        # Return the complete task status
        response_data = {
            'task_id': task_id,
            'status': task_status['status'],
            'progress': progress,
            'status_message': status_message,
            'current_step': current_step,
            'elapsed_time': int(elapsed_time),
            'remaining_time': remaining_time,
            'estimated_total_time': estimated_total_time,
            'steps': step_progress_list,  # Use detailed step progress
            'type': task_type
        }
        
        # Always include citations/results if present
        if task_status['status'] == 'completed':
            # Prefer 'results', fallback to 'citations', always include at least an empty list
            current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task {task_id} completed, checking for results")
            current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Task status keys: {list(task_status.keys())}")
            
            if 'results' in task_status:
                response_data['results'] = task_status['results']
                current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Using 'results' field, count: {len(task_status['results'])}")
            elif 'citations' in task_status:
                response_data['results'] = task_status['citations']
                current_app.logger.info(f"{WORKER_LABEL} [TASK_STATUS] Using 'citations' field, count: {len(task_status['citations'])}")
            else:
                response_data['results'] = []
                current_app.logger.warning(f"{WORKER_LABEL} [TASK_STATUS] No results or citations found in task status")
        elif task_status['status'] == 'failed' and 'error' in task_status:
            response_data['error'] = task_status['error']
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"{WORKER_LABEL} [TASK_STATUS] Error checking task {task_id}: {str(e)}")
        return make_error_response(
            "internal_error",
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

# Add comprehensive file upload security validation
def validate_file_upload(file):
    """
    Comprehensive file upload security validation.
    Returns (is_valid, error_message) tuple.
    """
    try:
        # Import centralized config
        from src.config import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
        
        # Check if file exists
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check file size
        file.seek(0, 2)  # Seek to end to get file size
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_CONTENT_LENGTH:
            return False, f"File too large. Maximum size is {MAX_CONTENT_LENGTH // (1024*1024)}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Validate filename
        filename = secure_filename(file.filename)
        if not filename or filename == '':
            return False, "Invalid filename"
        
        # Check file extension
        if '.' not in filename:
            return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Additional security checks
        # Check for double extensions (e.g., file.pdf.exe)
        if filename.count('.') > 1:
            return False, "Invalid filename: multiple extensions detected"
        
        # Check for suspicious patterns in filename
        suspicious_patterns = ['..', '\\', '/', ':', '*', '?', '"', '<', '>', '|']
        if any(pattern in file.filename for pattern in suspicious_patterns):
            return False, "Invalid filename: contains suspicious characters"
        
        # Check file content type (basic validation)
        allowed_mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'rtf': 'application/rtf'
        }
        
        if file_ext in allowed_mime_types:
            expected_mime = allowed_mime_types[file_ext]
            if hasattr(file, 'content_type') and file.content_type:
                if file.content_type != expected_mime:
                    logger.warning(f"File content type mismatch: expected {expected_mime}, got {file.content_type}")
                    # Don't reject based on content type alone as it can be unreliable
        
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
