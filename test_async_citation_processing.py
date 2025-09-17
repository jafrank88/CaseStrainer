"""
Test the async citation processing pipeline
"""

import sys
import os
import logging
import time
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_async_citation_processing():
    """Test the async citation processing pipeline"""
    try:
        # Add the src directory to the path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        # Import required components
        from rq import Queue
        from redis import Redis
        from config import get_config_value
        
        # Import CitationResult from the correct location
        try:
            # Try the direct import first
            from citation import CitationResult
        except ImportError:
            try:
                # Try with src prefix
                from src.citation import CitationResult
            except ImportError:
                # Fallback to a dummy class if needed
                class CitationResult:
                    pass
        
        # Initialize Redis connection with host networking
        # When running on the host, connect to localhost and the mapped port
        redis_url = 'redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0'  # Using port 6380 which is mapped to Redis container's 6379
        logger.info(f"Connecting to Redis at: {redis_url}")
        
        # Initialize Redis connection with explicit settings
        redis_conn = Redis.from_url(
            redis_url,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test the connection
        try:
            redis_conn.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            return False
        
        # Initialize the queue with explicit name
        queue_name = 'casestrainer'
        logger.info(f"Initializing queue: {queue_name}")
        queue = Queue(name=queue_name, connection=redis_conn)
        
        # Test text with citations
        test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."""
        
        # Test if we can import the function directly
        try:
            from src.rq_worker import verify_citations_enhanced
            logger.info("Successfully imported verify_citations_enhanced function")
        except ImportError as e:
            logger.error(f"Failed to import verify_citations_enhanced: {str(e)}")
            logger.error(f"Python path: {sys.path}")
            return False
            
        # Create a test job with the full module path
        logger.info("Enqueuing test job...")
        try:
            job = queue.enqueue(
                'src.rq_worker.verify_citations_enhanced',
                args=([], test_text, 'test_async_123', 'text', {}),
                job_timeout=300,  # 5 minute timeout
                result_ttl=3600  # Keep results for 1 hour
            )
            logger.info(f"Job enqueued with ID: {job.id}")
        except Exception as e:
            logger.error(f"Failed to enqueue job: {str(e)}")
            return False
        
        logger.info(f"Job enqueued with ID: {job.id}")
        
        # Wait for the job to complete
        max_wait = 300  # 5 minutes max
        wait_interval = 5  # Check every 5 seconds
        waited = 0
        
        logger.info("Waiting for job to complete...")
        while waited < max_wait:
            job.refresh()
            status = job.get_status()
            
            if status == 'finished':
                logger.info("Job completed successfully!")
                
                # Try to get the result directly from the job
                try:
                    result = job.result
                    if result is not None:
                        logger.info("Job result from job.result:")
                        logger.info(f"Type: {type(result)}")
                        if isinstance(result, dict):
                            for key, value in result.items():
                                logger.info(f"  {key}: {str(value)[:200]}..." if len(str(value)) > 200 else f"  {key}: {value}")
                        else:
                            logger.info(f"  {str(result)[:500]}...")
                    else:
                        logger.info("Job result is None")
                except Exception as e:
                    logger.error(f"Error getting result from job: {str(e)}")
                
                # Also try to get the result directly from Redis
                try:
                    result_key = f"rq:job:{job.id}"
                    result = redis_conn.hgetall(result_key)
                    if result:
                        logger.info("\nRaw Redis job data:")
                        for key, value in result.items():
                            try:
                                key_str = key.decode('utf-8', 'replace') if isinstance(key, bytes) else str(key)
                                value_str = value.decode('utf-8', 'replace') if isinstance(value, bytes) else str(value)
                                logger.info(f"  {key_str}: {value_str[:200]}..." if len(value_str) > 200 else f"  {key_str}: {value_str}")
                            except Exception as e:
                                logger.error(f"  Error processing key {key}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error getting result from Redis: {str(e)}")
                
                return True
                
            elif status == 'failed':
                # Print a summary
                if isinstance(result, dict):
                    print("\n" + "="*80)
                    print("ASYNC PROCESSING RESULTS")
                    print("="*80)
                    
                    if 'citations' in result and result['citations']:
                        print(f"\nFound {len(result['citations'])} citations:")
                        for i, citation in enumerate(result['citations'][:5], 1):  # Show first 5
                            print(f"  {i}. {citation.get('citation', 'N/A')}")
                        if len(result['citations']) > 5:
                            print(f"  ... and {len(result['citations']) - 5} more")
                    
                    if 'error' in result:
                        print("\nERROR:")
                        print(result['error'])
                
                return result
                
            elif job.is_failed:
                logger.error(f"Job failed: {job.exc_info}")
                return {"error": f"Job failed: {job.exc_info}"}
            
            logger.info(f"Job status: {job.get_status()}, waiting {wait_interval}s...")
            time.sleep(wait_interval)
            waited += wait_interval
        
        logger.error("Job timed out")
        return {"error": "Job timed out"}
        
    except Exception as e:
        logger.error(f"Error in test_async_citation_processing: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("=== Starting Async Citation Processing Test ===")
    try:
        result = test_async_citation_processing()
        logger.info("=== Test Completed ===")
    except Exception as e:
        logger.error("=== Test Failed ===", exc_info=True)
        sys.exit(1)
