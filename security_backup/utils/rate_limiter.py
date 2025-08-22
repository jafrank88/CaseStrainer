"""
Rate limiting utility for external API calls.
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A simple rate limiter for API calls.
    
    This ensures we don't exceed the rate limits of external APIs like CourtListener.
    """
    
    def __init__(self, max_calls: int, period: float):
        """
        Initialize the rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to apply rate limiting to a function.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper
    
    def wait(self) -> None:
        """
        Wait if necessary to ensure we don't exceed the rate limit.
        """
        now = time.time()
        
        # Remove calls older than the period
        self.calls = [t for t in self.calls if now - t < self.period]
        
        # If we've reached the limit, wait until the oldest call falls outside the window
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
        
        # Add this call to the list
        self.calls.append(time.time())

# Create a rate limiter for CourtListener API (180 calls per minute)
# Using 175 as a safety buffer to stay under the limit (increased from 170)
courtlistener_limiter = RateLimiter(max_calls=175, period=60)  # 175 calls per minute to be safe

def rate_limited(max_calls: int, period: float) -> Callable:
    """
    Decorator factory for rate limiting.
    
    Args:
        max_calls: Maximum number of calls allowed in the period
        period: Time period in seconds
        
    Returns:
        A decorator that applies rate limiting to the decorated function
    """
    limiter = RateLimiter(max_calls, period)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        return wrapper
    
    return decorator
