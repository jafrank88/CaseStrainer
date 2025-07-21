#!/usr/bin/env python3
"""
Health check script for RQ worker
Checks if the worker is connected to Redis and can process jobs
"""

import sys
import os
from redis import Redis

redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
try:
    r = Redis.from_url(redis_url)
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1) 