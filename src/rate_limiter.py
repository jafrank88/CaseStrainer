"""
Rate Limiter for CaseStrainer API endpoints
Provides protection against abuse and DoS attacks
"""

import time
import os

import threading
from collections import defaultdict
from functools import wraps
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter for API endpoints"""

    def __init__(self):
        self.calls: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.RLock()
        self._cleanup_interval = 3600  # Clean up old entries every hour
        self._last_cleanup = time.time()
        # Optional explicit bypass for controlled load tests.
        # Disabled by default unless RATE_LIMIT_BYPASS_KEY is set.
        self._bypass_key = (os.getenv("RATE_LIMIT_BYPASS_KEY") or "").strip()
        self._bypass_header = (os.getenv("RATE_LIMIT_BYPASS_HEADER") or "X-Load-Test-Key").strip()
        self._warned_bypass_config = False

    def limit(self, max_calls: int = 100, window: int = 3600, key_func=None):
        """
        Rate limiting decorator

        Args:
            max_calls: Maximum number of calls allowed in the window
            window: Time window in seconds
            key_func: Function to extract rate limit key (defaults to IP address)
        """

        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                from flask import request

                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    # Prefer first forwarded IP when present (reverse-proxy aware)
                    forwarded_for = request.headers.get("X-Forwarded-For", "")
                    first_forwarded = forwarded_for.split(",")[0].strip() if forwarded_for else ""
                    key = first_forwarded or request.remote_addr or "unknown"

                # Explicit bypass for trusted load testing only.
                if self._is_bypass_request(request):
                    return f(*args, **kwargs)

                allowed, retry_after, remaining, reset_epoch = self._check_rate_limit(key, max_calls, window)
                if not allowed:
                    from flask import jsonify, make_response

                    logger.warning(
                        "Rate limit exceeded: key=%s method=%s path=%s limit=%s window=%ss retry_after=%ss ua=%s",
                        key,
                        request.method,
                        request.path,
                        max_calls,
                        window,
                        retry_after,
                        request.headers.get("User-Agent", "unknown"),
                    )
                    response = make_response(
                        jsonify(
                            {
                                "error": "Rate limit exceeded",
                                "message": f"Maximum {max_calls} requests per {window} seconds",
                                "retry_after": retry_after,
                            }
                        ),
                        429,
                    )
                    response.headers["Retry-After"] = str(retry_after)
                    response.headers["X-RateLimit-Limit"] = str(max_calls)
                    response.headers["X-RateLimit-Remaining"] = "0"
                    response.headers["X-RateLimit-Reset"] = str(reset_epoch)
                    return response

                result = f(*args, **kwargs)
                try:
                    from flask import make_response

                    response = make_response(result)
                    response.headers["X-RateLimit-Limit"] = str(max_calls)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    response.headers["X-RateLimit-Reset"] = str(reset_epoch)
                    return response
                except Exception:
                    # Keep request path robust even when response wrapping fails.
                    return result

            return wrapper

        return decorator

    def _is_bypass_request(self, request) -> bool:
        """
        Allow controlled bypass when a trusted load-test key is configured.
        Disabled by default.
        """
        if not self._bypass_key:
            return False
        candidate = (request.headers.get(self._bypass_header) or "").strip()
        if not candidate:
            return False
        if candidate == self._bypass_key:
            logger.info(
                "Rate-limit bypass accepted: header=%s method=%s path=%s",
                self._bypass_header,
                request.method,
                request.path,
            )
            return True
        if not self._warned_bypass_config:
            logger.warning("Rate-limit bypass header present but key mismatch")
            self._warned_bypass_config = True
        return False

    def _check_rate_limit(self, key: str, max_calls: int, window: int):
        """Check limit and return (allowed, retry_after, remaining, reset_epoch)."""
        with self.lock:
            now = time.time()

            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup_old_entries()
                self._last_cleanup = now

            calls = self.calls[key]

            calls[:] = [call_time for call_time in calls if now - call_time < window]

            if len(calls) >= max_calls:
                oldest = calls[0] if calls else now
                retry_after = max(1, int(window - (now - oldest)))
                reset_epoch = int(oldest + window)
                return False, retry_after, 0, reset_epoch

            calls.append(now)
            remaining = max(0, max_calls - len(calls))
            oldest = calls[0] if calls else now
            reset_epoch = int(oldest + window)
            return True, 0, remaining, reset_epoch

    def _cleanup_old_entries(self):
        """Remove old rate limit entries to prevent memory leaks"""
        now = time.time()
        old_keys = []

        for key, calls in self.calls.items():
            calls[:] = [call_time for call_time in calls if now - call_time < 86400]

            if not calls:
                old_keys.append(key)

        for key in old_keys:
            del self.calls[key]


class AdvancedRateLimiter:
    """Enhanced rate limiter with IP blocking and advanced features"""

    def __init__(self):
        self.calls: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: set = set()
        self.lock = threading.RLock()
        self._cleanup_interval = 3600  # Clean up old entries every hour
        self._last_cleanup = time.time()
        self._block_duration = 3600  # Block IPs for 1 hour after violation

    def is_allowed(self, ip: str, limit: int = 100, window: int = 3600) -> bool:
        """Check if IP is allowed to make requests"""
        now = time.time()

        if ip in self.blocked_ips:
            logger.warning(f"Blocked IP {ip} attempted access")
            return False

        with self.lock:
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup_old_entries()
                self._last_cleanup = now

            calls = self.calls[ip]

            calls[:] = [call_time for call_time in calls if now - call_time < window]

            if len(calls) >= limit:
                self.blocked_ips.add(ip)
                logger.warning(f"IP {ip} blocked for rate limit violation")
                return False

            calls.append(now)
            return True

    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        with self.lock:
            self.blocked_ips.discard(ip)
            logger.info(f"IP {ip} unblocked")

    def get_blocked_ips(self) -> set:
        """Get list of currently blocked IPs"""
        with self.lock:
            return self.blocked_ips.copy()

    def _cleanup_old_entries(self):
        """Remove old rate limit entries to prevent memory leaks"""
        now = time.time()
        old_keys = []

        for key, calls in self.calls.items():
            calls[:] = [call_time for call_time in calls if now - call_time < 86400]

            if not calls:
                old_keys.append(key)

        for key in old_keys:
            del self.calls[key]


class InputValidator:
    """Input validation utilities"""

    @staticmethod
    def validate_citation_input(citation: str) -> bool:
        """Validate citation input for security"""
        if not citation or len(citation) > 1000:
            return False

        import re

        suspicious_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"data:",
            r"vbscript:",
            r"<iframe[^>]*>",
            r"on\w+\s*=",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, citation, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in citation: {pattern}")
                return False

        return True

    @staticmethod
    def validate_text_input(text: str, max_length: int = 1000000) -> bool:
        """Validate text input"""
        if not text or len(text) > max_length:
            return False

        if "\x00" in text:
            return False

        return True

    @staticmethod
    def validate_url_input(url: str) -> bool:
        """Validate URL input"""
        if not url or len(url) > 2000:
            return False

        import re

        url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(url_pattern, url):
            return False

        suspicious_patterns = [
            r"javascript:",
            r"data:",
            r"vbscript:",
            r"file://",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.warning(f"Suspicious URL pattern detected: {pattern}")
                return False

        return True


rate_limiter = RateLimiter()
advanced_rate_limiter = AdvancedRateLimiter()


def rate_limit(max_calls: int = 100, window: int = 3600):
    """Convenience decorator for rate limiting"""
    return rate_limiter.limit(max_calls, window)


def validate_input(input_type: str = "citation"):
    """Convenience decorator for input validation"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify

            if request.is_json:
                data = request.get_json()
                if input_type == "citation":
                    citation = data.get("citation", "")
                    if not InputValidator.validate_citation_input(citation):
                        return jsonify({"error": "Invalid citation input"}), 400
                elif input_type == "text":
                    text = data.get("text", "")
                    if not InputValidator.validate_text_input(text):
                        return jsonify({"error": "Invalid text input"}), 400
                elif input_type == "url":
                    url = data.get("url", "")
                    if not InputValidator.validate_url_input(url):
                        return jsonify({"error": "Invalid URL input"}), 400

            return f(*args, **kwargs)

        return wrapper

    return decorator
