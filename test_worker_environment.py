#!/usr/bin/env python3
"""
Test script to diagnose the worker environment and imports.
"""
import os
import sys
import time
import logging
import importlib
from rq import Queue
from redis import Redis

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if required modules can be imported."""
    modules = [
        'unified_extraction_architecture',
        'models',
        'worker_tasks',
        'src.unified_extraction_architecture',
        'src.models',
        'src.worker_tasks'
    ]
    
    results = {}
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            results[module_name] = {
                'status': 'success',
                'path': getattr(module, '__file__', 'unknown')
            }
        except ImportError as e:
            results[module_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    return results

def main():
    """Main function to test the worker environment."""
    try:
        # Connect to Redis
        redis_conn = Redis(
            host='localhost',
            port=6380,
            password='***REDACTED_REDIS_PASSWORD***',
            db=0,
            socket_connect_timeout=5
        )
        redis_conn.ping()
        logger.info("Successfully connected to Redis")
        
        # Create a queue
        queue = Queue('casestrainer', connection=redis_conn)
        
        # Enqueue the import test
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
                logger.info("\nSimple task completed successfully!")
                logger.info(f"Result: {job.result}")
                
                # Now test imports in the worker environment
                logger.info("\nTesting imports in worker environment...")
                import_job = queue.enqueue(
                    'worker_tasks.test_imports',
                    job_timeout=60
                )
                
                logger.info(f"Enqueued import test with ID: {import_job.id}")
                
                # Wait for the import test to complete
                import_waited = 0
                while import_waited < max_wait:
                    import_job.refresh()
                    import_status = import_job.get_status()
                    
                    if import_status == 'finished':
                        logger.info("\nImport test results:")
                        for mod, result in import_job.result.items():
                            if not isinstance(result, dict):
                                logger.info(f"  {mod}: {result}")
                                continue
                                
                            status = result.get('status', 'unknown')
                            if status == 'success':
                                path = result.get('path', 'unknown path')
                                logger.info(f"  ✓ {mod} - {path}")
                            elif status == 'error':
                                error = result.get('error', 'Unknown error')
                                logger.error(f"  ✗ {mod} - {error}")
                            else:
                                logger.info(f"  ? {mod} - {result}")
                        return True
                    elif import_status == 'failed':
                        logger.error(f"Import test failed: {import_job.exc_info}")
                        return False
                        
                    logger.info(f"Import test status: {import_status}, waiting {wait_interval}s...")
                    time.sleep(wait_interval)
                    import_waited += wait_interval
                
                logger.error("Import test timed out")
                return False
                
            elif status == 'failed':
                logger.error(f"Simple task failed: {job.exc_info}")
                return False
                
            logger.info(f"Simple task status: {status}, waiting {wait_interval}s...")
            time.sleep(wait_interval)
            waited += wait_interval
        
        logger.error("Simple task timed out")
        return False
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=== Testing Worker Environment ===")
    success = main()
    if success:
        logger.info("=== Test Completed Successfully ===")
    else:
        logger.error("=== Test Failed ===")
    sys.exit(0 if success else 1)
