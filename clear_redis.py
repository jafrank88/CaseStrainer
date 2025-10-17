#!/usr/bin/env python3
"""Clear Redis cache"""
from redis import Redis

r = Redis(host='redis', port=6379, decode_responses=True)
r.flushall()
print("✅ Redis cache cleared!")
