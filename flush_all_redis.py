#!/usr/bin/env python3
"""Completely flush ALL Redis databases"""
import redis

print("Flushing ALL Redis databases...")
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.flushall()
print("✅ All Redis databases flushed!")
