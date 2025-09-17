#!/usr/bin/env python3
"""
Test script for the enhanced citation verification worker task.
"""
import os
import sys
import logging
import time
from rq import Queue
from redis import Redis

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_citation_verification():
    """Test the citation verification task."""
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
        
        # Test text with citations
        test_text = """
        A federal court may ask this court to answer a question of Washington law when a 
        resolution of that question is necessary to resolve a case before the federal court. 
        RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
        
        In State v. Smith, 150 Wn.2d 135, 75 P.3d 934 (2003), the court held that...
        """
        
        # Enqueue the citation verification task
        job = queue.enqueue(
            'worker_tasks.verify_citations_enhanced',
            args=([], test_text, 'test_doc_001', 'legal_document', {
                'source': 'test_script',
                'test_case': 'basic_citation_verification'
            }),
            job_timeout=300,  # 5 minutes
            result_ttl=3600  # Keep results for 1 hour
        )
        
        logger.info(f"Enqueued citation verification job with ID: {job.id}")
        
        # Wait for the job to complete
        max_wait = 60  # 1 minute max
        wait_interval = 2  # Check every 2 seconds
        waited = 0
        
        logger.info("Waiting for job to complete...")
        while waited < max_wait:
            job.refresh()
            status = job.get_status()
            
            if status == 'finished':
                logger.info("Job completed successfully!")
                result = job.result
                
                # Print summary
                print("\n" + "="*80)
                print("CITATION VERIFICATION RESULTS")
                print("="*80)
                print(f"Document ID: {result.get('doc_id')}")
                print(f"Status: {result.get('status')}")
                print(f"Processing time: {result.get('processing_time_seconds', 0):.2f} seconds")
                
                # Print citation summary
                citations = result.get('verified_citations', [])
                print(f"\nProcessed {len(citations)} citations:")
                for i, citation in enumerate(citations[:5], 1):  # Show first 5 citations
                    print(f"  {i}. {citation.get('original_citation', 'N/A')} - {citation.get('status')} (confidence: {citation.get('confidence', 0):.0%})")
                
                if len(citations) > 5:
                    print(f"  ... and {len(citations) - 5} more citations")
                
                if 'warnings' in result and result['warnings']:
                    print("\nWarnings:")
                    for warning in result['warnings']:
                        print(f"  - {warning}")
                
                print("\n" + "="*80)
                return True
                
            elif status == 'failed':
                logger.error(f"Job failed: {job.exc_info}")
                return False
                
            logger.info(f"Job status: {status}, waiting {wait_interval}s...")
            time.sleep(wait_interval)
            waited += wait_interval
            
        logger.error("Job timed out")
        return False
        
    except Exception as e:
        logger.error(f"Error in test_citation_verification: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=== Starting Citation Verification Test ===")
    success = test_citation_verification()
    if success:
        logger.info("=== Test Completed Successfully ===")
    else:
        logger.error("=== Test Failed ===")
    sys.exit(0 if success else 1)
