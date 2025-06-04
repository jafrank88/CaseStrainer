"""
API endpoints for the Vue.js frontend.
This module provides the API endpoints needed by the Vue.js frontend.
"""

import os
import json
import logging
import time
import uuid
import traceback
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify, current_app, send_from_directory, g
from .api_validation import (
    validate_json_content_type,
    validate_required_fields,
    validate_citation_request,
    validate_file_upload,
)
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import tempfile
from .config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from .enhanced_validator_production import validate_citations_batch
from .citation_utils import (
    extract_citations_from_file,
    extract_citations_from_text,
    verify_citation,
)
