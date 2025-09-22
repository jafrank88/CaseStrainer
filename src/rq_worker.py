"""
Robust RQ Worker for CaseStrainer with memory management and auto-restart
This script starts an RQ worker with better error handling and resource management
"""

import os
import sys

# CRITICAL: Set up Python path FIRST before any other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # Add /app to path
sys.path.insert(0, os.path.dirname(__file__))  # Add /app/src to path

from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
import signal
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory monitoring disabled")

from rq import Worker, Queue
from redis import Redis
from src.redis_distributed_processor import extract_pdf_pages, extract_pdf_optimized
from src.optimized_pdf_processor import extract_pdf_optimized_v2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
redis_conn = Redis.from_url(redis_url)

queue = Queue('casestrainer', connection=redis_conn)

def register_worker_functions():
    """Register all worker functions with RQ."""
    worker_functions = [
        'extract_pdf_pages',
        'extract_pdf_optimized',
        'extract_pdf_optimized_v2',
        'process_citation_task_direct',
        'src.redis_distributed_processor.DockerOptimizedProcessor.process_document',
        'src.async_verification_worker.verify_citations_enhanced',
        'src.async_verification_worker.verify_citations_basic',
        'src.async_verification_worker.verify_citations_async'
    ]
    
    logger.info(f"Registered worker functions: {worker_functions}")
    return worker_functions

__all__ = [
    'process_citation_task_direct', 
    'extract_pdf_pages', 
    'extract_pdf_optimized', 
    'extract_pdf_optimized_v2',
    'verify_citations_enhanced'
]

def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """Direct wrapper function with extensive diagnostic logging."""
    
    # DIAGNOSTIC LOGGING - Track every step of worker startup
    logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER STARTUP BEGINS ==========")
    logger.info(f"[DIAGNOSTIC:{task_id}] Step 1: Function entry successful")
    
    try:
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 2: Starting basic imports...")
        import traceback
        import time
        import json
        import os
        import sys
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 2: Basic imports SUCCESS")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 3: Environment info...")
        logger.info(f"[DIAGNOSTIC:{task_id}] Python version: {sys.version}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Working directory: {os.getcwd()}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Input type: {input_type}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Input data keys: {list(input_data.keys())}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 3: Environment info SUCCESS")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 4: Redis readiness check...")
        try:
            import redis
            redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
            logger.info(f"[DIAGNOSTIC:{task_id}] Redis URL: {redis_url}")
            
            # Check if Redis is ready (not loading dataset)
            redis_client = redis.from_url(redis_url)
            
            # Wait for Redis to be ready with timeout
            max_wait = 30  # 30 seconds max wait
            wait_interval = 1  # Check every second
            
            for attempt in range(max_wait):
                try:
                    # Test Redis connection
                    redis_client.ping()
                    logger.info(f"[DIAGNOSTIC:{task_id}] Redis ready after {attempt} seconds")
                    break
                except redis.exceptions.BusyLoadingError:
                    if attempt == 0:
                        logger.info(f"[DIAGNOSTIC:{task_id}] Redis loading dataset, waiting...")
                    elif attempt % 5 == 0:
                        logger.info(f"[DIAGNOSTIC:{task_id}] Still waiting for Redis ({attempt}s)...")
                    time.sleep(wait_interval)
                except Exception as e:
                    logger.error(f"[DIAGNOSTIC:{task_id}] Redis connection error: {e}")
                    if attempt < 5:  # Retry connection errors for first 5 seconds
                        time.sleep(wait_interval)
                    else:
                        raise
            else:
                # Timeout waiting for Redis
                logger.error(f"[DIAGNOSTIC:{task_id}] Redis not ready after {max_wait} seconds")
                return {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': f'Redis not ready after {max_wait} seconds - dataset still loading',
                    'diagnostic': 'redis_loading_timeout'
                }
                
        except Exception as e:
            logger.error(f"[DIAGNOSTIC:{task_id}] Redis readiness error: {str(e)}")
            # Continue anyway - might be a temporary issue
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 4: Redis readiness SUCCESS")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 5: CitationService import...")
        from src.api.services.citation_service import CitationService
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 5: CitationService import SUCCESS")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 6: Creating CitationService instance...")
        service = CitationService()
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 6: CitationService creation SUCCESS")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER STARTUP COMPLETE ==========")
        
    except Exception as e:
        logger.error(f"[DIAGNOSTIC:{task_id}] STARTUP FAILED at import/initialization: {str(e)}")
        logger.error(f"[DIAGNOSTIC:{task_id}] Traceback: {traceback.format_exc()}")
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': f'Worker startup failed: {str(e)}',
            'diagnostic': 'startup_failure'
        }
    
    # Setup timeout handler for non-Windows systems
    timeout_set = False
    if platform.system() != 'Windows':
        try:
            def timeout_handler(signum, frame):
                error_msg = f"Task {task_id} timed out after 10 minutes"
                logger.error(f"[TASK:{task_id}] {error_msg}")
                raise TimeoutError(error_msg)
            
            signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore[attr-defined]
            signal.alarm(600)  # type: ignore[attr-defined]
            timeout_set = True
            logger.info(f"[TASK:{task_id}] Timeout handler set for 10 minutes")
        except (AttributeError, OSError) as e:
            logger.warning(f"[TASK:{task_id}] Could not set signal handler: {str(e)}")
    
    try:
        start_time = time.time()
        logger.info(f"[DIAGNOSTIC:{task_id}] ========== MAIN PROCESSING BEGINS ==========")
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 7: Starting processing of type: {input_type}")
        
        # Log input data (truncated if too large)
        input_data_str = str(input_data)
        if len(input_data_str) > 500:
            input_data_str = input_data_str[:500] + "... [truncated]"
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 7: Input data logged")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 8: Entering processing logic...")
        logger.info(f"[DIAGNOSTIC:{task_id}] Using minimal async worker for diagnostic testing")
        
        if input_type in ['text', 'url']:
            # Handle both text and URL inputs with the full pipeline
            if input_type == 'text':
                text = input_data.get('text', '')
                logger.info(f"[TASK:{task_id}] Processing text of length {len(text)}")
            elif input_type == 'url':
                url = input_data.get('url', '')
                logger.info(f"[TASK:{task_id}] Processing URL: {url}")
                
                # Extract text from URL first
                try:
                    logger.info(f"[TASK:{task_id}] Extracting text from URL...")
                    import requests
                    from src.optimized_pdf_processor import OptimizedPDFProcessor
                    import tempfile
                    import os
                    
                    # Download the content
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # If it's a PDF, extract text
                    if 'pdf' in response.headers.get('content-type', '').lower() or url.lower().endswith('.pdf'):
                        logger.info(f"[TASK:{task_id}] Detected PDF, extracting text...")
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                            temp_file.write(response.content)
                            temp_path = temp_file.name
                        
                        try:
                            # Extract text using PDF processor
                            pdf_processor = OptimizedPDFProcessor()
                            result = pdf_processor.process_pdf(temp_path)
                            text = result.text if result else ""
                            logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters from PDF")
                        finally:
                            # Clean up temp file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                    else:
                        # Plain text content
                        text = response.text
                        logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters from URL")
                    
                    if not text or len(text.strip()) < 10:
                        logger.warning(f"[TASK:{task_id}] No meaningful text extracted from URL")
                        result = {
                            'success': True,
                            'citations': [],
                            'clusters': [],
                            'processing_strategy': 'url_no_text',
                            'processing_time': time.time() - start_time
                        }
                        # Skip to full processing
                        skip_full_processing = True
                    else:
                        skip_full_processing = False
                    
                except Exception as e:
                    logger.error(f"[TASK:{task_id}] URL text extraction failed: {e}")
                    result = {
                        'success': False,
                        'error': f'URL text extraction failed: {str(e)}'
                    }
                    skip_full_processing = True
            else:
                skip_full_processing = False
            
            # Only proceed with full processing if we have text and no errors
            if not locals().get('skip_full_processing', False):
                # FULL ASYNC WORKER - Use UnifiedCitationProcessorV2 for complete processing
                logger.info(f"[DIAGNOSTIC:{task_id}] Step 9: Using full async worker with UnifiedCitationProcessorV2")
                
                try:
                    logger.info(f"[DIAGNOSTIC:{task_id}] Step 10: Importing UnifiedCitationProcessorV2...")
                    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                    import asyncio
                    import time
                    logger.info(f"[DIAGNOSTIC:{task_id}] Step 10: UnifiedCitationProcessorV2 import SUCCESS")
                    
                    logger.info(f"[DIAGNOSTIC:{task_id}] Step 11: Starting full citation processing pipeline")
                    
                    # Use the full processing pipeline
                    processor = UnifiedCitationProcessorV2()
                    result_data = asyncio.run(processor.process_text(text))
                    citations_found = result_data.get('citations', [])
                    
                    logger.info(f"[TASK:{task_id}] Full pipeline found {len(citations_found)} citations")
                    
                    # Convert CitationResult objects to dictionaries if needed
                    citations_list = []
                    for citation in citations_found:
                        if hasattr(citation, 'to_dict'):
                            citations_list.append(citation.to_dict())
                        elif isinstance(citation, dict):
                            citations_list.append(citation)
                        else:
                            # Fallback conversion with case_name mapping
                            cluster_case_name = getattr(citation, 'cluster_case_name', None)
                            extracted_case_name = getattr(citation, 'extracted_case_name', None)
                            canonical_name = getattr(citation, 'canonical_name', None)
                            
                            # REMOVED: case_name field eliminated to prevent contamination and maintain data clarity
                            # Frontend will use extracted_case_name and canonical_name directly
                            
                            citations_list.append({
                                'citation': getattr(citation, 'citation', str(citation)),
                                'extracted_case_name': extracted_case_name,
                                'canonical_name': canonical_name,
                                'cluster_case_name': cluster_case_name,
                                'verified': getattr(citation, 'verified', False),
                                'confidence': getattr(citation, 'confidence', 1.0),
                                'method': getattr(citation, 'method', 'full_async')
                            })
                    
                    # Apply deduplication to rq_worker async processing (MISSING FEATURE ADDED)
                    logger.info(f"[TASK:{task_id}] Starting deduplication of {len(citations_list)} citations")
                    try:
                        from src.citation_deduplication import deduplicate_citations
                        
                        original_count = len(citations_list)
                        citations_list = deduplicate_citations(citations_list, debug=True)
                        
                        logger.info(f"[TASK:{task_id}] Deduplication completed: {original_count} → {len(citations_list)} citations")
                        if len(citations_list) < original_count:
                            logger.info(f"[TASK:{task_id}] Deduplication SUCCESS: "
                                       f"({original_count - len(citations_list)} duplicates removed)")
                        
                    except Exception as e:
                        logger.error(f"[TASK:{task_id}] Deduplication FAILED: {e}")
                        # Continue with original citations if deduplication fails
                    
                    result = {
                        'success': True,
                        'citations': citations_list,
                        'clusters': result_data.get('clusters', []),
                        'processing_strategy': 'full_async_unified',
                        'processing_time': time.time() - start_time
                    }
                    
                    logger.info(f"[TASK:{task_id}] Full async processing completed successfully")
                    
                except Exception as e:
                    logger.error(f"[TASK:{task_id}] Full async processing failed: {e}")
                    logger.error(f"[TASK:{task_id}] Exception details: {str(e)}")
                    import traceback
                    logger.error(f"[TASK:{task_id}] Traceback: {traceback.format_exc()}")
                    
                    # Fallback to minimal processing if full pipeline fails
                    logger.info(f"[TASK:{task_id}] Falling back to minimal processing")
                    try:
                        import re
                        citation_patterns = [
                            r'\d+\s+Wn\.2d\s+\d+',           # Washington 2d
                            r'\d+\s+Wn\.\s+App\.\s+2d\s+\d+', # Washington App 2d  
                            r'\d+\s+P\.3d\s+\d+',            # Pacific 3d
                            r'\d+\s+U\.S\.\s+\d+',           # US Supreme Court
                            r'\d+\s+F\.3d\s+\d+',            # Federal 3d
                            r'\d+\s+P\.2d\s+\d+'             # Pacific 2d
                        ]
                        
                        citations_found = []
                        for pattern in citation_patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                citations_found.append({
                                    'citation': match,
                                    'case_name': 'N/A',  # FIXED: Add case_name field
                                    'extracted_case_name': None,
                                    'canonical_name': None,
                                    'cluster_case_name': None,
                                    'verified': False,
                                    'confidence': 0.8,
                                    'method': 'fallback_async'
                                })
                        
                        result = {
                            'success': True,
                            'citations': citations_found,
                            'clusters': [],
                            'processing_strategy': 'fallback_async',
                            'processing_time': time.time() - start_time
                        }
                        
                        logger.info(f"[TASK:{task_id}] Fallback processing found {len(citations_found)} citations")
                        
                    except Exception as e2:
                        logger.error(f"[TASK:{task_id}] Fallback processing also failed: {e2}")
                        result = {
                            'success': False,
                            'error': f'Both full and fallback processing failed: {str(e)}'
                        }
            
            # Ensure result has the expected format for async
            if result.get('success', False):
                result = {
                    'status': 'completed',
                    'task_id': task_id,
                    'citations': result.get('citations', []),
                    'clusters': result.get('clusters', []),
                    'metadata': {
                        'processing_strategy': result.get('processing_strategy', 'async_unified'),
                        'text_length': len(text)
                    }
                }
            else:
                result = {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': result.get('error', 'Processing failed')
                }
            
        else:
            # For non-text inputs, fall back to the original method
            logger.info(f"[TASK:{task_id}] Using CitationService for non-text input type: {input_type}")
            result = asyncio.run(service.process_citation_task(task_id, input_type, input_data))
        
        # Ensure the result is JSON serializable
        processing_time = time.time() - start_time
        logger.info(f"[TASK:{task_id}] Task completed in {processing_time:.2f} seconds")
        
        try:
            # Log result summary (truncated if too large)
            result_str = str(result)
            if len(result_str) > 500:
                result_str = result_str[:500] + "... [truncated]"
            logger.info(f"[TASK:{task_id}] Task result: {result_str}")
            
            # Test serialization
            json.dumps(result)
            logger.info(f"[TASK:{task_id}] Result is JSON serializable")
            
            # Log success with metrics if available
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                num_citations = len(result.get('citations', []))
                num_clusters = len(result.get('clusters', []))
                logger.info(f"[TASK:{task_id}] Task completed with status '{status}'. Citations: {num_citations}, Clusters: {num_clusters}")
            
            # Ensure the result is properly stored in Redis
            try:
                from redis import Redis
                import json
                redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
                redis_conn = Redis.from_url(redis_url)
                
                # Store the result with a 24-hour TTL
                result_key = f'rq:job:{task_id}:result'
                redis_conn.setex(result_key, 86400, json.dumps(result))
                logger.info(f"[TASK:{task_id}] Result stored in Redis with key: {result_key}")
                
                # Also store in the job hash for RQ compatibility
                job_key = f'rq:job:{task_id}'
                redis_conn.hset(job_key, 'result', json.dumps(result))
                redis_conn.expire(job_key, 86400)
                logger.info(f"[TASK:{task_id}] Result stored in job hash")
                
            except Exception as e:
                logger.error(f"[TASK:{task_id}] Error storing result in Redis: {str(e)}", exc_info=True)
            
            return result
            
        except (TypeError, OverflowError) as e:
            error_msg = f"Result for task {task_id} is not JSON serializable: {e}"
            logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
            
            # Create a safe result with error information
            safe_result = {
                'status': 'failed',
                'error': 'Result serialization failed',
                'task_id': task_id,
                'processing_time': processing_time,
                'original_status': result.get('status') if isinstance(result, dict) else str(type(result)),
                'error_details': str(e)
            }
            
            # Try to include basic result info if available
            if isinstance(result, dict):
                safe_result.update({
                    'result_type': 'dict',
                    'result_keys': list(result.keys())
                })
            else:
                safe_result['result_type'] = str(type(result))
            
            logger.info(f"[TASK:{task_id}] Returning safe result after serialization error")
            return safe_result
        
    except TimeoutError as e:
        error_msg = f"Task {task_id} timed out after 10 minutes"
        logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
        return {
            'status': 'failed',
            'error': error_msg,
            'task_id': task_id,
            'processing_time': time.time() - start_time if 'start_time' in locals() else None,
            'error_type': 'timeout',
            'stack_trace': traceback.format_exc()
        }
    except Exception as e:
        error_msg = f"Task {task_id} failed: {str(e)}"
        logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
        return {
            'status': 'failed',
            'error': error_msg,
            'task_id': task_id,
            'processing_time': time.time() - start_time if 'start_time' in locals() else None,
            'error_type': type(e).__name__,
            'stack_trace': traceback.format_exc(),
            'task_id': task_id,
            'exception_type': type(e).__name__
        }
    finally:
        if platform.system() != 'Windows' and timeout_set:
            try:
                signal.alarm(0)  # type: ignore[attr-defined]
            except (AttributeError, OSError):
                pass

def verify_citations_enhanced(citations: list, text: str, request_id: str, input_type: str, metadata: dict):
    """Enhanced async verification of citations using the fallback verifier."""
    try:
        from src.async_verification_worker import verify_citations_enhanced as verify_enhanced
        
        result = verify_enhanced(citations, text, request_id, input_type, metadata)
        
        logger.info(f"Verification completed for request {request_id}: {len(citations)} citations processed")
        return result
        
    except Exception as e:
        logger.error(f"Verification failed for request {request_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Verification failed: {str(e)}',
            'citations': citations,
            'request_id': request_id,
            'input_type': input_type,
            'metadata': metadata
        }

class RobustWorker(Worker):
    """Enhanced RQ worker with memory management and graceful shutdown."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_memory_mb = 2048  # 2GB memory limit
        self.job_count = 0
        self.max_jobs = 100  # Restart after 100 jobs
        
    def perform_job(self, job, queue):
        """Override to add memory management and job counting."""
        try:
            if PSUTIL_AVAILABLE:
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                if memory_usage > self.max_memory_mb:
                    logger.warning(f"Memory usage high ({memory_usage:.1f}MB), restarting worker")
                    sys.exit(0)  # Graceful shutdown
                    return
            
            self.job_count += 1
            if self.job_count >= self.max_jobs:
                logger.info(f"Processed {self.job_count} jobs, restarting worker")
                sys.exit(0)  # Graceful shutdown
                return
            
            logger.info(f"Processing job {job.id} (job #{self.job_count})")
            result = super().perform_job(job, queue)
            
            if PSUTIL_AVAILABLE:
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                logger.info(f"Job {job.id} completed. Memory: {memory_after:.1f}MB")
            else:
                logger.info(f"Job {job.id} completed. Memory monitoring disabled")
            
            return result
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            raise

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info('[DEBUG] ENTERED rq_worker.py main() - worker is starting up')
    
    if PSUTIL_AVAILABLE:
        logger.info("psutil available - memory monitoring enabled")
    else:
        logger.warning("psutil not available - memory monitoring disabled")
    
    signal.signal(signal.SIGTERM, signal_handler)  # type: ignore[attr-defined]
    signal.signal(signal.SIGINT, signal_handler)  # type: ignore[attr-defined]
    
    register_worker_functions()
    
    worker = RobustWorker([queue], connection=redis_conn)
    
    logger.info("Starting RQ worker...")
    logger.info(f"Redis URL: {redis_url}")
    logger.info(f"Queue: casestrainer")
    logger.info(f"Worker ID: {worker.key}")
    
    try:
        worker.work(
            with_scheduler=True,
            max_jobs=100  # Restart after 100 jobs
        )
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        logger.info("Worker shutdown complete")

if __name__ == '__main__':
    main() 