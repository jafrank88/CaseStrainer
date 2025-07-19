#!/usr/bin/env python3
"""
Health check script for RQ worker
Checks if the worker is connected to Redis and can process jobs
"""

import sys
import os
import time

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def check_rq_worker_health():
    """Check if RQ worker is healthy"""
    try:
        from redis import Redis
        from rq import Queue, Worker
        
        # Get Redis connection from environment
        redis_url = os.environ.get('REDIS_URL', 'redis://casestrainer-redis-prod:6379/0')
        if redis_url.startswith('redis://'):
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            redis_host = parsed.hostname or 'localhost'
            redis_port = parsed.port or 6379
            redis_db = int(parsed.path.lstrip('/')) if parsed.path else 0
        else:
            redis_host = 'localhost'
            redis_port = 6379
            redis_db = 0
        
        # Connect to Redis
        redis_conn = Redis(host=redis_host, port=redis_port, db=redis_db)
        redis_conn.ping()
        
        # Check if there are any workers
        workers = Worker.all(connection=redis_conn)
        if not workers:
            logger.info("No RQ workers found")
            return False
        
        # Check if at least one worker is alive
        for worker in workers:
            if worker.state == 'busy' or worker.state == 'idle':
                logger.info(f"Worker {worker.name} is {worker.state}")
                return True
        
        logger.info("No active workers found")
        return False
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

if __name__ == '__main__':
    # Try multiple times with short intervals
    for attempt in range(3):
        if check_rq_worker_health():
            sys.exit(0)
        if attempt < 2:
            time.sleep(1)
    
    sys.exit(1) 