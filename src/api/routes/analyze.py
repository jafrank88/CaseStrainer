"""
POST /analyze route: thin wrapper that calls the analyze service.
"""

import logging
import os

from flask import request

from src.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# Configurable via environment so the limit can be raised for tutorial/workshop days
# without a code change or image rebuild.  Defaults: 30 requests / 60 s per IP.
# Example .env override for a tutorial session:
#   ANALYZE_RATE_LIMIT_MAX_CALLS=200
#   ANALYZE_RATE_LIMIT_WINDOW=60
_ANALYZE_MAX_CALLS = int(os.getenv("ANALYZE_RATE_LIMIT_MAX_CALLS", "30"))
_ANALYZE_WINDOW = int(os.getenv("ANALYZE_RATE_LIMIT_WINDOW", "60"))


def register_analyze_routes(bp):
    """Register the /analyze POST route on the given blueprint."""

    @bp.route("/analyze", methods=["POST"])
    @rate_limit(max_calls=_ANALYZE_MAX_CALLS, window=_ANALYZE_WINDOW)
    def analyze():
        """Main analysis endpoint: file, JSON, form, or URL. Delegates to analyze_service."""
        from src.api.services.analyze_service import handle_analyze
        return handle_analyze(request)
