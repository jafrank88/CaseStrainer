#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ValidationTimeoutError(Exception):
    """Exception raised when validation operation times out."""
    pass

import logging
import os
import time
import warnings
from typing import Optional, Dict, Any

# Configure logging first
logger = logging.getLogger(__name__)

# Markdown and eyecite imports removed as they are not used

import sys
import flask
from flask import jsonify

# Configure logging
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the modules
from config import configure_logging

# Configure logging if not already configured
if not logging.getLogger().hasHandlers():
    configure_logging()

logger.info("Loading enhanced_validator_production.py v0.5.5 - Modified 2025-06-10")

def log_step(message: str, level: str = "info"):
    """Helper function to log processing steps with consistent formatting."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[VALIDATOR] {message}")
    return message

def extract_text_from_url(url: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use src.document_processing_unified.extract_text_from_url instead.
    This function will be removed in a future version.
    """
    warnings.warn(
        "extract_text_from_url is deprecated. Use src.document_processing_unified.extract_text_from_url instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from document_processing_unified import extract_text_from_url as unified_extract_text_from_url
    text = unified_extract_text_from_url(url)
    return {
        'status': 'success',
        'text': text,
        'content_type': 'text/plain'
    }

def make_error_response(error_type: str, message: str, details: Optional[str] = None, 
                       status_code: int = 400, source_type: Optional[str] = None,
                       source_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> flask.Response:
    """Create a standardized error response."""
    response_data = {
        'status': 'error',
        'error_type': error_type,
        'message': message,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    
    if details:
        response_data['details'] = details
    if source_type:
        response_data['source_type'] = source_type
    if source_name:
        response_data['source_name'] = source_name
    if metadata:
        response_data['metadata'] = metadata
        
    response = jsonify(response_data)
    response.status_code = status_code
    return response

# Note: The enhanced validator functionality is now integrated into the main /api/analyze endpoint
# All blueprint-related code and deprecated endpoints have been removed
