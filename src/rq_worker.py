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
import platform
import threading
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory monitoring disabled")

from rq import Worker, Queue
from src.verification_manager import VerificationManager
from redis import Redis
from src.redis_distributed_processor import extract_pdf_pages, extract_pdf_optimized, DockerOptimizedProcessor
from src.optimized_pdf_processor import extract_pdf_optimized_v2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

redis_url = os.environ.get('REDIS_URL', 'redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')
redis_conn = Redis.from_url(redis_url)

queue = Queue('casestrainer', connection=redis_conn)

def register_worker_functions():
    """Register all worker functions with RQ."""
    worker_functions = [
        'extract_pdf_pages',
        'extract_pdf_optimized',
        'extract_pdf_optimized_v2',
        'process_citation_task_direct',
        'process_citation_task_async',
        'src.redis_distributed_processor.DockerOptimizedProcessor.process_document',
        'src.async_verification_worker.verify_citations_enhanced',
        'src.async_verification_worker.verify_citations_basic',
        'src.async_verification_worker.verify_citations_async'
    ]
    
    logger.info(f"Registered worker functions: {worker_functions}")
    return worker_functions

__all__ = [
    'process_citation_task_direct', 
    'process_citation_task_async',
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
    
    # Add timeout wrapper to prevent infinite hangs
    import concurrent.futures
    import threading
    
    def run_with_timeout():
        """Inner function that runs the actual processing with timeout."""
        return _process_citation_task_internal(task_id, input_type, input_data)
    
    try:
        # Run with a 5-minute timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_with_timeout)
            try:
                result = future.result(timeout=300)  # 5 minutes timeout
                logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER COMPLETED SUCCESSFULLY ==========")
                return result
            except concurrent.futures.TimeoutError:
                logger.error(f"[DIAGNOSTIC:{task_id}] ========== WORKER TIMEOUT AFTER 5 MINUTES ==========")
                # Cancel the future if it's still running
                future.cancel()
                return {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': 'Job timed out after 5 minutes',
                    'diagnostic': 'timeout_error'
                }
    except Exception as e:
        logger.error(f"[DIAGNOSTIC:{task_id}] ========== WORKER CRASHED ==========")
        logger.error(f"[DIAGNOSTIC:{task_id}] Error: {str(e)}")
        import traceback
        logger.error(f"[DIAGNOSTIC:{task_id}] Traceback: {traceback.format_exc()}")
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': f'Worker crashed: {str(e)}',
            'diagnostic': 'worker_crash'
        }

def _process_citation_task_internal(task_id: str, input_type: str, input_data: dict):
    
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
            redis_url = os.environ.get('REDIS_URL', 'redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')
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
    
    # Setup timeout handler - disabled since we use ThreadPoolExecutor for timeout
    # Note: signal only works in main thread, so we rely on ThreadPoolExecutor timeout instead
    timeout_set = False
    logger.info(f"[TASK:{task_id}] Using ThreadPoolExecutor timeout (5 minutes) instead of signal handler")
    
    try:
        start_time = time.time()
        logger.info(f"[DIAGNOSTIC:{task_id}] ========== MAIN PROCESSING BEGINS ==========")
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 7: Starting processing of type: {input_type}")
        
        # CRITICAL: Add immediate flush to ensure logs appear
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Register verification/progress so the UI can poll immediately
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.1: About to create VerificationManager...")
        try:
            vm = VerificationManager()
            logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.2: VerificationManager created")
            vm.register_verification(task_id, task_id, total_citations=4)  # treat as 4-step progress initially
            logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.3: Verification registered")
            vm.update_progress(task_id, processed=0, total=4, message='Initializing async processing')
            logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.4: Progress updated")
        except Exception as _e:
            logger.error(f"[DIAGNOSTIC:{task_id}] Step 7.ERROR: VerificationManager failed: {_e}")
            import traceback
            logger.error(f"[DIAGNOSTIC:{task_id}] VerificationManager traceback: {traceback.format_exc()}")
        
        # Log input data (truncated if too large)
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 8: About to log input data...")
        input_data_str = str(input_data)
        if len(input_data_str) > 500:
            input_data_str = input_data_str[:500] + "... [truncated]"
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 8: Input data logged (length: {len(input_data_str)})")
        
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 9: About to enter processing logic...")
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
                    # CRITICAL FIX: Follow redirects to handle HTTP→HTTPS redirects
                    response = requests.get(url, timeout=30, allow_redirects=True)
                    response.raise_for_status()
                    
                    # If it's a PDF, extract text
                    if 'pdf' in response.headers.get('content-type', '').lower() or url.lower().endswith('.pdf'):
                        logger.info(f"[TASK:{task_id}] Detected PDF, extracting text...")
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                            temp_file.write(response.content)
                            temp_path = temp_file.name
                        
                        try:
                            # Extract text using UnifiedTextExtractor (same as file uploads)
                            from src.unified_text_extractor import extract_text_from_file_unified
                            text, method = extract_text_from_file_unified(temp_path, verbose=True)
                            logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters using {method}")
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
                # FULL ASYNC WORKER - Use CLEAN PIPELINE (87-93% accuracy)
                logger.info(f"[DIAGNOSTIC:{task_id}] Step 9: Using CLEAN PIPELINE for async processing (87-93% accuracy)")
                
                try:
                    logger.info(f"[DIAGNOSTIC:{task_id}] Step 10: Importing full pipeline (with clustering & verification)...")
                    from src.citation_extraction_endpoint import extract_citations_with_clustering
                    import time
                    logger.info(f"[DIAGNOSTIC:{task_id}] Step 10: Full pipeline import SUCCESS")

                    # CRITICAL FIX: Always disable verification for URL processing to prevent timeout
                    # URLs can contain many citations that would cause verification timeouts
                    enable_verification = input_data.get('enable_verification', True)  # Default to True for normal operation
                    enable_verification = False if input_type == 'url' else enable_verification
                    
                    logger.info(f"[TASK:{task_id}] Running full pipeline with verification={enable_verification}")
                    
                    # Create progress callback for worker
                    def worker_progress_callback(progress: int, step: str, message: str):
                        """Update progress via verification manager."""
                        logger.info(f"[TASK:{task_id}] 🔄 PROGRESS UPDATE: {progress}% - {step}: {message}")
                        try:
                            vm.update_progress(task_id, processed=progress, total=100, message=f'{progress}% - {step}: {message}')
                        except Exception as e:
                            logger.warning(f"[TASK:{task_id}] Failed to update progress: {e}")
                    
                    # Extract enable_verification flag from input_data
                    enable_verification = input_data.get('enable_verification', True)  # Default to True for normal operation
                    logger.info(f"[TASK:{task_id}] enable_verification flag: {enable_verification}")
                    
                    logger.info(f"[TASK:{task_id}] About to call unified pipeline with verification fix")
                    
                    # SYNCHRONOUS COMPLETION - Wait for full verification
                    # Import required modules for synchronous processing
                    import asyncio
                    import gc  # Garbage collection for memory management
                    from src.unified_processing_pipeline import process_citations_unified
                    
                    # Worker stability: Monitor memory usage before processing
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        logger.info(f"[TASK:{task_id}] Worker memory usage: {memory_mb:.1f}MB before processing")
                        
                        # If memory usage is high, force garbage collection
                        if memory_mb > 500:  # 500MB threshold
                            logger.warning(f"[TASK:{task_id}] High memory usage detected, forcing garbage collection")
                            gc.collect()
                    except ImportError:
                        logger.info(f"[TASK:{task_id}] psutil not available for memory monitoring")
                    
                    # Run full pipeline with verification and wait for completion
                    logger.info(f"[TASK:{task_id}] 🔄 Processing with verification={enable_verification}...")
                    
                    try:
                        pipeline_result = asyncio.run(process_citations_unified(
                            text, 
                            processing_mode="enhanced_sync", 
                            enable_parallel_verification=enable_verification if enable_verification else False,  # Only enable parallel if verification is enabled
                            enable_verification=enable_verification  # Use the modified flag (False for URLs)
                        ))
                        logger.info(f"[TASK:{task_id}] Full pipeline processing with verification completed")
                        
                        # Worker stability: Memory cleanup after processing
                        try:
                            gc.collect()  # Force garbage collection
                            if 'process' in locals():
                                memory_after = process.memory_info().rss / 1024 / 1024
                                logger.info(f"[TASK:{task_id}] Worker memory usage: {memory_after:.1f}MB after processing")
                        except Exception as mem_err:
                            logger.warning(f"[TASK:{task_id}] Memory cleanup failed: {mem_err}")
                        
                    except Exception as pipeline_err:
                        logger.error(f"[TASK:{task_id}] Pipeline processing failed: {pipeline_err}")
                        result = {
                            'status': 'failed',
                            'task_id': task_id,
                            'error': f'Pipeline processing failed: {str(pipeline_err)}'
                        }
                        return result
                    
                    # Extract results from completed pipeline
                    citations_list = list(pipeline_result.get('citations', []) or [])
                    clusters_list = list(pipeline_result.get('clusters', []) or [])
                    
                    logger.info(f"[TASK:{task_id}] 📊 Pipeline completed: {len(citations_list)} citations, {len(clusters_list)} clusters")
                    
                    # Check verification results
                    verified_count = sum(1 for c in citations_list if isinstance(c, dict) and c.get('verified', False))
                    logger.info(f"[TASK:{task_id}] Verification results: {verified_count}/{len(citations_list)} citations verified")
                    
                    # Create final result with complete verification data
                    result = {
                        'success': True,
                        'citations': citations_list,
                        'clusters': clusters_list,
                        'task_id': task_id,
                        'metadata': {
                            'processing_strategy': 'synchronous_full_verification',
                            'text_length': len(text),
                            'verification_completed': True,
                            'citation_count': len(citations_list),
                            'verified_count': verified_count
                        }
                    }
                    
                    # Save final result to Redis for task_status endpoint
                    try:
                        vm.update_progress(task_id, processed=4, total=4, message='Processing complete!')
                        vm.complete(task_id, result)
                        logger.info(f"[TASK:{task_id}] Complete result with verification saved to Redis")
                    except Exception as complete_err:
                        logger.warning(f"[TASK:{task_id}] Failed to save complete result: {complete_err}")
                    
                    return result
                    
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
                try:
                    vm.update_progress(task_id, processed=100, total=100, message='Processing completed successfully')
                    vm.complete(task_id, result)
                except Exception:
                    pass
            else:
                result = {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': result.get('error', 'Processing failed')
                }
            
        else:
            # File inputs: extract text then run full pipeline with verification+clustering
            logger.info(f"[TASK:{task_id}] Using FULL PIPELINE for file input")
            try:
                vm.update_progress(task_id, processed=1, total=4, message='Extracting text from file')
            except Exception:
                pass

            text = ''
            try:
                file_path = input_data.get('file_path')
                if not file_path:
                    raise ValueError('Missing file_path in input_data')
                dop = DockerOptimizedProcessor()
                text = dop.extract_text_from_file_sync(file_path)
                logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters from file")
            except Exception as e:
                logger.error(f"[TASK:{task_id}] File text extraction failed: {e}")
                result = {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': f'File text extraction failed: {str(e)}'
                }
                return result

            try:
                vm.update_progress(task_id, processed=2, total=4, message='Extracting and clustering citations')
            except Exception:
                pass

            try:
                from src.unified_input_processor import UnifiedInputProcessor
                # Extract enable_verification flag from input_data
                enable_verification = input_data.get('enable_verification', True)
                logger.info(f"[TASK:{task_id}] enable_verification flag (file): {enable_verification}")
                
                # Use unified pipeline directly - bypass sync/async decision to avoid recursion
                from src.unified_processing_pipeline import process_citations_unified
                logger.info(f"[TASK:{task_id}] Processing with unified pipeline directly (file path)...")
                
                # Call pipeline directly with asyncio
                import asyncio
                pipeline_result = asyncio.run(process_citations_unified(
                    text, 
                    processing_mode="enhanced_sync", 
                    enable_parallel_verification=enable_verification, 
                    enable_verification=enable_verification
                ))
                logger.info(f"[TASK:{task_id}] Unified pipeline processing completed (file path)")
            except Exception as e:
                logger.error(f"[TASK:{task_id}] Full pipeline failed: {e}")
                result = {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': f'Pipeline failed: {str(e)}'
                }
                return result

            citations = pipeline_result.get('citations', [])
            clusters = pipeline_result.get('clusters', [])

            # If any remain unverified, run enhanced fallback verification and merge
            try:
                unverified_count = sum(1 for c in citations if isinstance(c, dict) and not c.get('verified'))
            except Exception:
                unverified_count = 0
            if citations and unverified_count > 0:
                logger.info(f"[TASK:{task_id}] {unverified_count} citations unverified after pipeline; running enhanced fallback verification")
                try:
                    vm.update_progress(task_id, processed=3, total=max(4, len(citations)), message='Running fallback verification')
                except Exception:
                    pass
                try:
                    from src.async_verification_worker import verify_citations_enhanced as _verify_enhanced
                    # Performance guardrails
                    import os
                    elapsed = time.time() - start_time
                    if elapsed > 90:
                        logger.info(f"[TASK:{task_id}] Skipping fallback (elapsed {elapsed:.1f}s > 90s budget)")
                        enriched = {'success': False, 'citations': []}
                    else:
                        max_targets = int(os.environ.get('FALLBACK_VERIFY_MAX', '12'))
                        priority_tokens = ('F.4th','F.3d','U.S.','S. Ct.','L. Ed.','P.3d','P.2d','A.3d','A.2d')
                        unv = [c for c in citations if isinstance(c, dict) and not c.get('verified')]
                        pri = [c for c in unv if any(tok in (c.get('citation') or '') for tok in priority_tokens)]
                        non = [c for c in unv if c not in pri]
                        targets = (pri + non)[:max_targets]
                        if targets:
                            logger.info(f"[TASK:{task_id}] Fallback targets: {len(targets)}/{len(unv)} (max {max_targets})")
                            enriched = _verify_enhanced(targets, text, task_id, 'file', {'source': 'worker_fallback'})
                        else:
                            enriched = {'success': False, 'citations': []}
                    if isinstance(enriched, dict) and enriched.get('success') and enriched.get('citations'):
                        enriched_list = enriched['citations']
                        try:
                            by_citation = {}
                            for e in enriched_list:
                                key = (e.get('citation') or '').strip()
                                if key and key not in by_citation:
                                    by_citation[key] = e
                            for i, orig in enumerate(citations):
                                if not isinstance(orig, dict):
                                    continue
                                if orig.get('verified'):
                                    continue
                                k = (orig.get('citation') or '').strip()
                                if k and k in by_citation:
                                    cand = by_citation[k]
                                    if isinstance(cand, dict) and cand.get('verified'):
                                        citations[i] = cand
                            logger.info(f"[TASK:{task_id}] Fallback verification merged; remaining unverified: {sum(1 for c in citations if isinstance(c, dict) and not c.get('verified'))}")
                        except Exception as merge_err:
                            logger.warning(f"[TASK:{task_id}] Fallback merge warning: {merge_err}")
                    else:
                        logger.warning(f"[TASK:{task_id}] Fallback verification returned no enhancements")
                except Exception as e:
                    logger.error(f"[TASK:{task_id}] Fallback verification error: {e}")

            try:
                total = max(4, len(citations) or 4)
                vm.update_progress(task_id, processed=3, total=total, message='Verifying citations and finalizing')
            except Exception:
                pass

            result = {
                'status': 'completed',
                'task_id': task_id,
                'citations': citations,
                'clusters': clusters,
                'metadata': {
                    'processing_strategy': 'full_async_with_verification',
                    'text_length': len(text)
                }
            }

            try:
                vm.complete(task_id, result)
            except Exception:
                pass
        
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
                redis_url = os.environ.get('REDIS_URL', 'redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')
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
        try:
            vm.fail(task_id, error_msg)
        except Exception:
            pass
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
        try:
            vm.fail(task_id, error_msg)
        except Exception:
            pass
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
    """
    Enhanced RQ worker with memory management, graceful shutdown, and better monitoring.
    
    Features:
    - Memory usage monitoring and soft limits
    - Automatic restart after job count threshold
    - Graceful shutdown on signals
    - Detailed logging
    - Resource usage tracking
    """
    
    def __init__(self, *args, **kwargs):
        # Configure memory limits
        self.max_memory_mb = int(os.environ.get('WORKER_MAX_MEMORY_MB', 2048))  # 2GB default
        self.memory_check_interval = int(os.environ.get('MEMORY_CHECK_INTERVAL', 5))  # jobs
        
        # Configure job limits
        self.job_count = 0
        self.max_jobs = int(os.environ.get('MAX_JOBS_BEFORE_RESTART', 100))
        
        # Initialize worker with custom queue name if specified
        queue_name = os.environ.get('RQ_QUEUE_NAME', 'casestrainer')
        if 'queues' not in kwargs:
            kwargs['queues'] = [queue_name]
            
        # Configure worker name for better identification
        if 'name' not in kwargs:
            kwargs['name'] = f'worker-{os.getpid()}@{os.uname().nodename}'
            
        # Note: RQ Worker only accepts connection, queues, and name parameters
        # Other settings like job_timeout, result_ttl are set per-job or globally
        
        super().__init__(*args, **kwargs)
        
        # Initialize metrics
        self.start_time = time.time()
        self.metrics = {
            'jobs_completed': 0,
            'jobs_failed': 0,
            'memory_high_watermark': 0,
            'last_memory_check': 0
        }
        
        logger.info(f"Initialized RobustWorker with max_memory={self.max_memory_mb}MB, "
                  f"max_jobs={self.max_jobs}, queues={kwargs['queues']}")
        
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

class CodeChangeMonitor:
    """Monitor Python files for changes and trigger worker reload."""
    
    def __init__(self, watch_dir='/app/src', check_interval=2):
        self.watch_dir = Path(watch_dir)
        self.check_interval = check_interval
        self.file_mtimes = {}
        self.should_reload = False
        self.monitoring = False
        
        # Scan initial state
        self._scan_files()
        logger.info(f"📁 Code monitor initialized: watching {len(self.file_mtimes)} Python files in {watch_dir}")
    
    def _scan_files(self):
        """Scan all Python files and record their modification times."""
        try:
            for py_file in self.watch_dir.rglob('*.py'):
                # Skip __pycache__ directories
                if '__pycache__' not in str(py_file):
                    try:
                        self.file_mtimes[str(py_file)] = py_file.stat().st_mtime
                    except Exception as e:
                        logger.debug(f"Could not stat {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Error scanning files: {e}")
    
    def check_for_changes(self):
        """Check if any files have been modified."""
        try:
            for py_file in self.watch_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue
                    
                file_path = str(py_file)
                try:
                    current_mtime = py_file.stat().st_mtime
                    
                    if file_path not in self.file_mtimes:
                        # New file detected
                        logger.info(f"🆕 New file detected: {py_file.name}")
                        self.file_mtimes[file_path] = current_mtime
                        self.should_reload = True
                        return True
                    elif current_mtime > self.file_mtimes[file_path]:
                        # Modified file detected
                        logger.warning(f"🔄 Code change detected: {py_file.name}")
                        logger.warning(f"   Full path: {file_path}")
                        self.file_mtimes[file_path] = current_mtime
                        self.should_reload = True
                        return True
                except Exception as e:
                    logger.debug(f"Could not check {file_path}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error checking for changes: {e}")
        
        return False
    
    def start_monitoring(self, worker_pid):
        """Start monitoring in a background thread."""
        self.monitoring = True
        
        def monitor_loop():
            logger.info(f"Auto-reload enabled: monitoring for code changes every {self.check_interval}s")
            while self.monitoring:
                time.sleep(self.check_interval)
                if self.check_for_changes():
                    logger.warning("CODE CHANGED - Restarting worker to load new code...")
                    os.kill(worker_pid, signal.SIGTERM)
                    break
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False

def process_citation_task_async(task_id: str, document_text: str, document_type: str):
    """Async citation processing task for RQ workers with progress tracking."""
    
    logger.info(f"process_citation_task_async STARTED: task_id={task_id}, text_length={len(document_text)}")
    
    try:
        # Import the progress manager
        from src.progress_manager import ProgressManager
        
        # Initialize progress manager with Redis
        progress_manager = ProgressManager(redis_client=redis_conn)
        
        # Create progress tracker
        from src.progress_manager import ProgressTracker
        tracker = ProgressTracker(task_id, total_steps=25)  # Default steps
        
        # Store tracker in active tasks
        progress_manager.active_tasks[task_id] = tracker
        
        # Update initial progress
        progress_manager.update_progress(task_id, 0, "started", "Processing started...")
        
        # Create async event loop
        import asyncio
        
        async def run_async_processing():
            """Run the async processing in this worker."""
            try:
                # Get the async processor
                processor = progress_manager.async_processor
                
                # Call the async processing method
                await processor._process_document_async(task_id, document_text, document_type, tracker)
                
            except Exception as e:
                logger.error(f"Error in async processing: {e}")
                import traceback
                traceback.print_exc()
                
                # Update progress with error
                progress_manager.update_progress(
                    task_id, 0, "failed", f"Processing failed: {str(e)}", error=str(e)
                )
        
        # Run the async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_async_processing())
        finally:
            loop.close()
        
        logger.info(f"process_citation_task_async COMPLETED: task_id={task_id}")
        
    except Exception as e:
        logger.error(f"process_citation_task_async FAILED: task_id={task_id}, error={e}")
        import traceback
        traceback.print_exc()
        
        # Try to update progress with error if possible
        try:
            from src.progress_manager import ProgressManager
            progress_manager = ProgressManager(redis_client=redis_conn)
            progress_manager.update_progress(
                task_id, 0, "failed", f"Task failed: {str(e)}", error=str(e)
            )
        except:
            pass  # Best effort error reporting
    
    return {"task_id": task_id, "status": "completed"}

def main():
    """Main entry point for the RQ worker with enhanced error handling and monitoring."""
    print("=" * 80, flush=True)
    print("DEBUG STEP 1: main() function entered", flush=True)
    print("=" * 80, flush=True)
    
    # Configure logging
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    print("DEBUG STEP 2: Logging configured", flush=True)
    
    # Log startup information
    print("="* 80, flush=True)
    print("🚀 RQ WORKER MAIN() CALLED - AUTO-RELOAD CHECK STARTING", flush=True)
    print("=" * 80, flush=True)
    logger.info("=" * 80)
    logger.info(f"Starting CaseStrainer Worker (PID: {os.getpid()})")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Redis URL: {os.environ.get('REDIS_URL', 'redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')}")
    logger.info("=" * 80)
    
    print("DEBUG STEP 3: Startup info logged", flush=True)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("DEBUG STEP 4: Signal handlers configured", flush=True)
    
    # Configure queue and worker name
    queue_name = os.environ.get('RQ_QUEUE_NAME', 'casestrainer')
    worker_name = f'worker-{os.getpid()}@{os.uname().nodename}'
    
    print(f"DEBUG STEP 5: Queue={queue_name}, Worker={worker_name}", flush=True)
    
    # CRITICAL: Clean up any stale registration with the same name
    # This prevents "worker already exists" errors after container restarts
    try:
        from rq import Worker
        existing_workers = Worker.all(connection=redis_conn)
        for w in existing_workers:
            if w.name == worker_name:
                logger.info(f"Removing stale worker registration: {worker_name}")
                print(f"🧹 Removing stale worker registration: {worker_name}", flush=True)
                w.register_death()
                break
    except Exception as e:
        logger.warning(f"Could not clean up stale worker registration: {e}")
        print(f"⚠️  Could not clean up stale worker: {e}", flush=True)
    
    # Configure worker settings
    worker_functions = register_worker_functions()
    logger.info(f"Worker will register functions: {worker_functions}")
    
    worker_kwargs = {
        'connection': redis_conn,
        'queues': [queue_name],
        'name': worker_name
    }
    
    print("DEBUG STEP 6: Worker kwargs configured", flush=True)
    
    # Check if auto-reload is enabled (for development)
    auto_reload = os.environ.get('RQ_WORKER_AUTORELOAD', 'false').lower() == 'true'
    
    print(f"DEBUG STEP 7: Auto-reload check: RQ_WORKER_AUTORELOAD={os.environ.get('RQ_WORKER_AUTORELOAD', 'not set')}, auto_reload={auto_reload}", flush=True)
    
    # Start the worker with error handling
    max_restarts = 10
    restart_count = 0
    monitor = None  # Initialize here to avoid UnboundLocalError
    
    print(f"DEBUG STEP 8: About to enter worker loop (max_restarts={max_restarts})", flush=True)
    
    while restart_count < max_restarts:
        print(f"DEBUG STEP 9: Loop iteration {restart_count + 1}/{max_restarts}", flush=True)
        
        try:
            print("DEBUG STEP 10: Inside try block", flush=True)
            logger.info(f"Starting worker (attempt {restart_count + 1}/{max_restarts})")
            
            print("DEBUG STEP 11: About to create RobustWorker", flush=True)
            worker = RobustWorker(**worker_kwargs)
            print("DEBUG STEP 12: RobustWorker created successfully", flush=True)
            
            # Start code change monitor if auto-reload is enabled
            if auto_reload:
                print("DEBUG STEP 13: Auto-reload is TRUE, starting monitor...", flush=True)
                try:
                    print("DEBUG STEP 14: Creating CodeChangeMonitor instance", flush=True)
                    monitor = CodeChangeMonitor(watch_dir='/app/src', check_interval=2)
                    print("DEBUG STEP 15: CodeChangeMonitor created, starting monitoring", flush=True)
                    monitor.start_monitoring(os.getpid())
                    print("DEBUG STEP 16: Auto-reload monitor started successfully!", flush=True)
                    logger.info("Auto-reload monitor started successfully")
                except Exception as e:
                    print(f"DEBUG: Monitor exception: {e}", flush=True)
                    logger.warning(f"Could not start code monitor: {e}")
                    logger.warning("Continuing without auto-reload...")
                    monitor = None
            else:
                print("DEBUG STEP 13: Auto-reload is FALSE", flush=True)
                logger.info("Auto-reload disabled. Set RQ_WORKER_AUTORELOAD=true to enable.")
            
            print("DEBUG STEP 17: About to call worker.work()", flush=True)
            logger.info("Worker started. Press Ctrl+C to exit.")
            worker.work(logging_level='INFO')
            print("DEBUG STEP 18: worker.work() returned", flush=True)
            
            # Stop monitoring if active
            if monitor:
                monitor.stop_monitoring()
                
            break  # Exit loop if worker exits cleanly
                
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            if monitor:
                monitor.stop_monitoring()
            break
            
        except Exception as e:
            if monitor:
                monitor.stop_monitoring()
                
            restart_count += 1
            wait_time = min(2 ** restart_count, 60)  # Exponential backoff, max 60s
            
            logger.error(
                f"Worker crashed (attempt {restart_count}/{max_restarts}). "
                f"Restarting in {wait_time} seconds...",
                exc_info=True
            )
            
            time.sleep(wait_time)
    
    if restart_count >= max_restarts:
        logger.critical("Maximum restart attempts reached. Worker shutting down.")
    else:
        logger.info("Worker shutdown complete")

if __name__ == '__main__':
    main() 