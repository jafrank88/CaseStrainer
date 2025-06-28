"""
Citation API for CaseStrainer

This module provides API endpoints for accessing citation data
from the JSON files in the CaseStrainer application.
"""

from flask import (
    Blueprint,
    jsonify,
    request,
    make_response,
)
import os
import json
import logging
import uuid
import traceback
from werkzeug.utils import secure_filename
from datetime import datetime
import time
import requests

# Add the project root to the Python path
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from src to ensure consistent imports
from src.citation_utils import extract_citations
from src.citation_processor import CitationProcessor
from src.file_utils import extract_text_from_file
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from src.citation_grouping import group_citations_by_url

# Create an instance of CitationProcessor
citation_processor = CitationProcessor()

# Create an instance of EnhancedMultiSourceVerifier for citation verification
verifier = EnhancedMultiSourceVerifier()

# Create a special logger for citation verification
citation_logger = logging.getLogger("citation_verification")
citation_logger.setLevel(logging.DEBUG)

# Create a file handler for the citation verification logger (per-process log file to avoid Windows file locking issues)
# Use project root logs directory
logs_dir = os.path.join(project_root, "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
pid = os.getpid()
citation_handler = logging.FileHandler(
    os.path.join(logs_dir, f"citation_verification_{pid}.log"), delay=True
)
citation_handler.setLevel(logging.DEBUG)

# Create a formatter for the citation verification logger
citation_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
citation_handler.setFormatter(citation_formatter)

# Add the handler to the logger
citation_logger.addHandler(citation_handler)
print("Enhanced Validator functionality enabled")
USE_ENHANCED_VALIDATOR = True

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a Blueprint for the citation API
citation_api = Blueprint("citation_api", __name__)

# Path to the citation data files
CITATION_VERIFICATION_FILE = os.path.join(
    os.path.dirname(__file__), "citation_verification_results.json"
)
DATABASE_VERIFICATION_FILE = os.path.join(
    os.path.dirname(__file__), "database_verification_results.json"
)

# Upload folder for document analysis
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "rtf", "odt", "html", "htm"}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to generate a unique analysis ID
def generate_analysis_id():
    """Generate a unique ID for the analysis."""
    return str(uuid.uuid4())


# Function to log citation verification details
def log_citation_verification(citation, verification_result, api_response=None):
    """Log detailed information about citation verification process.

    Args:
        citation: The citation text being verified
        verification_result: The result of the verification attempt
        api_response: Optional raw API response for debugging
    """
    citation_logger.info("===== CITATION VERIFICATION DETAILS =====")
    citation_logger.info(f"Citation: {citation}")
    citation_logger.info(f"Verification Result: {verification_result}")

    # Log details about the verification result
    if verification_result:
        citation_logger.info(f"Found: {verification_result.get('found', False)}")
        citation_logger.info(f"Source: {verification_result.get('source')}")
        citation_logger.info(f"Case Name: {verification_result.get('case_name')}")
        citation_logger.info(f"Explanation: {verification_result.get('explanation')}")

        # Log details about the citation
        details = verification_result.get("details", {})
        if details:
            citation_logger.info("Citation Details:")
            for key, value in details.items():
                citation_logger.info(f"  {key}: {value}")

    # Log API response if provided
    if api_response:
        citation_logger.info("API Response:")
        if isinstance(api_response, dict):
            for key, value in api_response.items():
                if key != "results" and key != "data":
                    citation_logger.info(f"  {key}: {value}")
            # Log API results summary if available
            if "results" in api_response:
                citation_logger.info(
                    f"  Results count: {len(api_response['results']) if isinstance(api_response['results'], list) else 'N/A'}"
                )
        else:
            citation_logger.info(f"  Raw response: {str(api_response)[:500]}...")

    citation_logger.info("=========================================")


def load_citation_verification_data():
    """Load data from the citation verification results file."""
    try:
        if os.path.exists(CITATION_VERIFICATION_FILE):
            with open(CITATION_VERIFICATION_FILE, "r") as f:
                return json.load(f)
        return {"newly_confirmed": [], "still_unconfirmed": []}
    except Exception as e:
        logger.error(f"Error loading citation verification data: {str(e)}")
        return {"newly_confirmed": [], "still_unconfirmed": []}


def load_database_verification_data():
    """Load data from the database verification results file."""
    try:
        if os.path.exists(DATABASE_VERIFICATION_FILE):
            with open(DATABASE_VERIFICATION_FILE, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading database verification data: {str(e)}")
        return []


@citation_api.route("/confirmed-with-multitool-data", methods=["GET"])
@citation_api.route("/confirmed_with_multitool_data", methods=["GET"])
def confirmed_with_multitool_data():
    """Get confirmed citations data with multitool validation."""
    try:
        # Load the data
        data = load_citation_verification_data()
        # Group citations by canonical URL
        grouped_data = group_citations_by_url(data)
        # Create response data
        response_data = {
            "status": "success",
            "data": grouped_data,
            "count": len(grouped_data),
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Returning {len(grouped_data)} confirmed citations")
        # Create a response with CORS headers
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST")
        return response
    except Exception as e:
        logger.error(f"Error loading confirmed citations data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": [],
            "count": 0
        }), 500


@citation_api.route("/unconfirmed-citations-data", methods=["GET"])
@citation_api.route("/unconfirmed_citations_data", methods=["POST", "GET"])
def unconfirmed_citations_data():
    """Get unconfirmed citations data."""
    try:
        # Load the data
        data = load_database_verification_data()
        # Group citations by canonical URL
        grouped_data = group_citations_by_url(data)
        # Create response data
        response_data = {
            "status": "success",
            "data": grouped_data,
            "count": len(grouped_data),
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Returning {len(grouped_data)} unconfirmed citations")
        # Create a response with CORS headers
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST")
        return response
    except Exception as e:
        logger.error(f"Error loading unconfirmed citations data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": [],
            "count": 0
        }), 500


@citation_api.route("/reprocess-citation", methods=["POST"])
def reprocess_citation():
    """Reprocess a specific citation with enhanced validation."""
    try:
        data = request.get_json()
        if not data or 'citation' not in data:
            return jsonify({"error": "No citation provided"}), 400
            
        citation = data['citation']
        logger.info(f"Reprocessing citation: {citation}")
        
        # Verify the citation using the unified workflow
        result = verifier.verify_citation_unified_workflow(citation)
        
        return jsonify({
            "status": "success",
            "citation": citation,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error reprocessing citation: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add Flask after_request handler to log all JSON responses
def log_json_responses(response):
    """
    Flask after_request handler to log all JSON responses before they are sent to the frontend.
    This ensures we capture all JSON output regardless of which endpoint generates it.
    """
    try:
        # Only log JSON responses
        if response.content_type == 'application/json':
            # Get the response data
            response_data = response.get_data(as_text=True)
            
            # Try to parse and pretty-print the JSON for better logging
            try:
                import json
                parsed_data = json.loads(response_data)
                formatted_json = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                
                # Log the response with context
                logger.info("=" * 80)
                logger.info("JSON RESPONSE BEING SENT TO FRONTEND (CITATION API)")
                logger.info("=" * 80)
                logger.info(f"Endpoint: {request.endpoint}")
                logger.info(f"Method: {request.method}")
                logger.info(f"URL: {request.url}")
                logger.info(f"Status Code: {response.status_code}")
                logger.info(f"Content-Type: {response.content_type}")
                logger.info(f"Response Size: {len(response_data)} characters")
                logger.info("-" * 80)
                logger.info("RESPONSE BODY:")
                logger.info(formatted_json)
                logger.info("=" * 80)
                
            except json.JSONDecodeError:
                # If JSON parsing fails, log the raw response
                logger.warning("Failed to parse JSON response, logging raw data:")
                logger.info(f"Raw response: {response_data}")
                
        return response
        
    except Exception as e:
        logger.error(f"Error in log_json_responses: {str(e)}")
        return response

# Register the after_request handler to log all JSON responses
citation_api.after_request(log_json_responses)
