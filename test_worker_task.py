#!/usr/bin/env python3
"""
Test script to verify worker task execution.
"""
import os
import sys
import time
import json
import logging
from rq import Queue
from redis import Redis

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_worker_task():
    """Test worker task execution."""
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
        
        # Enqueue a simple task
        job = queue.enqueue(
            'worker_tasks.simple_task',
            job_timeout=60
        )
        
        logger.info(f"Enqueued simple task with ID: {job.id}")
        
        # Wait for the job to complete
        max_wait = 30
        waited = 0
        wait_interval = 2
        
        while waited < max_wait:
            job.refresh()
            status = job.get_status()
            
            if status == 'finished':
                logger.info("\nTask completed successfully!")
                logger.info(f"Result: {json.dumps(job.result, indent=2)}")
                return True
                
            elif status == 'failed':
                logger.error(f"Task failed: {job.exc_info}")
                return False
                
            logger.info(f"Task status: {status}, waiting {wait_interval}s...")
            time.sleep(wait_interval)
            waited += wait_interval
        
        logger.error("Task timed out")
        return False
        
    except Exception as e:
        logger.error(f"Error in test_worker_task: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=== Testing Worker Task Execution ===")
    success = test_worker_task()
    if success:
        logger.info("=== Test Completed Successfully ===")
    else:
        logger.error("=== Test Failed ===")
    sys.exit(0 if success else 1)
