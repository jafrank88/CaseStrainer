"""
POST /analyze route: thin wrapper that calls the analyze service.
"""

import logging

from flask import request

from src.rate_limiter import rate_limit

logger = logging.getLogger(__name__)


def register_analyze_routes(bp):
    """Register the /analyze POST route on the given blueprint."""

    @bp.route("/analyze", methods=["POST"])
    @rate_limit(max_calls=30, window=60)
    def analyze():
        """Main analysis endpoint: file, JSON, form, or URL. Delegates to analyze_service."""
        from src.api.services.analyze_service import handle_analyze
        return handle_analyze(request)
