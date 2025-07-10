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
    """Extract text content from a URL, including PDF support."""
    try:
        logger.info(f"[extract_text_from_url] Fetching URL: {url}")
        response = requests.get(url, timeout=300, stream=True)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"[extract_text_from_url] Content-Type: {content_type}")
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator='\n', strip=True)
        elif 'text/plain' in content_type:
            text = response.text
        elif 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            temp_file = None
            try:
                logger.info(f"[extract_text_from_url] Starting PDF download for URL: {url}")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmp.write(chunk)
                    temp_file = tmp.name
                logger.info(f"[extract_text_from_url] PDF downloaded to: {temp_file}")
                logger.info(f"[extract_text_from_url] Starting text extraction from PDF: {temp_file}")
                text_result = extract_text_from_file(temp_file, file_ext='.pdf')
                if isinstance(text_result, tuple):
                    text, _ = text_result
                else:
                    text = text_result
                logger.info(f"[extract_text_from_url] Text extraction complete from PDF: {temp_file}")
                if isinstance(text, dict):
                    if not text.get('success', True):
                        logger.error(f"[extract_text_from_url] PDF extraction error: {text.get('error')}")
                        return {
                            'status': 'error',
                            'error': text.get('error', 'Failed to extract text from PDF'),
                            'content_type': content_type
                        }
            except Exception as e:
                logger.error(f"[extract_text_from_url] Exception during PDF extraction: {str(e)}")
                return {
                    'status': 'error',
                    'error': f'Error extracting text from PDF: {str(e)}',
                    'content_type': content_type
                }
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                        logger.info(f"[extract_text_from_url] Temporary PDF file deleted: {temp_file}")
                    except Exception as cleanup_e:
                        logger.warning(f"[extract_text_from_url] Could not delete temp file: {cleanup_e}")
        else:
            logger.error(f"[extract_text_from_url] Unsupported content type: {content_type}")
            return {
                'status': 'error',
                'error': f'Unsupported content type: {content_type}',
                'content_type': content_type
            }
        logger.info(f"[extract_text_from_url] Extraction success for URL: {url}")
        return {
            'status': 'success',
            'text': text,
            'content_type': content_type
        }
    except requests.RequestException as e:
        logger.error(f"[extract_text_from_url] RequestException: {str(e)}")
        return {
            'status': 'error',
            'error': f'Failed to fetch URL: {str(e)}',
            'details': traceback.format_exc()
        }
    except Exception as e:
        logger.error(f"[extract_text_from_url] General Exception: {str(e)}")
        return {
            'status': 'error',
            'error': f'Error processing URL: {str(e)}',
            'details': traceback.format_exc()
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
