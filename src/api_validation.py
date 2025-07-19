"""
Input validation utilities for the CaseStrainer API.
"""

import re
from functools import wraps
from flask import jsonify, request
import logging
from typing import Callable, Any, Tuple, List
from .config import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)


def validate_json_content_type(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to validate that the request has JSON content type."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            logger.warning("Request must be JSON")
            return jsonify({"error": "Content-Type must be application/json"}), 415
        return f(*args, **kwargs)

    return decorated_function


def validate_required_fields(required_fields: List[str]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate that required fields are present in the request JSON."""

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
                return (
                    jsonify(
                        {
                            "error": "Missing required fields",
                            "missing_fields": missing_fields,
                        }
                    ),
                    400,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_citation_text(text: str) -> Tuple[bool, str]:
    """Validate that the citation text is a non-empty string."""
    if not isinstance(text, str) or not text.strip():
        return False, "Citation text must be a non-empty string"

    # Check for potentially malicious content
    if len(text) > 1000:  # Reasonable max length for a citation
        return False, "Citation text is too long"

    # Check for common injection patterns
    if re.search(r"[\x00-\x1F\x7F-\xFF]", text):
        return False, "Citation contains invalid characters"

    return True, ""


def validate_case_name(case_name: str) -> Tuple[bool, str]:
    """Validate that the case name is a string (can be empty)."""
    if case_name is not None and not isinstance(case_name, str):
        return False, "Case name must be a string"
    return True, ""


def validate_citation_request(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to validate a citation verification request."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()

        # Check required fields
        if "citation" not in data:
            return jsonify({"error": "Missing required field: citation"}), 400

        # Validate citation text
        is_valid, error = validate_citation_text(data["citation"])
        if not is_valid:
            return jsonify({"error": f"Invalid citation: {error}"}), 400

        # Validate case name if provided
        if "case_name" in data:
            is_valid, error = validate_case_name(data["case_name"])
            if not is_valid:
                return jsonify({"error": f"Invalid case name: {error}"}), 400

        return f(*args, **kwargs)

    return decorated_function


def validate_file_upload(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to validate file upload requests."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Check file extension
        allowed_extensions = ALLOWED_EXTENSIONS
        if (
            file.filename is None
            or "." not in file.filename
            or file.filename.rsplit(".", 1)[1].lower() not in allowed_extensions
        ):
            return (
                jsonify(
                    {
                        "error": "Invalid file type. Allowed types: "
                        + ", ".join(allowed_extensions)
                    }
                ),
                400,
            )

        return f(*args, **kwargs)

    return decorated_function


def validate_file_direct(file: Any) -> Tuple[bool, str]:
    """Direct function to validate a file object (not a decorator)."""
    if not file:
        return False, "No file provided"
    
    if file.filename == "":
        return False, "No selected file"
    
    # Check file extension
    allowed_extensions = ALLOWED_EXTENSIONS
    if (
        file.filename is None
        or "." not in file.filename
        or file.filename.rsplit(".", 1)[1].lower() not in allowed_extensions
    ):
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (50MB limit)
    if hasattr(file, 'content_length') and file.content_length > 50 * 1024 * 1024:
        return False, "File size must be less than 50MB"
    
    return True, ""


def validate_text_input(text: str) -> Tuple[bool, str]:
    """Validate that the text input is a non-empty, reasonable-length string with no control characters."""
    if not isinstance(text, str) or not text.strip():
        return False, "Text input must be a non-empty string"
    if len(text) > 100000:  # Arbitrary max length for text input
        return False, "Text input is too long (max 100,000 characters)"
    # Check for control characters
    if re.search(r"[\x00-\x1F\x7F-\xFF]", text):
        return False, "Text input contains invalid control characters"
    return True, ""

def validate_url_input(url: str) -> Tuple[bool, str]:
    """Validate that the URL input is a non-empty, valid http(s) URL."""
    if not isinstance(url, str) or not url.strip():
        return False, "URL must be a non-empty string"
    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)"
    # Basic URL pattern check
    url_pattern = re.compile(r'^https?://[\w\-\.]+(:\d+)?(/[\w\-\./?%&=]*)?$', re.IGNORECASE)
    if not url_pattern.match(url):
        return False, "URL must start with http:// or https:// and be a valid URL"
    return True, ""
