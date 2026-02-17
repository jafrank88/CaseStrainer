"""
Redis connection helper for CaseStrainer
Handles both Docker and local development environments
"""

import os

import socket
from redis import Redis
from rq import Queue


def get_redis_url():
    """
    Get the Redis URL from application config (single source of truth).
    """
    from src.config import REDIS_URL
    return REDIS_URL


def get_redis_connection():
    """
    Get a Redis connection for the current environment.

    Returns:
        Redis: Redis connection object
    """
    redis_url = get_redis_url()
    return Redis.from_url(redis_url)


def get_rq_queue(queue_name="casestrainer"):
    """
    Get an RQ queue for the current environment.

    Args:
        queue_name (str): Name of the queue

    Returns:
        Queue: RQ Queue object
    """
    redis_conn = get_redis_connection()
    return Queue(queue_name, connection=redis_conn)
