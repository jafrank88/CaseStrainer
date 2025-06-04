"""
Simplified CaseStrainer application with Enhanced Validator enabled
"""

import os
import sys
import json
import logging
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import required modules from src
from src.citation_api import USE_ENHANCED_VALIDATOR
from src.app_final_vue import (
    extract_citations_from_file,
    extract_citations_from_text,
    verify_citation,
)

# Create Flask application
app = Flask(__name__, static_folder="static/vue")

# Add URL prefix handling for Nginx
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)


# Load configuration
class Config:
    SECRET_KEY = "dev-key-for-casestrainer"
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload


app.config.from_object(Config)

# Try to load API key from config.json
try:
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config.json"
    )
    with open(config_path, "r") as f:
        config = json.load(f)
        COURTLISTENER_API_KEY = config.get("COURTLISTENER_API_KEY", "")
        logger.info(
            f"Loaded CourtListener API key from config.json: {COURTLISTENER_API_KEY[:5]}..."
        )
except (FileNotFoundError, json.JSONDecodeError) as e:
    logger.warning(f"Error loading config.json: {str(e)}. Using environment variables.")
    COURTLISTENER_API_KEY = os.environ.get("COURTLISTENER_API_KEY", "")

# Try to import and register the enhanced validator
try:
    from src.enhanced_validator_production import (
        register_enhanced_validator,
        enhanced_validator_bp,
    )

    app = register_enhanced_validator(app)
    # The blueprint is now registered inside register_enhanced_validator
    logger.info("Enhanced Validator registered successfully")
except ImportError as e:
    logger.warning(f"Could not import enhanced validator: {e}")
    logger.warning("The application will run with basic validation only.")
except Exception as e:
    logger.error(f"Error registering enhanced validator: {e}")
    logger.warning("The application will run with basic validation only.")


# API endpoints
@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    API endpoint to analyze citations from various sources:
    - File upload (multipart/form-data with 'file' field)
    - Text input (form data with 'text' or 'brief_text' field)
    """
    try:
        logger.info("Received analyze request")

        # Debug information
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content type: {request.content_type}")
        logger.info(f"Form data keys: {list(request.form.keys())}")
        logger.info(
            f"Files keys: {list(request.files.keys()) if request.files else 'No files'}"
        )

        # Check if Enhanced Validator is enabled
        logger.info(f"Enhanced Validator enabled: {USE_ENHANCED_VALIDATOR}")

        # Handle file upload
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            # Create a temporary file
            temp_dir = tempfile.mkdtemp()
            filename = secure_filename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)

            logger.info(f"Processing file: {filename}")

            # Extract and verify citations
            citations = extract_citations_from_file(filepath)
            verified_citations = [
                verify_citation(citation["citation"], citation.get("context", ""))
                for citation in citations
            ]

            # Format the response for the Vue frontend
            response_data = format_response_for_vue(verified_citations)

            # Clean up
            os.remove(filepath)
            os.rmdir(temp_dir)

            return jsonify(response_data)

        # Handle text input
        elif "text" in request.form or "brief_text" in request.form:
            text = request.form.get("text", "") or request.form.get("brief_text", "")
            logger.info(f"Processing text input (length: {len(text)})")

            # Extract and verify citations
            citations = extract_citations_from_text(text)
            verified_citations = [
                verify_citation(citation["citation"], citation.get("context", ""))
                for citation in citations
            ]

            # Format the response for the Vue frontend
            response_data = format_response_for_vue(verified_citations)

            return jsonify(response_data)

        else:
            logger.error("No valid input provided")
            return jsonify({"error": "No file or text provided"}), 400

    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


def format_response_for_vue(verified_citations):
    """
    Format the verified citations data for the Vue.js frontend
    """
    # Extract citation validation results
    validation_results = []
    citations_list = []

    for citation in verified_citations:
        # Create a validation result object for the detailed view
        result = {
            "citation": citation.get("citation", ""),
            "verified": citation.get("valid", False),
            "source": citation.get("source", "unknown"),
            "context": citation.get("context", ""),
            "verification_method": citation.get("verification_method", "unknown"),
            "case_name": citation.get("case_name", ""),
            "court": citation.get("court", ""),
            "year": citation.get("year", ""),
            "details": citation.get("details", {}),
        }

        # Create a citation object for the main list view
        citation_obj = {
            "citation": citation.get("citation", ""),
            "valid": citation.get("valid", False),
            "source": citation.get("source", "unknown"),
            "case_name": citation.get("case_name", ""),
            "context": citation.get("context", ""),
            "reporter": citation.get("reporter", ""),
            "court": citation.get("court", ""),
            "year": citation.get("year", ""),
        }

        validation_results.append(result)
        citations_list.append(citation_obj)

    # Create the response object
    response = {
        "citations_count": len(validation_results),
        "validation_results": validation_results,
        "citations": citations_list,
        "analysis_id": "vue-" + str(hash(str(validation_results)))[:8],
    }

    return response


# Serve Vue.js frontend
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_vue(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    # Use host='0.0.0.0' to allow external access
    app.run(host="0.0.0.0", port=5000, debug=False)
