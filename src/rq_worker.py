"""
Robust RQ Worker for CaseStrainer with memory management and auto-restart
This script starts an RQ worker with better error handling and resource management
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
        'src.redis_distributed_processor.DockerOptimizedProcessor.process_document'
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
    """Direct wrapper function to create CitationService instance and call process_citation_task."""
    from src.api.services.citation_service import CitationService
    import asyncio
    import time
    
    service = CitationService()
    
    import platform
    timeout_set = False
    
    if platform.system() != 'Windows':
        try:
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Task {task_id} timed out after 10 minutes")
            
            signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore[attr-defined]
            signal.alarm(600)  # type: ignore[attr-defined]
            timeout_set = True
        except (AttributeError, OSError):
            pass
    
    try:
        start_time = time.time()
        logger.info(f"Starting task {task_id} of type {input_type}")
        
        result = asyncio.run(service.process_citation_task(task_id, input_type, input_data))
        
        processing_time = time.time() - start_time
        logger.info(f"Task {task_id} completed successfully in {processing_time:.2f} seconds")
        return result
        
    except TimeoutError as e:
        logger.error(f"Task {task_id} timed out: {e}")
        return {
            'status': 'failed',
            'error': 'Task timed out after 10 minutes',
            'task_id': task_id
        }
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': task_id
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