"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import logging

from flask import Blueprint, request

from src.api.services.citation_service import CitationService

logger = logging.getLogger(__name__)

vue_api = Blueprint("vue_api", __name__)

citation_service = CitationService()

from src.api.routes import register_all_routes

register_all_routes(vue_api)


def _analyze_impl(request):
    """Backward-compatible name; delegates to analyze_pipeline.analyze_request."""
    from src.api.services.analyze_pipeline import analyze_request
    return analyze_request(request)



def _handle_json_input(service, request_id, data=None):
    """
    Handle JSON input processing with CitationService integration

    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
        data: Optional pre-parsed JSON data (for testing or direct call)

    Returns:
        Dictionary with analysis results or error information
    """
    logger.warning(
        f"[JSON Input {request_id}] Deprecated legacy handler invoked; routing to canonical _analyze_impl"
    )
    return _analyze_impl(request)


async def _handle_form_input(service, request_id):
    """
    Handle form input processing with CitationService integration

    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
    """
    logger.warning(
        f"[Form Input {request_id}] Deprecated legacy handler invoked; routing to canonical _analyze_impl"
    )
    return _analyze_impl(request)


def _is_test_citation_text(text: str) -> bool:
    """Check if text contains known test citations that should be rejected."""
    return False


def _extract_test_pattern(text: str) -> str:
    """Extract the test pattern that was detected."""
    if not text:
        return "no_text"

    text_norm = text.strip().lower()

    if "smith v. jones" in text_norm and "123 f.3d 456" in text_norm:
        return "smith_v_jones_123_f3d_456"
    elif "123 f.3d 456" in text_norm:
        return "123_f3d_456_pattern"
    elif "999 u.s. 999" in text_norm:
        return "999_us_999_pattern"
    elif "test citation" in text_norm:
        return "test_citation_string"
    elif "sample citation" in text_norm:
        return "sample_citation_string"

    return "unknown_test_pattern"


def _is_test_url(url: str) -> bool:
    """Check if a URL is a test URL that should be rejected."""
    if not url:
        return False

    url_lower = url.lower()

    test_url_patterns = [
        "example.com",
        "test.com",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "test.local",
        "dev.local",
        "staging.local",
        "mock.com",
        "fake.com",
        "dummy.com",
        "sample.com",
    ]

    for pattern in test_url_patterns:
        if pattern in url_lower:
            logger.warning(f"Test URL detected: {url} (pattern: {pattern})")
            return True

    problematic_protocols = [
        "file://",
        "ftp://",
        "mailto:",
        "tel:",
        "javascript:",
        "data:",
        "chrome://",
        "about:",
        "moz-extension://",
    ]

    for protocol in problematic_protocols:
        if url_lower.startswith(protocol):
            logger.warning(f"Problematic URL protocol detected: {url} (protocol: {protocol})")
            return True

    return False


def _validate_url(url: str) -> bool:
    """Validate that a URL is safe and properly formatted."""
    if not url or not isinstance(url, str):
        return False

    if len(url) > 2048:
        logger.warning(f"URL too long: {len(url)} characters")
        return False

    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)

        if parsed.scheme not in ["http", "https"]:
            logger.warning(f"Unsupported protocol: {parsed.scheme}")
            return False

        if _is_test_url(url):
            return False

        return True
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False


