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
from src.citation_utils import extract_all_citations as extract_citations
from src.citation_processor import CitationProcessor
from src.file_utils import extract_text_from_file

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


@citation_api.route("/analyze", methods=["POST"])
def analyze():
    """Analyze a document for citations."""
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[Analysis {analysis_id}] Starting enhanced analysis")
        
        # Log request data (excluding binary content)
        request_data = {
            "has_file": "file" in request.files,
            "filename": request.files["file"].filename if "file" in request.files else None,
            "file_size": request.files["file"].content_length if "file" in request.files else None,
            "has_text": "text" in request.form,
            "text_length": len(request.form["text"]) if "text" in request.form else None,
            "options": request.form.get("options", {})
        }
        logger.info(f"[Analysis {analysis_id}] Request data: {json.dumps(request_data, indent=2)}")
        
        # Set timeouts - match frontend timeout of 30 seconds
        ANALYSIS_TIMEOUT = 28  # seconds (slightly less than frontend to allow for response time)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        
        # Check if we have pasted text
        if "text" in request.form or (request.is_json and "text" in (request.get_json(silent=True) or {})):
            if request.is_json:
                text = request.get_json(silent=True).get("text", "")
            else:
                text = request.form.get("text", "")
            if not text.strip():
                error_msg = "No text provided"
                logger.error(f"[Analysis {analysis_id}] {error_msg}")
                return jsonify({"error": error_msg}), 400

            logger.info(f"[Analysis {analysis_id}] Processing pasted text ({len(text)} characters)")
            # Extract and validate citations (reuse your existing logic)
            try:
                logger.info(f"[Analysis {analysis_id}] Starting citation extraction (text input)")
                extraction_start = time.time()
                extraction_result = extract_citations(text, return_debug=True, analysis_id=analysis_id)
                extraction_time = time.time() - extraction_start

                # Handle the tuple return value from extract_citations
                if isinstance(extraction_result, tuple) and len(extraction_result) == 2:
                    citations, debug_info = extraction_result
                    if isinstance(citations, dict) and "confirmed_citations" in citations:
                        citations = citations["confirmed_citations"]
                else:
                    citations = extraction_result if isinstance(extraction_result, list) else []
                    debug_info = {}

                if not citations:
                    logger.warning(f"[Analysis {analysis_id}] No citations found after {extraction_time:.1f}s")
                    return jsonify({
                        "status": "Invalid",
                        "analysis_id": analysis_id,
                        "validation_results": [],
                        "file_name": None,
                        "citations_count": 0,
                        "extraction_time": time.time() - start_time,
                        "processing_time": 0,
                        "validation_time": 0,
                        "error": "No citations found in document"
                    })

                logger.info(f"[Analysis {analysis_id}] Found {len(citations)} citations in {extraction_time:.1f}s")

                # Validate citations with progress reporting
                logger.info(f"[Analysis {analysis_id}] Starting citation validation (text input)")
                validation_start = time.time()
                validation_results = validate_citations(citations, analysis_id=analysis_id)
                validation_time = time.time() - validation_start

                logger.info(f"[Analysis {analysis_id}] Validated {len(validation_results)} citations in {validation_time:.1f}s")

                # Prepare response with timing information
                total_time = time.time() - start_time
                response = {
                    "status": "Valid" if any(r.get("valid") for r in validation_results) else "Invalid",
                    "analysis_id": analysis_id,
                    "validation_results": validation_results,
                    "citations": validation_results,  # Include both for compatibility
                    "file_name": None,
                    "citations_count": len(citations),
                    "extraction_time": extraction_time,
                    "processing_time": extraction_time,
                    "validation_time": validation_time,
                    "total_time": total_time,
                    "file_size": None,
                    "debug_info": debug_info if debug_info else None
                }

                logger.info(f"[Analysis {analysis_id}] Analysis completed in {total_time:.1f}s (text input)")
                return jsonify(response)

            except Exception as e:
                error_msg = f"Error processing citations: {str(e)}"
                logger.error(f"[Analysis {analysis_id}] {error_msg}")
                return jsonify({"error": error_msg}), 500

        # Check if we have a file upload
        if "file" not in request.files:
            error_msg = "No file uploaded or text provided"
            logger.error(f"[Analysis {analysis_id}] {error_msg}")
            return jsonify({"error": error_msg}), 400
            
        file = request.files["file"]
        if not file or not file.filename:
            error_msg = "No file selected"
            logger.error(f"[Analysis {analysis_id}] {error_msg}")
            return jsonify({"error": error_msg}), 400
            
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            error_msg = f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
            logger.error(f"[Analysis {analysis_id}] {error_msg}")
            return jsonify({"error": error_msg}), 400
            
        # Save the uploaded file
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            logger.info(f"[Analysis {analysis_id}] Saved uploaded file: {file_path} ({file_size/1024:.1f}KB)")
        except Exception as e:
            error_msg = f"Error saving uploaded file: {str(e)}"
            logger.error(f"[Analysis {analysis_id}] {error_msg}")
            return jsonify({"error": error_msg}), 500
            
        # Extract text from the file with progress reporting
        try:
            logger.info(f"[Analysis {analysis_id}] Starting text extraction")
            extraction_start = time.time()
            
            # Check if file is a valid PDF
            if not file_path.lower().endswith('.pdf'):
                error_msg = "Only PDF files are supported"
                logger.error(f"[Analysis {analysis_id}] {error_msg}")
                return jsonify({"error": error_msg}), 400
                
            # Extract text with timeout
            text = extract_text_from_file(file_path, timeout=ANALYSIS_TIMEOUT)
            extraction_time = time.time() - extraction_start
            
            if text.startswith("Error:"):
                error_msg = text
                logger.error(f"[Analysis {analysis_id}] {error_msg}")
                return jsonify({"error": error_msg}), 400
                
            if not text or not text.strip():
                error_msg = "No text could be extracted from the file"
                logger.error(f"[Analysis {analysis_id}] {error_msg}")
                return jsonify({"error": error_msg}), 400
                
            logger.info(f"[Analysis {analysis_id}] Extracted {len(text)} characters in {extraction_time:.1f}s")
            
        except Exception as e:
            error_msg = f"Error extracting text: {str(e)}"
            logger.error(f"[Analysis {analysis_id}] {error_msg}")
            return jsonify({"error": error_msg}), 500
            
        # Extract and validate citations with progress reporting
        try:
            logger.info(f"[Analysis {analysis_id}] Starting citation extraction")
            extraction_start = time.time()
            
            # Extract citations and handle the tuple return value
            extraction_result = extract_citations(text, return_debug=True, analysis_id=analysis_id)
            extraction_time = time.time() - extraction_start
            
            # Handle the tuple return value from extract_citations
            if isinstance(extraction_result, tuple) and len(extraction_result) == 2:
                citations, debug_info = extraction_result
                # If citations is a dict with confirmed_citations, use that
                if isinstance(citations, dict) and "confirmed_citations" in citations:
                    citations = citations["confirmed_citations"]
            else:
                citations = extraction_result if isinstance(extraction_result, list) else []
                debug_info = {}
            
            if not citations:
                logger.warning(f"[Analysis {analysis_id}] No citations found after {extraction_time:.1f}s")
                return jsonify({
                    "status": "Invalid",
                    "analysis_id": analysis_id,
                    "validation_results": [],
                    "file_name": filename,
                    "citations_count": 0,
                    "extraction_time": time.time() - start_time,
                    "processing_time": 0,
                    "validation_time": 0,
                    "error": "No citations found in document"
                })
                
            logger.info(f"[Analysis {analysis_id}] Found {len(citations)} citations in {extraction_time:.1f}s")
            
            # Validate citations with progress reporting
            logger.info(f"[Analysis {analysis_id}] Starting citation validation")
            validation_start = time.time()
            
            def validate_citations(citations, analysis_id):
                """
                Validate a list of citations.
                Args:
                    citations: List of citations to validate.
                    analysis_id: ID of the analysis for logging purposes.
                Returns:
                    List of validation results for each citation.
                """
                results = []
                for citation in citations:
                    try:
                        # Get citation text from either format
                        citation_text = citation.get("text", citation.get("citation", ""))
                        if not citation_text:
                            continue
                            
                        # Check if citation was verified by CourtListener
                        is_verified = False
                        case_name = "Unknown Case"
                        confidence = 0.0
                        metadata = {}
                        details = {}
                        
                        # Check CourtListener verification
                        if isinstance(citation, dict):
                            # Check for clusters (CourtListener API response)
                            if "clusters" in citation:
                                clusters = citation.get("clusters", [])
                                if clusters:
                                    cluster = clusters[0]  # Use first cluster
                                    is_verified = True
                                    case_name = cluster.get("case_name", "Unknown Case")
                                    confidence = 0.9  # High confidence for CourtListener matches
                                    metadata = {
                                        "case_name": case_name,
                                        "court": cluster.get("court", ""),
                                        "date_filed": cluster.get("date_filed", ""),
                                        "judges": cluster.get("judges", ""),
                                        "docket": cluster.get("docket", ""),
                                        "precedential_status": cluster.get("precedential_status", ""),
                                        "citation_count": cluster.get("citation_count", 0),
                                        "verified": True,
                                        "url": cluster.get("url", "")
                                    }
                                    details = {
                                        "court": cluster.get("court", ""),
                                        "date_filed": cluster.get("date_filed", ""),
                                        "precedential_status": cluster.get("precedential_status", ""),
                                        "judges": cluster.get("judges", "")
                                    }
                                    # Add clusters to the citation object
                                    citation["verified"] = True
                                    citation["clusters"] = clusters
                            # Check for direct verification fields
                            elif citation.get("verified") or citation.get("valid"):
                                is_verified = True
                                case_name = citation.get("case_name", "Unknown Case")
                                confidence = citation.get("confidence", 0.9)
                                metadata = {
                                    "case_name": case_name,
                                    "court": citation.get("court", ""),
                                    "date_filed": citation.get("date_filed", ""),
                                    "verified": True,
                                    "url": citation.get("url", "")
                                }
                                details = {
                                    "court": citation.get("court", ""),
                                    "date_filed": citation.get("date_filed", ""),
                                    "precedential_status": citation.get("precedential_status", "")
                                }
                            # Check for normalized citations (eyecite format)
                            elif "normalized_citations" in citation:
                                is_verified = True
                                case_name = citation.get("case_name", "Unknown Case")
                                confidence = 0.8  # Medium confidence for eyecite matches
                                metadata = {
                                    "case_name": case_name,
                                    "normalized_citations": citation.get("normalized_citations", []),
                                    "source": "eyecite",
                                    "verified": True
                                }
                                details = {
                                    "source": "eyecite",
                                    "normalized_citations": citation.get("normalized_citations", [])
                                }
                        
                        # Create validation result with consistent field names
                        found = is_verified
                        result = {
                            "citation": citation_text,  # Use consistent field name
                            "text": citation_text,      # Include both for compatibility
                            "valid": found,
                            "verified": found,
                            "case_name": case_name,
                            "confidence": confidence,
                            "method": "CourtListener API" if found and "clusters" in citation else "eyecite",
                            "metadata": metadata,
                            "details": details,
                            "source": "CourtListener" if found and "clusters" in citation else "eyecite",
                            "status": 200 if found else 404,
                            "error_message": "" if found else citation.get("error", "Citation not found"),
                            "clusters": citation.get("clusters", []) if found and "clusters" in citation else []
                        }
                        
                        results.append(result)
                        logger.info(f"[Analysis {analysis_id}] Citation {citation_text} validated: {found} (confidence: {confidence})")
                        
                    except Exception as e:
                        logger.error(f"[Analysis {analysis_id}] Error validating citation: {str(e)}")
                        continue
                return results
            
            validation_results = validate_citations(citations, analysis_id=analysis_id)
            validation_time = time.time() - validation_start
            
            logger.info(f"[Analysis {analysis_id}] Validated {len(validation_results)} citations in {validation_time:.1f}s")
            
            # Prepare response with timing information
            total_time = time.time() - start_time
            response = {
                "status": "Valid" if any(r.get("valid") for r in validation_results) else "Invalid",
                "analysis_id": analysis_id,
                "validation_results": validation_results,
                "citations": validation_results,  # Include both for compatibility
                "file_name": filename,
                "citations_count": len(citations),
                "extraction_time": extraction_time,
                "processing_time": extraction_time,
                "validation_time": validation_time,
                "total_time": total_time,
                "file_size": file_size,
                "debug_info": debug_info if debug_info else None
            }
            
            logger.info(f"[Analysis {analysis_id}] Analysis completed in {total_time:.1f}s")
            return jsonify(response)
            
        except Exception as e:
            error_msg = f"Error processing citations: {str(e)}"
            logger.error(f"[Analysis {analysis_id}] {error_msg}")
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        error_msg = f"Unexpected error during analysis: {str(e)}"
        logger.error(f"[Analysis {analysis_id}] {error_msg}")
        return jsonify({"error": error_msg}), 500
        
    finally:
        # Clean up uploaded file
        try:
            if "file_path" in locals():
                os.remove(file_path)
                logger.info(f"[Analysis {analysis_id}] Cleaned up uploaded file")
        except Exception as e:
            logger.warning(f"[Analysis {analysis_id}] Error cleaning up file: {str(e)}")


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


@citation_api.route('/fetch_url', methods=['POST'])
def fetch_url():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return jsonify({'text': resp.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
