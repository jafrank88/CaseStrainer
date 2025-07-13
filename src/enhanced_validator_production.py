#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ValidationTimeoutError(Exception):
    """Exception raised when validation operation times out."""
    pass

import json
import logging
import os
import re
import tempfile
import time
import uuid
import traceback
import warnings
from src.file_utils import extract_text_from_file
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
from src.citation_correction_engine import CitationCorrectionEngine
from src.citation_utils import get_citation_context
import hashlib
from functools import lru_cache
from typing import Optional, Dict, Any

# Configure logging first
logger = logging.getLogger(__name__)

# Check if markdown is available
try:
    import markdown
    from bs4 import BeautifulSoup
    import html
    MARKDOWN_AVAILABLE = True
    logger.info("Markdown and BeautifulSoup packages successfully imported")
except ImportError as e:
    MARKDOWN_AVAILABLE = False
    logger.warning(f"markdown or BeautifulSoup not available, markdown processing will be skipped. Error: {str(e)}")

# Check if eyecite is available
try:
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False
    logger.warning("eyecite not available, falling back to regex citation extraction")

import sys
import time
import requests
import flask
from flask import request, jsonify
from urllib.parse import urlparse

# Import centralized logging configuration

# Configure logging
logger = logging.getLogger(__name__)

# The actual logging configuration will be done when the Flask app is initialized
# and configure_logging() is called from app_final_vue.py

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the modules
from src.config import configure_logging, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

# Configure logging if not already configured
if not logging.getLogger().hasHandlers():
    configure_logging()

# Initialize the citation processor
citation_processor = UnifiedCitationProcessor()

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
    from src.document_processing_unified import extract_text_from_url as unified_extract_text_from_url
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
