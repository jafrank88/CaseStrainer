import os
import sys
import logging
import tempfile

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

# Import the functions from the correct location
from app_final_vue import (
    extract_citations_from_file,
    extract_citations_from_text,
    verify_citation,
)
from citation_api import USE_ENHANCED_VALIDATOR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
vue_api = Blueprint("vue_api", __name__)

# Try to import and register the enhanced validator
try:
    from enhanced_validator_production import register_enhanced_validator

    register_enhanced_validator()
    logger.info("Enhanced Validator registered successfully in Vue API")
except ImportError as e:
    logger.warning(f"Could not import enhanced validator: {e}")
    logger.warning("The application will run with basic validation only.")
except Exception as e:
    logger.error(f"Error registering enhanced validator: {e}")
    logger.warning("The application will run with basic validation only.")


@vue_api.route("/analyze", methods=["POST"])
def analyze():
    """
    API endpoint to analyze citations from various sources:
    - File upload (multipart/form-data with 'file' field)
    - Text input (form data with 'brief_text' field)
    - URL input (form data with 'url' field)
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
        elif "brief_text" in request.form:
            text = request.form["brief_text"]
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

        # Handle URL input
        elif "url" in request.form:
            url = request.form["url"]
            logger.info(f"Processing URL: {url}")

            # For now, we'll treat URLs as text input
            # In a future enhancement, we could fetch the content from the URL
            return jsonify({"error": "URL processing not implemented yet"}), 501

        else:
            logger.error("No valid input provided")
            return jsonify({"error": "No file, text, or URL provided"}), 400

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
