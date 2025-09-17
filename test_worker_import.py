#!/usr/bin/env python3
"""
Test script to verify RQ worker can import and execute the task function.
"""
import os
import sys
import logging
from rq import Queue
from redis import Redis
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_worker_import():
    """Test if the worker can import and execute a simple task."""
    try:
        # Connect to Redis
        redis_conn = Redis(
            host='localhost',
            port=6380,  # Mapped port from Docker
            password='***REDACTED_REDIS_PASSWORD***',
            db=0,
            socket_connect_timeout=5
        )
        redis_conn.ping()
        logger.info("Successfully connected to Redis")
        
        # Create a queue
        queue = Queue('casestrainer', connection=redis_conn)
        
        # Enqueue a simple task from the worker_tasks module
        job = queue.enqueue(
            'worker_tasks.simple_task',
            job_timeout=60
        )
        logger.info(f"Enqueued simple task with ID: {job.id}")
        
        # Wait for the job to complete
        max_wait = 30
        waited = 0
        
        while waited < max_wait:
            job.refresh()
            status = job.get_status()
            
            if status == 'finished':
                logger.info("Job completed successfully!")
                logger.info(f"Result: {job.result}")
                return True
            elif status == 'failed':
                logger.error(f"Job failed: {job.exc_info}")
                return False
                
            logger.info(f"Job status: {status}, waiting 1s...")
            time.sleep(1)
            waited += 1
            
        logger.error("Job timed out")
        return False
        
    except Exception as e:
        logger.error(f"Error in test_worker_import: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== Starting Worker Import Test ===")
    success = test_worker_import()
    if success:
        logger.info("=== Test Completed Successfully ===")
    else:
        logger.error("=== Test Failed ===")
    sys.exit(0 if success else 1)
