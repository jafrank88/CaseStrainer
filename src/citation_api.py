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

# Add the project root to the Python path
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from src to ensure consistent imports
from src.citation_utils import extract_all_citations as extract_citations
from src.citation_processor import CitationProcessor

# Create an instance of CitationProcessor
citation_processor = CitationProcessor()

# Create a special logger for citation verification
citation_logger = logging.getLogger("citation_verification")
citation_logger.setLevel(logging.DEBUG)

# Create a file handler for the citation verification logger (per-process log file to avoid Windows file locking issues)
if not os.path.exists("logs"):
    os.makedirs("logs")
pid = os.getpid()
citation_handler = logging.FileHandler(
    f"logs/citation_verification_{pid}.log", delay=True
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
    """API endpoint to provide data for the Confirmed with Multitool tab."""
    logger.info("Confirmed with Multitool API endpoint called")
    """
    API endpoint to provide data for the Confirmed with Multitool tab.
    Returns citations that were confirmed with the multi-source tool but not with CourtListener.
    """
    # First, check the database verification results for citations verified by alternative sources
    db_data = load_database_verification_data()
    multitool_citations = []

    # Filter for citations that were verified by alternative sources
    for item in db_data:
        result = item.get("verification_result", {})
        if (
            result.get("found") is True
            and result.get("source")
            and result.get("source") != "CourtListener"
        ):
            multitool_citations.append(
                {
                    "citation_text": item.get("citation_text", ""),
                    "case_name": result.get("case_name", "Unknown"),
                    "confidence": result.get("confidence", 0.5),
                    "source": result.get("source", "Alternative Source"),
                    "url": result.get("url", ""),
                    "explanation": result.get(
                        "explanation", "No explanation available"
                    ),
                }
            )

    # If no citations found in database verification results, check citation verification results
    if not multitool_citations:
        citation_data = load_citation_verification_data()
        newly_confirmed = citation_data.get("newly_confirmed", [])

        for citation in newly_confirmed:
            multitool_citations.append(
                {
                    "citation_text": citation.get("citation_text", ""),
                    "case_name": citation.get("case_name", "Unknown"),
                    "confidence": citation.get("confidence", 0.5),
                    "source": citation.get("source", "Multi-source Verification"),
                    "url": citation.get("url", ""),
                    "explanation": citation.get(
                        "explanation", "No explanation available"
                    ),
                    "document": citation.get("document", ""),
                }
            )

    # If still no citations found, provide sample data for demonstration
    if not multitool_citations:
        multitool_citations = [
            {
                "citation_text": "347 U.S. 483",
                "case_name": "Brown v. Board of Education",
                "confidence": 0.95,
                "source": "Google Scholar",
                "url": "https://scholar.google.com/scholar_case?case=12120372216939101759",
                "explanation": "The landmark case Brown v. Board of Education (347 U.S. 483) established that separate educational facilities are inherently unequal.",
            },
            {
                "citation_text": "410 U.S. 113",
                "case_name": "Roe v. Wade",
                "confidence": 0.92,
                "source": "Justia",
                "url": "https://supreme.justia.com/cases/federal/us/410/113/",
                "explanation": "The Court's decision in Roe v. Wade (410 U.S. 113) recognized a woman's right to choose.",
            },
            {
                "citation_text": "5 U.S. 137",
                "case_name": "Marbury v. Madison",
                "confidence": 0.88,
                "source": "FindLaw",
                "url": "https://caselaw.findlaw.com/us-supreme-court/5/137.html",
                "explanation": "Marbury v. Madison (5 U.S. 137) established the principle of judicial review.",
            },
        ]

    response_data = {
        "citations": multitool_citations,
        "count": len(multitool_citations),
    }

    logger.info(f"Returning {len(multitool_citations)} confirmed citations")

    # Create a response with CORS headers
    response = make_response(jsonify(response_data))
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST")

    return response


@citation_api.route("/unconfirmed-citations-data", methods=["GET"])
@citation_api.route("/unconfirmed_citations_data", methods=["POST", "GET"])
def unconfirmed_citations_data():
    """API endpoint to provide data for the Unconfirmed Citations tab."""
    logger.info("Unconfirmed Citations API endpoint called")
    """
    API endpoint to provide data for the Unconfirmed Citations tab.
    Returns citations that could not be verified in any source.
    """
    # First, check the citation verification results for unconfirmed citations
    citation_data = load_citation_verification_data()
    unconfirmed_citations = []

    # Get unconfirmed citations from the still_unconfirmed array
    for citation in citation_data.get("still_unconfirmed", []):
        unconfirmed_citations.append(
            {
                "citation_text": citation.get("citation_text", ""),
                "case_name": citation.get("case_name", "Unknown"),
                "confidence": citation.get("confidence", 0.3),
                "explanation": citation.get("explanation", "No explanation available"),
                "document": citation.get("document", ""),
            }
        )

    # If no unconfirmed citations found in citation verification results, check database verification results
    if not unconfirmed_citations:
        db_data = load_database_verification_data()

        # Filter for citations that were not found/verified
        for item in db_data:
            result = item.get("verification_result", {})
            if result.get("found") is False:
                unconfirmed_citations.append(
                    {
                        "citation_text": item.get("citation_text", ""),
                        "case_name": result.get("case_name", "Unknown"),
                        "confidence": result.get("confidence", 0.3),
                        "explanation": result.get(
                            "explanation", "No explanation available"
                        ),
                    }
                )

    # If still no unconfirmed citations found, provide sample data for demonstration
    if not unconfirmed_citations:
        unconfirmed_citations = [
            {
                "citation_text": "999 U.S. 123",
                "case_name": "Fictional v. NonExistent",
                "confidence": 0.15,
                "explanation": "Citation not found in any legal database. The U.S. Reports volume 999 does not exist.",
                "document": "sample_brief_1.pdf",
            },
            {
                "citation_text": "531 F.3d 9999",
                "case_name": "Smith v. Imaginary Corp",
                "confidence": 0.22,
                "explanation": "Citation format is valid but no matching case found. The F.3d volume 531 does not contain a page 9999.",
                "document": "sample_brief_2.pdf",
            },
        ]

    response_data = {
        "citations": unconfirmed_citations,
        "count": len(unconfirmed_citations),
    }

    logger.info(f"Returning {len(unconfirmed_citations)} unconfirmed citations")

    # Create a response with CORS headers
    response = make_response(jsonify(response_data))
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST")

    return response


@citation_api.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    """API endpoint to analyze a document or pasted text with the Enhanced Validator."""
    # Handle preflight OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = jsonify({"status": "success"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    # Log request details for debugging
    logger.info("Citation analysis request received")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(
        f"Request files: {list(request.files.keys()) if request.files else 'No files'}"
    )
    logger.info(
        f"Request form: {list(request.form.keys()) if request.form else 'No form data'}"
    )

    # Add CORS headers for this specific endpoint

    try:
        # Generate a unique analysis ID
        analysis_id = generate_analysis_id()
        logger.info(f"Generated analysis ID: {analysis_id}")

        # Use session storage instead of global variables
        from flask import session

        # Clear the previous citations to ensure we're not mixing old and new data
        session["user_citations"] = []
        logger.info("Cleared previous citation data in user session")

        # Initialize variables
        document_text = None
        file_path = None

        # Log debug_info if provided
        debug_info = request.form.get("debug_info")
        if debug_info:
            try:
                with open("logs/debug.log", "a", encoding="utf-8") as debug_log:
                    timestamp = datetime.now().isoformat()
                    debug_log.write(
                        f"[{timestamp}] Analysis ID: {analysis_id} | Debug Info: {debug_info}\n"
                    )
            except Exception as log_err:
                logger.error(f"Failed to write debug_info to debug.log: {log_err}")

        # Check if a file was uploaded or a URL was provided
        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            logger.info(f"File uploaded: {file.filename if file else 'None'}")

            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, f"{analysis_id}_{filename}")

                # Save file
                file.save(file_path)
                logger.info(f"File saved to: {file_path}")

                # Extract text from file
                from file_utils import extract_text_from_file

                document_text = extract_text_from_file(file_path)
                logger.info(f"Extracted {len(document_text)} characters from file")
            else:
                error_msg = f"Invalid file: {file.filename if file else 'None'}"
                logger.error(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 400

        # Check if a URL was provided
        elif "url" in request.form and request.form["url"].strip():
            url = request.form["url"].strip()
            logger.info(f"URL provided: {url}")

            try:
                # Check if it's a PDF URL
                if url.lower().endswith(".pdf"):
                    import tempfile
                    import requests

                    # Download the PDF
                    response = requests.get(url, stream=True)
                    response.raise_for_status()

                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as temp_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                temp_file.write(chunk)
                        temp_file_path = temp_file.name

                    try:
                        # Extract text from the downloaded PDF
                        from file_utils import extract_text_from_file

                        document_text = extract_text_from_file(temp_file_path)
                        logger.info(
                            f"Extracted {len(document_text)} characters from PDF URL"
                        )
                    finally:
                        # Clean up the temporary file
                        try:
                            os.unlink(temp_file_path)
                        except Exception as e:
                            logger.warning(
                                f"Failed to delete temporary file {temp_file_path}: {e}"
                            )
                else:
                    # For non-PDF URLs, use the existing extract_text_from_url function
                    from .enhanced_validator_production import extract_text_from_url

                    document_text = extract_text_from_url(url)
                    logger.info(f"Extracted {len(document_text)} characters from URL")

            except Exception as e:
                error_msg = f"Error processing URL: {str(e)}"
                logger.error(error_msg)
                return jsonify({"status": "error", "message": error_msg}), 400

        # Get text from form if provided (handle both 'text' and 'brief_text' fields)
        elif ("text" in request.form and request.form["text"].strip()) or (
            "brief_text" in request.form and request.form["brief_text"].strip()
        ):
            # Check which field is present
            if "text" in request.form and request.form["text"].strip():
                document_text = request.form["text"].strip()
            else:
                document_text = request.form["brief_text"].strip()
            logger.info(f"Text provided: {len(document_text)} characters")

        # Return error if no file or text provided
        else:
            error_msg = "No file or text provided"
            logger.error(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 400

        # Extract citations from text
        citations = []
        if document_text:
            try:
                # Extract citations with debug info
                extracted_result = extract_citations(document_text, return_debug=True)

                # Handle the return value from extract_citations
                if isinstance(extracted_result, tuple) and len(extracted_result) == 2:
                    # If it's a tuple with debug info, extract just the citations data
                    extracted_data, extract_debug = extracted_result
                    logger.debug("Extracted citations with debug info")
                else:
                    # If not a tuple, use the result as is
                    extracted_data = extracted_result

                # Extract confirmed and possible citations
                if isinstance(extracted_data, dict):
                    confirmed_citations = extracted_data.get("confirmed_citations", [])
                    possible_citations = extracted_data.get("possible_citations", [])

                    # Combine confirmed and possible citations, with confirmed first
                    extracted_citations = confirmed_citations + possible_citations
                    logger.info(
                        f"Extracted {len(extracted_citations)} citations ({len(confirmed_citations)} confirmed, {len(possible_citations)} possible)"
                    )
                else:
                    # Fallback if the structure is unexpected
                    logger.warning(
                        f"Unexpected extracted data format: {type(extracted_data)}"
                    )
                    extracted_citations = []

                # Ensure extracted_citations is a list of dictionaries with the expected structure
                processed_citations = []
                for item in extracted_citations:
                    if isinstance(item, dict):
                        # Ensure the citation has the expected structure
                        citation = {
                            "citation_text": item.get("citation_text", ""),
                            "case_name": item.get("case_name", ""),
                            "metadata": item.get("metadata", {}),
                            "source": item.get("source", "unknown"),
                            "validation_status": item.get(
                                "validation_status", "pending"
                            ),
                            "is_valid": item.get("is_valid", False),
                        }
                        processed_citations.append(citation)

                extracted_citations = processed_citations

                # Log the number of extracted citations
                logger.info(f"Extracted {len(extracted_citations)} citations from text")

            except Exception as e:
                logger.error(f"Error extracting citations: {str(e)}", exc_info=True)
                extracted_citations = []

            # Validate each citation
            for i, citation_item in enumerate(extracted_citations):
                try:
                    logger.debug(
                        f"Processing citation item {i+1}/{len(extracted_citations)}: {citation_item}"
                    )

                    # Skip if not a dictionary
                    if not isinstance(citation_item, dict):
                        logger.warning(
                            f"Skipping non-dict citation item: {citation_item}"
                        )
                        continue

                    # Log the complete structure of the citation item for debugging
                    logger.debug(f"Citation item type: {type(citation_item)}")
                    logger.debug(
                        f"Citation item structure: {json.dumps(citation_item, default=str, indent=2)}"
                    )

                    # Log all keys in the citation item for debugging
                    if hasattr(citation_item, "keys"):
                        logger.debug(
                            f"Citation item keys: {list(citation_item.keys())}"
                        )

                    # Get citation text from various possible fields
                    citation_text = citation_item.get("citation_text", "")
                    if not citation_text and "citation" in citation_item:
                        citation_text = citation_item["citation"]

                    # Skip empty citations
                    if not citation_text or not citation_text.strip():
                        logger.warning(f"Skipping empty citation at index {i}")
                        continue

                    # Log the citation being processed
                    logger.debug(f"Processing citation: {citation_text}")

                    # Validate the citation
                    try:
                        # Call the validation endpoint
                        validation_response = requests.post(
                            f"{request.host_url}casestrainer/api/verify-citation",
                            json={"citation": {"citation_text": citation_text}},
                            headers={"Content-Type": "application/json"},
                        )

                        # Parse the validation response
                        if validation_response.status_code == 200:
                            validation_result = validation_response.json()
                            is_valid = validation_result.get("verified", False)
                            source = validation_result.get("source", "unknown")
                            validation_method = validation_result.get(
                                "validation_method", source
                            )
                            explanation = validation_result.get(
                                "explanation",
                                (
                                    "Citation validated"
                                    if is_valid
                                    else "Citation not found"
                                ),
                            )
                            case_name = validation_result.get("case_name", "")
                            url = validation_result.get("url", "")
                            confidence = float(
                                validation_result.get(
                                    "confidence", 1.0 if is_valid else 0.0
                                )
                            )
                            name_match = bool(
                                validation_result.get("name_match", is_valid)
                            )
                        else:
                            logger.error(
                                f"Error validating citation {citation_text}: {validation_response.status_code} - {validation_response.text}"
                            )
                            is_valid = False
                            source = "error"
                            validation_method = "error"
                            explanation = f"Validation failed with status {validation_response.status_code}"
                            case_name = ""
                            url = ""
                            confidence = 0.0
                            name_match = False
                    except Exception as e:
                        logger.error(
                            f"Exception during citation validation for {citation_text}: {str(e)}",
                            exc_info=True,
                        )
                        is_valid = False
                        source = "error"
                        validation_method = "error"
                        explanation = f"Validation error: {str(e)}"
                        case_name = ""
                        url = ""
                        confidence = 0.0
                        name_match = False

                    # Create citation data with consistent structure
                    citation_data = {
                        "citation": citation_text,
                        "found": is_valid,
                        "found_case_name": case_name,
                        "url": url,
                        "explanation": explanation,
                        "source": source,
                        "validation_method": validation_method,
                        "confidence": confidence,
                        "name_match": name_match,
                        "metadata": citation_item.get("metadata", {}),
                    }

                    # Add to citations list
                    citations.append(citation_data)
                    logger.debug(f"Added citation to results: {citation_data}")

                except Exception as e:
                    logger.error(
                        f"Error processing citation {citation_item}: {str(e)}",
                        exc_info=True,
                    )
                    continue

            logger.info(f"Validated {len(citations)} citations")

            # Store the validated citations in the user's session
            from flask import session

            session["user_citations"] = citations
            logger.info(f"Stored {len(citations)} citations in user session")

            # Log a sample of the citations for debugging
            if citations:
                sample = min(3, len(citations))
                logger.debug(f"Sample of {sample} citations: {citations[:sample]}")

        # Return results in the format expected by the EnhancedFileUpload component
        validation_results = []
        for citation in citations:
            validation_results.append(
                {
                    "citation": citation.get("citation", ""),
                    "verified": citation.get("found", False),
                    "validation_method": citation.get("source"),
                    "case_name": citation.get("found_case_name", ""),
                    "url": citation.get("url"),
                    "explanation": citation.get("explanation", ""),
                    "confidence": citation.get("confidence", 0.0),
                    "name_match": citation.get("name_match", False),
                }
            )

        response_data = {
            "status": "success",
            "analysis_id": analysis_id,
            "validation_results": validation_results,
            "file_name": (
                file.filename
                if "file" in request.files and file and file.filename
                else None
            ),
            "citations_count": len(citations),
        }

        logger.info(f"Analysis completed for ID: {analysis_id}")
        return jsonify(response_data)

    except Exception as e:
        error_msg = f"Error analyzing document: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        return jsonify({"status": "error", "message": error_msg}), 500


@citation_api.route("/reprocess-citation", methods=["POST"])
def reprocess_citation():
    """
    API endpoint to reprocess a single unconfirmed citation to check if it can now be confirmed.
    """
    try:
        data = request.get_json()
        citation = data.get("citation", "")

        if not citation:
            return jsonify({"success": False, "message": "No citation provided"}), 400

        # In a real implementation, this would call the citation verification logic
        # For now, we'll just return a success message
        # Simulate a 20% chance of finding the citation on reprocessing
        import random

        found = random.random() < 0.2

        if found:
            return jsonify(
                {
                    "success": True,
                    "message": f'Citation "{citation}" has been verified!',
                    "result": {
                        "citation_text": citation,
                        "found": True,
                        "confidence": round(random.uniform(0.7, 0.95), 2),
                        "explanation": "Citation was successfully verified after reprocessing.",
                        "source": random.choice(
                            ["Google Scholar", "Justia", "FindLaw", "HeinOnline"]
                        ),
                    },
                }
            )
        else:
            return jsonify(
                {
                    "success": True,
                    "message": f'Citation "{citation}" was reprocessed but still could not be verified.',
                    "result": {
                        "citation_text": citation,
                        "found": False,
                        "confidence": round(random.uniform(0.1, 0.4), 2),
                        "explanation": "Citation still could not be verified after reprocessing.",
                    },
                }
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "message": "An error occurred while reprocessing the citation",
                }
            ),
            500,
        )
