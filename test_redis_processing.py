"""
Test Redis queue integration for async citation processing.
"""

import os
import sys
import time
import json
import logging
from rq import Queue
from redis import Redis
from test_citation_processing import test_citation_processing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_redis_queue():
    """Test Redis queue integration for async processing."""
    try:
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        logger.info(f"Connecting to Redis at {redis_url}")
        
        redis_conn = Redis.from_url(redis_url)
        queue = Queue('casestrainer', connection=redis_conn)
        
        # Test Redis connection
        if not redis_conn.ping():
            raise Exception("Failed to connect to Redis")
            
        logger.info("Successfully connected to Redis")
        
        # Enqueue a test job
        test_text = "This is a test citation to Brown v. Board of Education, 347 U.S. 483 (1954)."
        job = queue.enqueue(
            'src.progress_manager.process_citation_task_direct',
            args=('redis_test_1', 'text', {'text': test_text}),
            job_timeout=600,
            result_ttl=3600
        )
        
        logger.info(f"Enqueued job {job.id}. Waiting for completion...")
        
        # Wait for job to complete
        max_wait = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            job.refresh()
            if job.is_finished:
                result = job.return_value
                logger.info("Job completed successfully!")
                logger.info(f"Result: {json.dumps(result, indent=2)}")
                return True
            elif job.is_failed:
                logger.error(f"Job failed: {job.exc_info}")
                return False
                
            time.sleep(1)
            
        logger.warning("Job did not complete within the expected time")
        return False
        
    except Exception as e:
        logger.error(f"Error testing Redis queue: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=== Starting Redis Queue Test ===")
    success = test_redis_queue()
    if success:
        logger.info("=== Redis Queue Test PASSED ===")
        sys.exit(0)
    else:
        logger.error("=== Redis Queue Test FAILED ===")
        sys.exit(1)
