#!/usr/bin/env python3
"""
Health check script for RQ workers.

This script verifies that:
1. Redis is accessible
2. The worker can connect to the queue
3. The worker process is responding
"""

import os
import sys
import redis
from rq import Queue, Worker


def main():
    """Perform health check for RQ worker."""
    try:
        # Check Redis connection
        redis_url = os.environ.get("REDIS_URL", "redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0")
        redis_conn = redis.from_url(redis_url)

        # Test Redis ping
        redis_conn.ping()

        # Check if worker can access queue
        queue = Queue("casestrainer", connection=redis_conn)

        # Get worker count
        workers = Worker.all(connection=redis_conn)
        active_workers = [w for w in workers if w.state == "busy" or w.state == "idle"]

        # At least one worker should be active
        if len(active_workers) == 0:
            print(f"WARNING: No active workers found. Total workers: {len(workers)}")
            sys.exit(1)

        print(f"OK: Redis connected, {len(active_workers)} active workers")
        sys.exit(0)

    except redis.exceptions.ConnectionError as e:
        print(f"ERROR: Cannot connect to Redis: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
