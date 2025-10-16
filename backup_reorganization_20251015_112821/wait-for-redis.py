#!/usr/bin/env python3
"""
Wait for Redis to be ready before starting RQ workers.
This prevents BusyLoadingError during worker startup.
"""

import redis
import time
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_redis(max_wait=60):
    """Wait for Redis to be ready with timeout."""
    
    redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
    logger.info(f"Waiting for Redis at: {redis_url}")
    
    try:
        redis_client = redis.from_url(redis_url)
        
        for attempt in range(max_wait):
            try:
                # Test Redis connection
                redis_client.ping()
                logger.info(f"✅ Redis ready after {attempt} seconds")
                return True
                
            except redis.exceptions.BusyLoadingError:
                if attempt == 0:
                    logger.info("⏳ Redis loading dataset, waiting...")
                elif attempt % 10 == 0:
                    logger.info(f"⏳ Still waiting for Redis ({attempt}s)...")
                time.sleep(1)
                
            except redis.exceptions.ConnectionError as e:
                if attempt == 0:
                    logger.info(f"⏳ Redis not yet available, waiting... ({e})")
                elif attempt % 10 == 0:
                    logger.info(f"⏳ Still waiting for Redis connection ({attempt}s)...")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Unexpected Redis error: {e}")
                if attempt < 5:  # Retry for first 5 seconds
                    time.sleep(1)
                else:
                    raise
        
        # Timeout
        logger.error(f"❌ Redis not ready after {max_wait} seconds")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return False

def main():
    """Main function to wait for Redis."""
    
    logger.info("🔍 Redis Readiness Check Starting...")
    
    if wait_for_redis(max_wait=60):
        logger.info("🎉 Redis is ready! Starting RQ worker...")
        sys.exit(0)  # Success
    else:
        logger.error("💥 Redis readiness check failed!")
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
