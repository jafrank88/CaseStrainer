#!/usr/bin/env python3
"""
Robust RQ Worker for CaseStrainer with memory management and auto-restart
This script starts an RQ worker with better error handling and resource management
"""

import sys
import os
import gc
import psutil
import logging
import time
import signal
from typing import Optional

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustRQWorker:
    """Robust RQ worker with memory management and auto-restart capabilities."""
    
    def __init__(self, queue_name: str = 'casestrainer', max_jobs: int = 100, max_memory_mb: int = 1024):
        self.queue_name = queue_name
        self.max_jobs = max_jobs
        self.max_memory_mb = max_memory_mb
        self.jobs_processed = 0
        self.start_time = time.time()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"Initializing robust RQ worker for queue: {queue_name}")
        logger.info(f"Max jobs before restart: {max_jobs}")
        logger.info(f"Max memory usage: {max_memory_mb}MB")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within acceptable limits."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            logger.debug(f"Current memory usage: {memory_mb:.1f}MB")
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.max_memory_mb}MB)")
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Could not check memory usage: {e}")
            return True  # Assume OK if we can't check
    
    def _cleanup_memory(self):
        """Force garbage collection and memory cleanup."""
        try:
            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Garbage collection freed {collected} objects")
            
            # Clear any cached objects
            if 'citation_service' in globals():
                del globals()['citation_service']
            
            # Clear any large objects that might be cached
            for name in list(globals().keys()):
                if name.startswith('_') or name in ['logger', 'self', 'queue_name', 'max_jobs', 'max_memory_mb']:
                    continue
                try:
                    obj = globals()[name]
                    if hasattr(obj, '__sizeof__'):
                        size = obj.__sizeof__()
                        if size > 1024 * 1024:  # 1MB
                            logger.debug(f"Clearing large object {name} (size: {size})")
                            del globals()[name]
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Error during memory cleanup: {e}")
    
    def _should_restart(self) -> bool:
        """Determine if the worker should restart."""
        # Check job count
        if self.jobs_processed >= self.max_jobs:
            logger.info(f"Processed {self.jobs_processed} jobs, restarting worker")
            return True
        
        # Check memory usage
        if not self._check_memory_usage():
            logger.warning("Memory usage too high, restarting worker")
            return True
        
        # Check uptime (restart every 2 hours)
        uptime = time.time() - self.start_time
        if uptime > 7200:  # 2 hours
            logger.info(f"Worker uptime {uptime:.0f}s, restarting for freshness")
            return True
        
        return False
    
    def _job_handler(self, job, *args, **kwargs):
        """Custom job handler with memory management."""
        try:
            logger.info(f"Processing job {job.id} ({self.jobs_processed + 1}/{self.max_jobs})")
            
            # Check memory before processing
            if not self._check_memory_usage():
                logger.warning("Memory usage too high before job processing")
                self._cleanup_memory()
            
            # Process the job
            result = job.perform()
            
            # Increment job counter
            self.jobs_processed += 1
            
            # Cleanup after each job
            self._cleanup_memory()
            
            logger.info(f"Job {job.id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            self._cleanup_memory()
            raise
    
    def start(self):
        """Start the robust RQ worker."""
        try:
            from rq import Worker, Queue
            from redis import Redis
            import os
            
            # Get Redis connection
            redis_url = os.environ.get('REDIS_URL', 'redis://casestrainer-redis:6379/0')
            redis_conn = Redis.from_url(redis_url)
            
            # Create queue
            queue = Queue(self.queue_name, connection=redis_conn)
            
            logger.info(f"Starting worker for queue: {self.queue_name}")
            logger.info(f"Redis URL: {redis_url}")
            
            # Create worker
            worker = Worker([queue], connection=redis_conn)
            
            # Start the worker with simplified parameters
            worker.work(
                with_scheduler=False,
                max_jobs=self.max_jobs
            )
            
        except Exception as e:
            logger.error(f"Error starting worker: {e}")
            raise

def main():
    """Main entry point for the robust RQ worker."""
    try:
        # Get configuration from environment
        queue_name = os.environ.get('RQ_QUEUE_NAME', 'casestrainer')
        max_jobs = int(os.environ.get('RQ_MAX_JOBS', '100'))
        max_memory_mb = int(os.environ.get('RQ_MAX_MEMORY_MB', '1024'))
        
        # Create and start worker
        worker = RobustRQWorker(
            queue_name=queue_name,
            max_jobs=max_jobs,
            max_memory_mb=max_memory_mb
        )
        
        worker.start()
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 