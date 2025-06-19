"""
Vue.js API Endpoints for CaseStrainer (Updated)

This module provides the API endpoints needed by the Vue.js frontend for the Multitool Confirmed and Unconfirmed Citations tabs.
"""

import os
import uuid
import traceback
from datetime import datetime, timezone
import json
import flask
from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    make_response,
    after_this_request
)
from werkzeug.utils import secure_filename
import sys
import tempfile

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from flask_mail import Message, Mail
from citation_utils import verify_citation, extract_all_citations

# Import configuration
from config import get_config_value

# Get API key
COURTLISTENER_API_KEY = get_config_value("COURTLISTENER_API_KEY")

from src.file_utils import extract_text_from_file

import re
import logging
from src.pdf_handler import PDFHandler, PDFExtractionMethod, PDFExtractionConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s – %(message)s'
)
logger = logging.getLogger(__name__)

# Create a Blueprint for Vue.js API endpoints
vue_api = Blueprint('vue_api', __name__)

@vue_api.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    """
    Unified API endpoint for document analysis and citation verification.
    Handles both file uploads and direct text analysis.
    """
    try:
        # Log request details for debugging
        current_app.logger.info(f"[ANALYZE] Received {request.method} request to /api/analyze")
        current_app.logger.info(f"[ANALYZE] Headers: {dict(request.headers)}")
        current_app.logger.info(f"[ANALYZE] Form data: {request.form.to_dict() if request.form else 'No form data'}")
        current_app.logger.info(f"[ANALYZE] Files: {list(request.files.keys()) if request.files else 'No files'}")
        
        # Handle OPTIONS request for CORS preflight (unchanged) ...
        if request.method == 'OPTIONS':
            response = make_response(jsonify({'status': 'ok'}), 200)
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

        # Check if this is a file upload or document analysis request (unchanged) ...
        if 'file' in request.files or 'file' in request.form or (request.is_json and 'file' in (request.get_json(silent=True) or {})):
            current_app.logger.info("[ANALYZE] Routing to analyze_document")
            return analyze_document()
        # Otherwise, treat it as a citation verification request (unchanged) ...
        current_app.logger.info("[ANALYZE] Routing to handle_verify_citation")
        return handle_verify_citation()
    except Exception as e:
        current_app.logger.error(f"[ANALYZE] Error in /api/analyze endpoint: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        error_response = {
            'status': 'error',
            'message': 'An internal server error occurred',
            'error': str(e)
        }
        response = jsonify(error_response)
        response.status_code = 500
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

def handle_verify_citation():
    # Create a response object (unchanged) ...
    response_headers = {}
    if request.method == 'OPTIONS':
         (unchanged OPTIONS block) ...
         return response

    @after_this_request
    def add_cors_headers(response):
         (unchanged CORS block) ...
         return response

    default_error_response = {
         (unchanged default error response) ...
    }

    try:
         (Log incoming request details (unchanged) ...)
         current_app.logger.info("=== New Request ===")
         current_app.logger.info(f"Method: {request.method}")
         current_app.logger.info(f"Path: {request.path}")
         current_app.logger.info(f"Headers: {dict(request.headers)}")
         current_app.logger.info(f"Content-Type: {request.content_type}")
         current_app.logger.info(f"Mimetype: {request.mimetype}")
         current_app.logger.info(f"Raw data: {request.get_data()}")
         current_app.logger.info(f"Request args: {request.args}")
         current_app.logger.info(f"Request form: {request.form}")
         current_app.logger.info(f"Request JSON: {request.get_json(silent=True)}")

         # --- NEW: Handle pasted text extraction ---
         text = None
         if request.is_json:
             data = request.get_json(force=True, silent=True) or {}
             text = data.get('text')
         elif request.form:
             text = request.form.get('text')
         if text and isinstance(text, str) and text.strip():
             current_app.logger.info(f"[handle_verify_citation] Received pasted text, first 500 chars: {text[:500]}")
             citations = extract_all_citations(text)
             current_app.logger.info(f"[handle_verify_citation] Extracted {len(citations)} citations: {citations}")
             return jsonify({
                 'status': 'success',
                 'citations': citations,
                 'message': f'Extracted {len(citations)} citations from pasted text.'
             }), 200, response_headers
         # --- End NEW block ---

         (Initialize data dict and citation variables (unchanged) ...)
         data = {}
         citation = None
         case_name = ""

         (Parse request data (unchanged) ...)

         (Remainder of handle_verify_citation (unchanged) ...)

    except Exception as e:
         (Unchanged error handling (or "…" if unchanged) …)

# (Remainder of file (analyze_document, get_citation_context, etc.) unchanged (or "…" if unchanged) …) 