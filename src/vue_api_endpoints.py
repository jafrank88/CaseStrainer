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
logger = logging.getLogger(__name__)
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
import sqlite3
import platform
from src.citation_utils import extract_all_citations
from src.file_utils import extract_text_from_file
from src.citation_utils import deduplicate_citations
from src.enhanced_validator_production import make_error_response
import tempfile

# Redis imports
try:
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None
    logger.warning("Redis not available - install with: pip install redis")

# RQ imports
try:
    from rq import Queue, Worker
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False
    logger.warning("RQ not available - install with: pip install rq")

# CitationService import
try:
    from src.api.services.citation_service import CitationService
    CITATION_SERVICE_AVAILABLE = True
    logger.info("CitationService imported successfully")
except ImportError as e:
    logger.warning(f"CitationService not available: {e}")
    CITATION_SERVICE_AVAILABLE = False

# PDF Handler import
try:
    from src.pdf_handler import extract_text_from_pdf, PDF_HANDLER_AVAILABLE
    logger.info("PDF handler imported successfully")
except ImportError as e:
    logger.warning(f"PDF handler not available: {e}")
    PDF_HANDLER_AVAILABLE = False
    extract_text_from_pdf = None

# Input validation functions
def validate_file_direct(file):
    """
    Validate uploaded file directly.
    
    Args:
        file: Flask file object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "No filename provided"
    
    # Check file size (50MB limit)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        return False, "File size exceeds 50MB limit"
    
    # Check file extension
    allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.html', '.htm', '.rtf'}
    file_ext = os.path.splitext(file.filename.lower())[1]
    
    if file_ext not in allowed_extensions:
        return False, f"Unsupported file type: {file_ext}. Supported types: {', '.join(allowed_extensions)}"
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type:
        allowed_mime_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/html',
            'application/rtf'
        }
        if mime_type not in allowed_mime_types:
            return False, f"Unsupported MIME type: {mime_type}"
    
    return True, ""

def validate_text_input(text):
    """
    Validate text input.
    
    Args:
        text: Text string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text:
        return False, "No text provided"
    
    if not isinstance(text, str):
        return False, "Text must be a string"
    
    # Check minimum length (10 characters)
    if len(text.strip()) < 10:
        return False, "Text must be at least 10 characters long"
    
    # Check maximum length (1MB)
    if len(text) > 1024 * 1024:  # 1MB
        return False, "Text exceeds 1MB limit"
    
    # Check for non-printable characters (except newlines and tabs)
    import string
    printable_chars = set(string.printable)
    non_printable_count = sum(1 for char in text if char not in printable_chars)
    if non_printable_count > len(text) * 0.1:  # More than 10% non-printable
        return False, "Text contains too many non-printable characters"
    
    return True, ""

def validate_url_input(url):
    """
    Validate URL input.
    
    Args:
        url: URL string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not url:
        return False, "No URL provided"
    
    if not isinstance(url, str):
        return False, "URL must be a string"
    
    # Check URL length
    if len(url) > 2048:
        return False, "URL exceeds 2048 character limit"
    
    # Basic URL format validation
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        if not parsed.scheme:
            return False, "URL must include a protocol (http:// or https://)"
        
        if parsed.scheme not in ['http', 'https']:
            return False, "URL must use HTTP or HTTPS protocol"
        
        if not parsed.netloc:
            return False, "URL must include a valid domain"
        
        # Check for localhost or private IP addresses
        if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
            return False, "Localhost URLs are not allowed"
        
        # Check for private IP ranges
        if parsed.hostname:
            try:
                import ipaddress
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private:
                    return False, "Private IP addresses are not allowed"
            except ValueError:
                # Not an IP address, which is fine
                pass
        
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"
    
    return True, ""

# Use UnifiedCitationProcessor for multi-source citation verification
try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    CitationVerifier = UnifiedCitationProcessor  # Alias for compatibility
    logger.info("Using UnifiedCitationProcessor for multi-source citation verification")
except ImportError as e:
    logger.warning(f"Could not import UnifiedCitationProcessor: {e}")
    logger.warning("Falling back to CitationVerifier")
    from src.citation_verification import CitationVerifier
    RateLimitError = Exception  # Fallback for compatibility

# Place log_json_responses here, before blueprint registration

def log_json_responses(response):
    """
    Flask after_request handler to log all JSON responses before they are sent to the frontend.
    """
    try:
        # Only log JSON responses
        if response.content_type == 'application/json':
            # Get the response data
            response_data = response.get_data(as_text=True)
            # Try to parse and pretty-print the JSON for better logging
            try:
                import json
                parsed_data = json.loads(response_data)
                formatted_json = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                # Log the response with context
                logger.info("=" * 80)
                logger.info("JSON RESPONSE BEING SENT TO FRONTEND")
                logger.info("=" * 80)
                logger.info(f"Endpoint: {request.endpoint}")
                logger.info(f"Method: {request.method}")
                logger.info(f"URL: {request.url}")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(f"Content-Type: {response.content_type}")
                logger.info(f"Response Size: {len(response_data)} characters")
                logger.info("-" * 80)
                logger.info("RESPONSE BODY:")
                logger.info(formatted_json)
                logger.info("=" * 80)
            except json.JSONDecodeError:
                # If JSON parsing fails, log the raw response
                logger.warning("Failed to parse JSON response, logging raw data:")
                logger.info(f"Raw response: {response_data}")
        return response
    except Exception as e:
        logger.error(f"Error in log_json_responses: {str(e)}")
        return response

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

# Global application start time for uptime tracking
APP_START_TIME = time.time()

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
    if REDIS_AVAILABLE:
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
            logger.info(f"[REDIS] Redis connection successful to {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"[REDIS] Redis connection failed: {e}")
            redis_conn = None
    else:
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
    if not REDIS_AVAILABLE or redis_conn is None:
        return "down"
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

def get_uptime():
    """Calculate and format application uptime."""
    uptime_seconds = time.time() - APP_START_TIME
    
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    if days > 0:
        formatted = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    elif hours > 0:
        formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        formatted = f"{minutes:02d}:{seconds:02d}"
    
    return {
        'seconds': int(uptime_seconds),
        'minutes': int(uptime_seconds // 60),
        'hours': hours,
        'days': days,
        'formatted': formatted,
        'human_readable': _format_uptime_human(uptime_seconds)
    }

def _format_uptime_human(seconds):
    """Format uptime in human-readable format."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours, {int((seconds % 3600) // 60)} minutes"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days} days, {hours} hours"

@vue_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the Vue API."""
    try:
        uptime = get_uptime()
        return jsonify({
            'status': 'healthy',
            'service': 'CaseStrainer Vue API',
            'timestamp': datetime.now().isoformat(),
            'uptime': uptime,
            'server_uptime': uptime['seconds'],  # For compatibility with monitoring systems
            'redis': check_redis(),
            'database': check_db(),
            'rq_worker': check_rq_worker(),
            'environment': WORKER_ENV,
            'version': '0.5.8'
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
        uptime = get_uptime()
        stats = {
            'timestamp': time.time(),
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'uptime': uptime,
            'server_uptime': uptime['seconds'],  # For compatibility with monitoring systems
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

@vue_api.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get task status and result for async processing."""
    logger.info(f"[DEBUG STEP] [get_task_status] Called for task_id: {task_id} at {datetime.utcnow().isoformat()}")
    logger.info(f"[DEBUG get_task_status] Checking status for task_id: {task_id} at {datetime.utcnow().isoformat()}")
    try:
        # First check if task is completed and has results
        result = get_task_result(task_id)
        if result:
            return jsonify({
                'status': 'completed',
                'task_id': task_id,
                'results': result.get('results', []),
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),  # Include clusters
                'case_names': result.get('case_names', []),
                'metadata': result.get('metadata', {}),
                'statistics': result.get('statistics', {}),
                'summary': result.get('summary', {})
            })
        
        # Check if task is still in progress
        if RQ_AVAILABLE and redis_conn:
            try:
                # Check if there's a job ID for this task
                job_id = redis_conn.get(f"task_to_job:{task_id}")
                if job_id:
                    job_id = job_id.decode('utf-8')
                    from rq import Queue
                    from rq.job import Job
                    job = Job.fetch(job_id, connection=redis_conn)
                    if job.is_finished:
                        # Job finished but result not stored, try to get from job
                        job_result = job.result
                        if job_result:
                            set_task_result(task_id, job_result)
                            return jsonify({
                                'status': 'completed',
                                'task_id': task_id,
                                'results': job_result.get('results', []),
                                'citations': job_result.get('citations', []),
                                'clusters': job_result.get('clusters', []),  # Include clusters
                                'case_names': job_result.get('case_names', []),
                                'metadata': job_result.get('metadata', {}),
                                'statistics': job_result.get('statistics', {}),
                                'summary': job_result.get('summary', {})
                            })
                    elif job.is_failed:
                        return jsonify({
                            'status': 'failed',
                            'task_id': task_id,
                            'error': str(job.exc_info) if job.exc_info else 'Job failed'
                        }), 500
                    else:
                        # Job is still running
                        return jsonify({
                            'status': 'processing',
                            'task_id': task_id,
                            'message': 'Task is being processed'
                        })
            except Exception as e:
                logger.warning(f"Error checking RQ job for task {task_id}: {e}")
        
        # Check if task is in threading queue
        if task_queue and task_queue.qsize() > 0:
            # This is a simplified check - in a real implementation you'd track individual tasks
            return jsonify({
                'status': 'queued',
                'task_id': task_id,
                'message': 'Task is queued for processing'
            })
        
        # Task not found
        return jsonify({
            'status': 'not_found',
            'task_id': task_id,
            'message': 'Task not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        return jsonify({
            'status': 'error',
            'task_id': task_id,
            'error': str(e)
        }), 500

@vue_api.route('/version', methods=['GET'])
def get_version():
    """Get application version information."""
    try:
        version_info = {
            'version': '2.0.0',
            'name': 'CaseStrainer',
            'description': 'Legal Citation Analysis Tool',
            'uptime': get_uptime(),
            'environment': WORKER_ENV,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }
        return jsonify(version_info)
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        return jsonify({'error': 'Failed to get version info'}), 500

@vue_api.route('/db_stats', methods=['GET'])
def get_db_stats():
    """Get database statistics."""
    try:
        # Get citation database stats
        db_path = os.path.join(os.getcwd(), 'data', 'citations.db')
        stats = {
            'database': {
                'path': db_path,
                'exists': os.path.exists(db_path),
                'size': os.path.getsize(db_path) if os.path.exists(db_path) else 0
            },
            'citations': {
                'total': 0,
                'verified': 0,
                'unverified': 0
            },
            'cache': {
                'redis_available': RQ_AVAILABLE,
                'active_requests': len(active_requests) if 'active_requests' in globals() else 0
            },
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }
        
        # Try to get actual citation counts from database
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get total citations
                cursor.execute("SELECT COUNT(*) FROM citations")
                stats['citations']['total'] = cursor.fetchone()[0]
                
                # Get verified citations
                cursor.execute("SELECT COUNT(*) FROM citations WHERE verified = 1")
                stats['citations']['verified'] = cursor.fetchone()[0]
                
                # Get unverified citations
                cursor.execute("SELECT COUNT(*) FROM citations WHERE verified = 0")
                stats['citations']['unverified'] = cursor.fetchone()[0]
                
                conn.close()
            except Exception as e:
                logger.warning(f"Error getting database stats: {e}")
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({'error': 'Failed to get database stats'}), 500

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
    
    # Enable RQ for Docker/Linux environments
    RQ_AVAILABLE = True
    logger.info(f"RQ queue initialized successfully with Redis at {redis_host}:{redis_port}")
        
except Exception as e:
    logger.error(f"Failed to initialize RQ queue: {e}")
    RQ_AVAILABLE = False


# Worker thread variables (for fallback if RQ is not available)
worker_thread = None
worker_running = False
task_queue = None

def initialize_worker():
    """Initialize worker thread (fallback only)"""
    global worker_thread, worker_running, task_queue
    
    # Only initialize if RQ is not available
    if not RQ_AVAILABLE:
        logger.info("Initializing fallback worker thread")
        # Fallback worker thread logic would go here
        return True
    else:
        logger.info("RQ available, no need for fallback worker thread")
        return True

def worker_loop():
    """Worker loop (fallback only)"""
    if not RQ_AVAILABLE:
        logger.info("Running fallback worker loop")
        # Fallback worker loop logic would go here
    return

def is_worker_running():
    """Check if worker is running"""
    if RQ_AVAILABLE:
        return True  # RQ workers are running in separate containers
    else:
        return worker_thread and worker_thread.is_alive()

def get_server_stats():
    """Get server stats"""
    uptime = get_uptime()
    return {
        'start_time': APP_START_TIME,
        'uptime': uptime['formatted'],
        'uptime_seconds': uptime['seconds'],
        'restart_count': 0,
        'worker_alive': is_worker_running(),
        'worker_disabled': False,
        'rq_available': RQ_AVAILABLE
    }

# --- Task status/result helpers and input hash tracking (Redis-backed, with in-memory fallback) ---
INPUT_HASH_TTL = 3600  # 1 hour
input_hash_to_result = {}
input_hash_to_task = {}
input_hash_expiry = {}

# Helper: Compute a hash for deduplication
import hashlib

def compute_input_hash(input_data):
    if isinstance(input_data, bytes):
        data = input_data
    elif isinstance(input_data, str):
        data = input_data.encode('utf-8')
    elif hasattr(input_data, 'read'):
        data = input_data.read()
        input_data.seek(0)
    else:
        data = str(input_data).encode('utf-8')
    return hashlib.sha256(data).hexdigest()

# Task status/result helpers

def set_task_status(task_id, status, data):
    key = f"task_status:{task_id}"
    value = json.dumps({'status': status, 'data': data, 'timestamp': time.time()})
    try:
        if REDIS_AVAILABLE and redis_conn:
            redis_conn.setex(key, INPUT_HASH_TTL, value)
        else:
            input_hash_to_result[key] = value
            input_hash_expiry[key] = time.time() + INPUT_HASH_TTL
    except Exception as e:
        logger.warning(f"[set_task_status] Failed to set status for {task_id}: {e}")
        input_hash_to_result[key] = value
        input_hash_expiry[key] = time.time() + INPUT_HASH_TTL

def set_task_result(task_id, result):
    key = f"task_result:{task_id}"
    value = json.dumps(result)
    logger.info(f"[DEBUG STEP] [set_task_result] Called for task {task_id} at {datetime.utcnow().isoformat()}")
    try:
        if REDIS_AVAILABLE and redis_conn:
            logger.info(f"[DEBUG STEP] [set_task_result] Using Redis host: {redis_conn.connection_pool.connection_kwargs.get('host')}, port: {redis_conn.connection_pool.connection_kwargs.get('port')}, db: {redis_conn.connection_pool.connection_kwargs.get('db')}")
            redis_conn.setex(key, INPUT_HASH_TTL, value)
            logger.info(f"[DEBUG STEP] [set_task_result] Successfully saved result to Redis for task {task_id}")
        else:
            input_hash_to_result[key] = value
            input_hash_expiry[key] = time.time() + INPUT_HASH_TTL
            logger.info(f"[DEBUG STEP] [set_task_result] Successfully saved result to memory for task {task_id}")
    except Exception as e:
        logger.warning(f"[DEBUG STEP] [set_task_result] Failed to set result for {task_id}: {e}")
        input_hash_to_result[key] = value
        input_hash_expiry[key] = time.time() + INPUT_HASH_TTL

def get_task_result(task_id):
    key = f"task_result:{task_id}"
    logger.info(f"[DEBUG STEP] [get_task_result] Called for task {task_id} at {datetime.utcnow().isoformat()}")
    try:
        if REDIS_AVAILABLE and redis_conn:
            logger.info(f"[DEBUG STEP] [get_task_result] Using Redis host: {redis_conn.connection_pool.connection_kwargs.get('host')}, port: {redis_conn.connection_pool.connection_kwargs.get('port')}, db: {redis_conn.connection_pool.connection_kwargs.get('db')}")
            value = redis_conn.get(key)
            if value:
                logger.info(f"[DEBUG STEP] [get_task_result] Found result in Redis for task {task_id}")
                return json.loads(value)
            else:
                logger.info(f"[DEBUG STEP] [get_task_result] No result in Redis for task {task_id}")
        else:
            value = input_hash_to_result.get(key)
            if value:
                logger.info(f"[DEBUG STEP] [get_task_result] Found result in memory for task {task_id}")
                return json.loads(value)
            else:
                logger.info(f"[DEBUG STEP] [get_task_result] No result in memory for task {task_id}")
    except Exception as e:
        logger.warning(f"[DEBUG STEP] [get_task_result] Failed to get result for {task_id}: {e}")
    return None

def cleanup_input_hashes():
    now = time.time()
    expired = [k for k, exp in input_hash_expiry.items() if exp < now]
    for k in expired:
        input_hash_to_result.pop(k, None)
        input_hash_to_task.pop(k, None)
        input_hash_expiry.pop(k, None)

def process_citation_task(task_id: str, task_type: str, task_data: dict):
    """
    Simplified wrapper that delegates to CitationService.
    This maintains compatibility with your existing queue system.
    """
    logger.info(f"[TASK] Processing {task_type} task {task_id}")
    
    try:
        if not CITATION_SERVICE_AVAILABLE:
            logger.error("[TASK] CitationService not available")
            set_task_status(task_id, 'failed', {'error': 'CitationService not available'})
            return {'status': 'failed', 'error': 'CitationService not available'}
        
        # Use the extracted service
        citation_service = CitationService()
        result = citation_service.process_citation_task(task_id, task_type, task_data)
        
        # Update task status based on result
        if result.get('status') == 'failed':
            set_task_status(task_id, 'failed', {'error': result.get('error', 'Unknown error')})
            logger.error(f"[TASK] Task {task_id} failed: {result.get('error')}")
        else:
            set_task_status(task_id, 'completed', {'progress': 100, 'current_step': 'Complete'})
            
            # Store the full result
            task_result_data = {
                'task_id': task_id,
                'type': task_type,
                'status': 'completed',
                'results': result.get('citations', []),
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),  # Include clusters
                'case_names': result.get('case_names', []),
                'metadata': result.get('metadata', {}),
                'statistics': result.get('statistics', {}),
                'summary': result.get('summary', {}),
                'processing_time': result.get('metadata', {}).get('processing_time', 0)
            }
            
            set_task_result(task_id, task_result_data)
            logger.info(f"[TASK] Task {task_id} completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"[TASK] Error in task {task_id}: {e}", exc_info=True)
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
    task_id = None  # Initialize task_id to prevent UnboundLocalError

    try:
        logger = current_app.logger
        logger.info(f"[DEBUG STEP] [ANALYZE] Start analyze endpoint at {datetime.utcnow().isoformat()}")
        logger.info(f"[DEBUG STEP] [ANALYZE] Request method: {request.method}")
        logger.info(f"[DEBUG STEP] [ANALYZE] Request headers: {dict(request.headers)}")
        try:
            logger.info(f"[DEBUG STEP] [ANALYZE] Request body: {request.get_data(as_text=True)[:1000]}")
        except Exception as e:
            logger.warning(f"[DEBUG STEP] [ANALYZE] Could not log request body: {e}")
        
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
        logger.info(f"[DEBUG STEP] [ANALYZE] Assigned task_id: {task_id}")
        current_app.logger.info(f"{WORKER_LABEL} [ANALYZE] Assigned task ID: {task_id}")

        # Initialize citation service
        if not CITATION_SERVICE_AVAILABLE:
            return jsonify({
                'status': 'error',
                'message': 'CitationService not available'
            }), 500
        
        citation_service = CitationService()

        # Handle file upload
        if 'file' in request.files or 'file' in request.form or (request.is_json and 'file' in data):
            logger.info(f"[ANALYZE] Processing file upload request")
            file = request.files.get('file')
            if not file:
                logger.error(f"[ANALYZE] No file provided in request")
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided'
                }), 400
            # Comprehensive file validation
            logger.info(f"[ANALYZE] Validating file: {file.filename}")
            is_valid, error_message = validate_file_direct(file)
            if not is_valid:
                logger.error(f"[ANALYZE] File validation failed: {error_message}")
                return jsonify({
                    'status': 'error',
                    'message': error_message
                }), 400
            logger.info(f"[ANALYZE] File validation passed")
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            temp_file_path = None
            
            # Save uploaded file to shared uploads directory instead of temp file
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            # Use relative path to uploads directory in project root
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir, exist_ok=True)
            temp_file_path = os.path.join(uploads_dir, unique_filename)
            logger.info(f"[ANALYZE] Saving file to: {temp_file_path}")
            file.save(temp_file_path)
            logger.info(f"[ANALYZE] File saved successfully")
            
            # Extract text from file BEFORE enqueueing to avoid hanging in worker
            logger.info(f"[ANALYZE] Extracting text from file before enqueueing: {temp_file_path}")
            
            # Disable verbose pdfminer logging to speed up extraction
            import logging
            logging.getLogger("pdfminer").setLevel(logging.WARNING)
            logging.getLogger("pdfminer.cmapdb").setLevel(logging.ERROR)
            logging.getLogger("pdfminer.psparser").setLevel(logging.ERROR)
            logging.getLogger("pdfminer.pdfinterp").setLevel(logging.ERROR)
            
            try:
                # Use the faster pdf_handler for PDF files
                if file_ext.lower() == '.pdf' and PDF_HANDLER_AVAILABLE and extract_text_from_pdf:
                    logger.info(f"[ANALYZE] Using fast PDF handler for: {filename}")
                    try:
                        extracted_text = extract_text_from_pdf(temp_file_path, timeout=25)
                        logger.info(f"[ANALYZE] PDF handler extraction completed successfully")
                    except Exception as pdf_error:
                        logger.warning(f"[ANALYZE] PDF handler failed, falling back to document_processing_unified: {pdf_error}")
                        # Fallback to document_processing_unified
                        from src.document_processing_unified import extract_text_from_file
                        extracted_text = extract_text_from_file(temp_file_path)
                else:
                    # Fallback to document_processing_unified for non-PDF files
                    logger.info(f"[ANALYZE] Using document_processing_unified for: {filename}")
                    from src.document_processing_unified import extract_text_from_file
                    extracted_text = extract_text_from_file(temp_file_path)
                
                logger.info(f"[ANALYZE] Text extraction completed. Length: {len(extracted_text)}")
                
                if not extracted_text or not extracted_text.strip():
                    logger.warning(f"[ANALYZE] Extracted text is empty for file: {filename}")
                    return jsonify({
                        'status': 'error',
                        'message': 'No text content could be extracted from the uploaded file'
                    }), 400
                
                # Clean up the file immediately after extraction
                try:
                    os.remove(temp_file_path)
                    logger.info(f"[ANALYZE] Cleaned up uploaded file after text extraction: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"[ANALYZE] Could not clean up file {temp_file_path}: {e}")
                
                # Add task to queue with extracted text instead of file path
                task = {
                    'task_id': task_id,
                    'type': 'text',  # Changed from 'file' to 'text'
                    'data': {
                        'text': extracted_text,
                        'filename': filename,
                        'file_ext': file_ext,
                        'source_type': 'file'
                    }
                }
                
            except Exception as e:
                logger.error(f"[ANALYZE] Error extracting text from file: {e}", exc_info=True)
                # Clean up file on error
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        logger.info(f"[ANALYZE] Cleaned up uploaded file after extraction error: {temp_file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"[ANALYZE] Could not clean up file {temp_file_path}: {cleanup_error}")
                
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to extract text from file: {str(e)}'
                }), 500
            
            # Initialize task in active_requests
            set_task_status(task_id, 'queued', task['data'])
            # Enqueue task
            current_app.logger.info(f"[ANALYZE] RQ_AVAILABLE={RQ_AVAILABLE}, queue={queue}")
            if RQ_AVAILABLE and queue:
                job = queue.enqueue(process_citation_task, task_id, 'text', task['data'], job_timeout=600)  # 10 minutes
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
                logger.error(f"[ANALYZE] RQ is not available or queue is not initialized. Cannot enqueue task {task_id}.")
                return make_error_response(
                    "rq_unavailable",
                    f"RQ is not available or queue is not initialized. Cannot enqueue task {task_id}.",
                    status_code=500
                )
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
            
            # NEW: Use CitationService for immediate/async decision
            input_data = {'type': 'text', 'text': text}
            
            if citation_service.should_process_immediately(input_data):
                # NEW: Use CitationService for immediate processing
                logger.info(f"[ANALYZE] Using immediate processing for: {text[:50]}...")
                
                result = citation_service.process_immediately(input_data)
                
                if result.get('status') == 'error':
                    return jsonify(result), 500
                
                # DEBUG: Log the result before returning to frontend
                logger.info(f"[ANALYZE] DEBUG - Result status: {result.get('status')}")
                if result.get('citations'):
                    for i, citation in enumerate(result['citations']):
                        logger.info(f"[ANALYZE] DEBUG - Citation {i}: extracted_case_name='{citation.get('extracted_case_name')}', extracted_date='{citation.get('extracted_date')}', canonical_name='{citation.get('canonical_name')}', canonical_date='{citation.get('canonical_date')}'")
                else:
                    logger.info(f"[ANALYZE] DEBUG - No citations in result")
                
                # Return immediate response
                return jsonify(result)
            
            else:
                # Continue with async processing
                logger.info(f"[ANALYZE] Using async processing for text")
                
                task = {
                    'task_id': task_id,
                    'type': 'text',
                    'data': {'text': text}
                }
                
                set_task_status(task_id, 'queued', task['data'])
                
                # Enqueue task
                current_app.logger.info(f"[ANALYZE] RQ_AVAILABLE={RQ_AVAILABLE}, queue={queue}")
                if RQ_AVAILABLE and queue:
                    job = queue.enqueue(process_citation_task, task_id, 'text', task['data'], job_timeout=600)  # 10 minutes
                    logger.info(f"[ANALYZE] Enqueued job for task {task_id}: job_id={getattr(job, 'id', None)}")
                    if not job:
                        logger.error(f"[ANALYZE] Failed to enqueue task {task_id}: job is None")
                        return make_error_response(
                            "enqueue_error",
                            f"Failed to enqueue task {task_id}",
                            status_code=500
                        )
                    # Store the job ID mapping in Redis
                    try:
                        redis_conn.setex(f"task_to_job:{task_id}", 3600, job.id)
                        logger.info(f"[ANALYZE] Stored task {task_id} -> job {job.id} mapping")
                    except Exception as e:
                        logger.error(f"[ANALYZE] Failed to store job mapping for {task_id}: {e}")
                    logger.info(f"[ANALYZE] Added text task {task_id} to RQ")
                else:
                    logger.error(f"[ANALYZE] RQ is not available or queue is not initialized. Cannot enqueue task {task_id}.")
                    return make_error_response(
                        "rq_unavailable",
                        f"RQ is not available or queue is not initialized. Cannot enqueue task {task_id}.",
                        status_code=500
                    )
                
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'Text input received, processing started',
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
            else:
                logger.error(f"[ANALYZE] RQ is not available or queue is not initialized. Cannot enqueue task {task_id}.")
                return make_error_response(
                    "rq_unavailable",
                    f"RQ is not available or queue is not initialized. Cannot enqueue task {task_id}.",
                    status_code=500
                )
            
            # Return immediate response with task ID for queued tasks
            if RQ_AVAILABLE and queue:
                return jsonify({
                    'status': 'processing',
                    'task_id': task_id,
                    'message': 'URL input received, processing started',
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
    finally:
        # Clean up input hashes after processing
        cleanup_input_hashes()
