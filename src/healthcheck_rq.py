#!/usr/bin/env python3
"""
Health check script for RQ workers.

This script verifies that:
1. Redis is accessible
2. The worker can connect to the queue
3. At least one worker process is present (via Worker.all() or rq:worker:* keys)
"""

import sys
import redis
from rq import Queue, Worker


def main():
    """Perform health check for RQ worker."""
    try:
        from src.config import REDIS_URL
        redis_conn = redis.from_url(REDIS_URL)

        # Test Redis ping
        redis_conn.ping()

        # Check if worker can access queue
        queue = Queue("casestrainer", connection=redis_conn)

        # Get worker count via RQ API (uses rq:workers / rq:workers:queue set)
        workers = Worker.all(connection=redis_conn)
        active_workers = [w for w in workers if w.state == "busy" or w.state == "idle"]

        if len(active_workers) > 0:
            print(f"OK: Redis connected, {len(active_workers)} active workers")
            sys.exit(0)

        # Fallback: RQ 2.x sometimes does not populate rq:workers set; check for any worker keys
        worker_keys = list(redis_conn.keys("rq:worker:*") or [])
        if worker_keys:
            # At least one worker key exists (heartbeat keys); consider healthy
            print(f"OK: Redis connected, {len(worker_keys)} worker(s) via keys (registry empty)")
            sys.exit(0)

        print(f"WARNING: No active workers found. Total workers: {len(workers)}")
        sys.exit(1)

    except redis.exceptions.ConnectionError as e:  # type: ignore[attr-defined]
        print(f"ERROR: Cannot connect to Redis: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
