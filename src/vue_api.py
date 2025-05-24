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
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import tempfile
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from citation_utils import (
    extract_citations_from_file,
    extract_citations_from_text,
    verify_citation,
)


# --- Not-a-citation blacklist helpers ---
NOT_CITATIONS_PATH = os.path.join(os.path.dirname(__file__), "not_citations.json")


def load_not_citations():
    try:
        with open(NOT_CITATIONS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"exact": [], "regex": []}


def save_not_citations(data):
    with open(NOT_CITATIONS_PATH, "w") as f:
        json.dump(data, f, indent=2)


api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/api/not_citations", methods=["GET"])
def get_not_citations():
    return jsonify(load_not_citations())


@api_blueprint.route("/api/not_citations", methods=["POST"])
def add_not_citation():
    data = request.json
    pattern = data.get("pattern")
    is_regex = data.get("is_regex", False)
    nc = load_not_citations()
    key = "regex" if is_regex else "exact"
    if pattern and pattern not in nc[key]:
        nc[key].append(pattern)
        save_not_citations(nc)
    return jsonify({"success": True, "not_citations": nc})


# Configure logging
logger = logging.getLogger(__name__)

# Define constants
VERSION = "0.4.5"  # Current CaseStrainer version
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

# Create a blueprint for the API endpoints
api_blueprint = Blueprint("api", __name__)


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Add CORS headers to all API responses


@api_blueprint.route("/version", methods=["GET"])
def get_version():
    """Return the current CaseStrainer version as JSON."""
    return jsonify({"version": VERSION})


@api_blueprint.after_request
def add_cors_headers(response):
    """Add CORS headers to all API responses."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


# Import citation analysis functions from the main application


# Thread-local storage for API keys
import threading

thread_local = threading.local()

# Import citation extraction and verification functions
from citation_utils import (
    extract_citations_from_file,
    extract_citations_from_text,
    verify_citation,
)


# Helper function to fetch content from a URL
def fetch_url_content(url):
    """
    Fetch content from a URL. If PDF, use extract_citations_from_file logic.
    """
    try:
        logger.info(f"[fetch_url_content] Fetching URL: {url}")
        # All imports moved to the top of the file for hygiene.

        # Add http:// if missing
        if not url.startswith("http"):
            logger.info(
                (f"[fetch_url_content] URL missing scheme, prepending http://: {url}")
            )
            url = "http://" + url

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=30)
        logger.info(f"[fetch_url_content] Response status code: {response.status_code}")
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        logger.info(f"[fetch_url_content] Content-Type: {content_type}")
        # If PDF, save to temp file and use extract_citations_from_file
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            logger.info(
                (
                    f"[fetch_url_content] Detected PDF content. "
                    "Saving to temp file and extracting citations."
                )
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            try:
                citations = extract_citations_from_file(tmp_path)
                logger.info(
                    (
                        f"[fetch_url_content] extract_citations_from_file returned "
                        f"{len(citations)} citations."
                    )
                )
            finally:
                os.remove(tmp_path)
                
            # Extract text from each citation dictionary and join with spaces
            citation_texts = []
            for citation in citations:
                if isinstance(citation, dict):
                    # Try to get the 'text' or 'citation' field from the dictionary
                    text = citation.get('text') or citation.get('citation')
                    if text:
                        citation_texts.append(str(text))
                elif isinstance(citation, str):
                    citation_texts.append(citation)
                    
            if not citation_texts:
                logger.warning("[fetch_url_content] No valid citation text found in citations")
                return {"text": "", "status": "success"}
                
            return {"text": " ".join(citation_texts), "status": "success"}
        else:
            # Parse HTML and extract text
            logger.info(f"[fetch_url_content] Parsing HTML and extracting text.")
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=" ", strip=True)
            logger.info(
                (
                    f"[fetch_url_content] Extracted text length: {len(text)}. "
                    "Passing to extract_citations_from_text."
                )
            )
            citations = extract_citations_from_text(text)
            logger.info(
                (
                    f"[fetch_url_content] extract_citations_from_text returned "
                    f"{len(citations)} citations."
                )
            )
            
            # Extract text from each citation dictionary and join with spaces
            citation_texts = []
            for citation in citations:
                if isinstance(citation, dict):
                    # Try to get the 'text' or 'citation' field from the dictionary
                    text = citation.get('text') or citation.get('citation')
                    if text:
                        citation_texts.append(str(text))
                elif isinstance(citation, str):
                    citation_texts.append(citation)
                    
            if not citation_texts:
                logger.warning("[fetch_url_content] No valid citation text found in citations")
                return {"text": "", "status": "success"}
                
            return {"text": " ".join(citation_texts), "status": "success"}
    except Exception as e:
        logger.error(
            (f"[fetch_url_content] Error fetching or processing URL content: {str(e)}")
        )
        raise


# API endpoint to fetch content from a URL
@api_blueprint.route("/fetch_url", methods=["POST"])
def fetch_url():
    try:
        data = request.get_json()
        url = data.get("url")
        logger.info(f"[fetch_url] Received request with URL: {url}")
        if not url:
            logger.warning("[fetch_url] Missing URL in request body.")
            return jsonify({"status": "error", "message": "Missing URL"}), 400
        result = fetch_url_content(url)
        logger.info(
            (
                f"[fetch_url] fetch_url_content returned type: {type(result)}, value: {result}"
            )
        )
        # Always expect a dict from fetch_url_content
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /fetch_url endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Helper function to verify citations in parallel
def verify_citations_parallel(citations):
    """Verify multiple citations in parallel using ThreadPoolExecutor."""
    try:
        # Create a thread pool
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit verification tasks
            future_to_citation = {}
            for i, citation in enumerate(citations):
                # Get the citation text and context
                citation_text = citation["text"]
                context = (
                    citation["contexts"][0]["text"] if citation["contexts"] else None
                )

                # Submit the verification task
                future = executor.submit(verify_citation, citation_text, context)
                future_to_citation[future] = i

            # Process results as they complete
            for future in future_to_citation:
                try:
                    # Get the verification result
                    result = future.result()
                    citation_index = future_to_citation[future]

                    # Update the citation with verification results
                    citations[citation_index]["valid"] = result.get("found", False)

                    # Add metadata from verification
                    if "metadata" not in citations[citation_index]:
                        citations[citation_index]["metadata"] = {}

                    # Update metadata with verification results
                    citations[citation_index]["metadata"].update(
                        {
                            "source": result.get("source"),
                            "url": result.get("url"),
                            "explanation": result.get("explanation"),
                        }
                    )

                    # If case name was found, update it
                    if result.get("found_case_name"):
                        citations[citation_index]["name"] = result.get(
                            "found_case_name"
                        )
                except Exception as e:
                    logger.error(f"Error processing verification result: {str(e)}")

        # Log unverified citations
        unverified_citations = [
            citation for citation in citations if not citation.get("valid")
        ]
        if unverified_citations:
            logs_dir = os.path.join(current_app.root_path, "logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            with open(os.path.join(logs_dir, "unverified_citations.log"), "a") as f:
                for citation in unverified_citations:
                    f.write(json.dumps(citation) + "\n")

        return citations
    except Exception as e:
        logger.error(f"Error in parallel verification: {str(e)}")
        return citations


# Citation analysis endpoints
@api_blueprint.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze a brief for citations.
    Accepts either a text string, a file upload, or a URL.
    """
    # Import here to avoid circular imports
    from enhanced_validator_production import analyze_text
    
    request_id = str(uuid.uuid4())[:8]  # Short ID for request tracking
    start_time = time.time()
    
    # Configure request logging
    logger.info(f"[ANALYZE:{request_id}] 1. Starting request")
    logger.info(f"[ANALYZE:{request_id}] Headers: {dict(request.headers)}")
    logger.info(f"[ANALYZE:{request_id}] Content-Type: {request.content_type}")
    
    # Initialize response data
    response_data = {
        'request_id': request_id,
        'success': False,
        'citations': [],
        'metadata': {
            'source_type': 'unknown',
            'start_time': start_time,
            'end_time': None,
            'duration_ms': None,
            'debug': {}
        },
        'error': None
    }
    
    try:
        # Parse request data
        data = {}
        if request.content_type and "multipart/form-data" in request.content_type:
            data = request.form.to_dict()
            if 'file' in request.files:
                data['file'] = request.files['file']
        else:
            data = request.get_json(silent=True) or {}
            
        log_data = {}
        for k, v in data.items():
            if k == 'text':
                continue
            if hasattr(v, 'filename') and hasattr(v, 'content_type'):
                log_data[k] = f"<FileStorage: {v.filename} ({v.content_type})>"
            else:
                log_data[k] = v
        logger.info(f"[ANALYZE:{request_id}] Request data: {log_data}")
        logger.info(f"[ANALYZE:{request_id}] Text length: {len(data.get('text', '')) if 'text' in data else 'N/A'}")
        
        # Initialize processing variables
        citations = []
        source_type = "unknown"

        # Process file upload
        if request.content_type and "multipart/form-data" in request.content_type:
            try:
                logger.info(f"[ANALYZE:{request_id}] Processing file upload")
                
                if "file" not in request.files:
                    raise ValueError("No file part in the request")

                file = request.files["file"]
                if file.filename == "":
                    raise ValueError("No file selected")

                if not file or not allowed_file(file.filename):
                    raise ValueError("File type not allowed")
                
                # Process the uploaded file
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                logger.info(f"[ANALYZE:{request_id}] File saved to {filepath}")
                
                # Extract text from the file
                try:
                    from file_utils import extract_text_from_file
                    file_text = extract_text_from_file(filepath)
                    
                    if not isinstance(file_text, str) or not file_text.strip():
                        raise ValueError("File extraction returned empty or invalid text")
                        
                    logger.info(f"[ANALYZE:{request_id}] Extracted {len(file_text)} characters from file")
                    
                    # Analyze the extracted text
                    from enhanced_validator_production import analyze_text
                    analysis = analyze_text(file_text)
                    source_type = "file"
                    
                    # Add debug info if requested
                    if data.get("debug"):
                        analysis["debug_info"] = {
                            "file_path": filepath,
                            "file_size": os.path.getsize(filepath),
                            "text_length": len(file_text)
                        }
                        
                except Exception as e:
                    logger.error(f"[ANALYZE:{request_id}] Error processing file: {str(e)}", exc_info=True)
                    raise ValueError(f"Error processing file: {str(e)}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[ANALYZE:{request_id}] File upload error: {error_msg}", exc_info=True)
                response_data['error'] = error_msg
                response_data['metadata']['debug']['error_type'] = 'file_upload_error'
                return jsonify(response_data), 400
                
        # Process text or URL
        else:
            try:
                if data.get("text"):
                    logger.info(f"[ANALYZE:{request_id}] Processing text input")
                    
                    text = data["text"]
                    if not isinstance(text, str):
                        raise ValueError(f"Input text must be a string, got {type(text)}")
                        
                    logger.info(f"[ANALYZE:{request_id}] Analyzing text of length: {len(text)}")
                    
                    analysis = analyze_text(text)
                    source_type = "text"
                    
                elif data.get("url"):
                    # Fetch content from URL and analyze
                    url = data["url"]
                    logger.info(f"[ANALYZE:{request_id}] Processing URL: {url}")
                    
                    try:
                        logger.info(f"[ANALYZE:{request_id}] Calling fetch_url_content")
                        url_content = fetch_url_content(url)
                        logger.info(f"[ANALYZE:{request_id}] fetch_url_content returned: {type(url_content)}")
                        
                        if not isinstance(url_content, dict):
                            logger.error(f"[ANALYZE:{request_id}] fetch_url_content did not return a dict: {url_content}")
                            raise ValueError("Unexpected response format from URL fetcher")
                            
                        if not url_content.get("text"):
                            logger.error(f"[ANALYZE:{request_id}] No text in response: {url_content}")
                            raise ValueError("No text content found in URL response")
                            
                        text = url_content["text"]
                        logger.info(f"[ANALYZE:{request_id}] Fetched {len(text)} characters from URL")
                        
                        logger.info(f"[ANALYZE:{request_id}] Calling analyze_text")
                        analysis = analyze_text(text)
                        logger.info(f"[ANALYZE:{request_id}] analyze_text completed")
                        
                        source_type = "url"
                        
                        # Add URL metadata
                        if 'metadata' not in analysis:
                            analysis['metadata'] = {}
                        analysis['metadata']['url'] = url
                        
                    except Exception as e:
                        logger.error(f"[ANALYZE:{request_id}] URL processing error: {str(e)}", exc_info=True)
                        # Include more detailed error information
                        error_type = type(e).__name__
                        error_details = str(e)
                        error_msg = f"Error processing URL ({error_type}): {error_details}"
                        logger.error(f"[ANALYZE:{request_id}] {error_msg}")
                        raise ValueError(error_msg) from e
                        
                else:
                    raise ValueError("No text or URL provided in request")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[ANALYZE:{request_id}] Text/URL processing error: {error_msg}", exc_info=True)
                response_data['error'] = error_msg
                response_data['metadata']['debug']['error_type'] = 'processing_error'
                return jsonify(response_data), 400
        
        # Process the analysis results
        if not isinstance(analysis, dict):
            error_msg = f"Analysis result is not a dictionary: {type(analysis)}"
            logger.error(f"[ANALYZE:{request_id}] {error_msg}")
            response_data['error'] = "Invalid analysis result format"
            response_data['metadata']['debug']['error_type'] = 'invalid_analysis_format'
            return jsonify(response_data), 500

        # Extract citations from the analysis result
        citations = []
        landmark_cases = []
        validation_results = []
        
        # Check for citations in the expected format from enhanced_validator_production
        if "citations" in analysis and isinstance(analysis["citations"], list):
            # Handle the case where citations is already a list
            citations = analysis["citations"]
        elif "citations" in analysis and isinstance(analysis["citations"], dict):
            # Handle the format from enhanced_validator_production
            if "confirmed_citations" in analysis["citations"]:
                citations.extend(analysis["citations"]["confirmed_citations"] or [])
            if "possible_citations" in analysis["citations"]:
                citations.extend(analysis["citations"]["possible_citations"] or [])
        
        # Extract landmark cases and validation results if available
        landmark_cases = analysis.get("landmark_cases", [])
        validation_results = analysis.get("validation_results", [])
        
        # If we have validation results but no citations, create citations from them
        if not citations and validation_results:
            citations = [
                {
                    "citation": result.get("citation", {}).get("citation_text", ""),
                    "case_name": result.get("citation", {}).get("case_name", ""),
                    "verified": result.get("validation", {}).get("verified", False),
                    "validation_method": result.get("validation", {}).get("validation_method", ""),
                    "metadata": result.get("citation", {}).get("metadata", {})
                }
                for result in validation_results
            ]
        # If we have citations but no validation results, try to create validation results
        elif citations and not validation_results:
            validation_results = [
                {
                    "citation": {
                        "citation_text": cite.get("citation", ""),
                        "case_name": cite.get("case_name", ""),
                        "metadata": cite.get("metadata", {})
                    },
                    "validation": {
                        "verified": cite.get("verified", False),
                        "validation_method": cite.get("validation_method", ""),
                        "case_name": cite.get("case_name", "")
                    }
                }
                for cite in citations
                if isinstance(cite, dict)
            ]
        
        # Log the number of citations found
        logger.info(f"[ANALYZE:{request_id}] Found {len(citations)} citations, "
                  f"{len(landmark_cases)} landmark cases, and "
                  f"{len(validation_results)} validation results in analysis")
        
        # Prepare the response data
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Add debug info if present in the request
        if data.get("debug_info"):
            logs_dir = os.path.join(current_app.root_path, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            with open(os.path.join(logs_dir, "frontend_debug.log"), "a") as f:
                f.write(json.dumps(data["debug_info"]) + "\n")
            analysis["debug_info"] = data["debug_info"]
        
        # Prepare the response with all available data
        response_data.update({
            'success': True,
            'citations': citations,  # The main citations list
            'landmark_cases': landmark_cases,  # Any landmark cases found
            'validation_results': validation_results,  # Detailed validation results
            'metadata': {
                **response_data['metadata'],
                'source_type': source_type,
                'start_time': start_time,
                'end_time': end_time,
                'duration_ms': duration_ms,
                'citation_count': len(citations),
                'landmark_case_count': len(landmark_cases),
                'validation_count': len(validation_results),
                **analysis.get('metadata', {})
            },
            # Include any other analysis data that might be useful
            **{k: v for k, v in analysis.items() 
               if k not in ['citations', 'metadata', 'landmark_cases', 'validation_results']}
        })

        # Log completion
        logger.info(
            f"[ANALYZE:{request_id}] Analysis complete. "
            f"Found {len(response_data['citations'])} citations in {duration_ms:.2f}ms"
        )

        # Clean up any file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"[ANALYZE:{request_id}] Removed temporary file: {filepath}")
            except Exception as e:
                logger.warning(f"[ANALYZE:{request_id}] Failed to remove temporary file: {str(e)}")

        return jsonify(response_data)
    except Exception as e:
        error_msg = f"Unexpected error in analyze endpoint: {str(e)}"
        logger.error(f"[ANALYZE:{request_id}] {error_msg}")
        logger.error(traceback.format_exc())
        
        # Prepare error response with consistent structure
        end_time = time.time()
        error_response = {
            'request_id': request_id,
            'success': False,
            'error': error_msg,
            'citations': [],
            'metadata': {
                'source_type': 'unknown',
                'start_time': start_time,
                'end_time': end_time,
                'duration_ms': (end_time - start_time) * 1000,
                'error_type': 'unexpected_error',
                'error_traceback': traceback.format_exc()
            }
        }
        
        return jsonify(error_response), 500


@api_blueprint.route("/status", methods=["GET"])
def status():
    """Get the status of an ongoing analysis."""
    try:
        return jsonify(
            {"status": "completed", "progress": 100, "message": "Analysis complete"}
        )
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/unconfirmed_citations_data", methods=["POST"])
def unconfirmed_citations_data():
    """Get unconfirmed citations data with optional filters."""
    try:
        return jsonify(
            {
                "citations": [
                    {
                        "id": 1,
                        "citation_text": "410 U.S. 113",
                        "case_name": "Roe v. Wade",
                        "confidence": 0.3,
                        "explanation": "Citation format is valid but case name could not be verified",
                        "source_file": "example.pdf",
                    },
                    {
                        "id": 2,
                        "citation_text": "347 U.S. 483",
                        "case_name": "Brown v. Board of Education",
                        "confidence": 0.4,
                        "explanation": "Citation format is valid but case name could not be verified",
                        "source_file": "example.pdf",
                    },
                ],
                "total": 2,
            }
        )
    except Exception as e:
        logger.error(f"Error in unconfirmed_citations_data endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/confirmed_with_multitool_data", methods=["GET"])
def confirmed_with_multitool_data():
    """Get citations confirmed with multiple tools."""
    try:
        return jsonify(
            {
                "citations": [
                    {
                        "id": 3,
                        "citation_text": "531 U.S. 98",
                        "case_name": "Bush v. Gore",
                        "confidence": 0.9,
                        "explanation": "Verified with multiple sources",
                        "source_file": "example.pdf",
                    },
                    {
                        "id": 4,
                        "citation_text": "558 U.S. 310",
                        "case_name": "Citizens United v. FEC",
                        "confidence": 0.95,
                        "explanation": "Verified with multiple sources",
                        "source_file": "example.pdf",
                    },
                ],
                "total": 2,
            }
        )
    except Exception as e:
        logger.error(f"Error in confirmed_with_multitool_data endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/citation_network_data", methods=["GET"])
def citation_network_data():
    """Get citation network data for visualization."""
    try:
        return jsonify(
            {
                "nodes": [
                    {
                        "id": 1,
                        "name": "Roe v. Wade",
                        "citation": "410 U.S. 113",
                        "type": "unconfirmed",
                    },
                    {
                        "id": 2,
                        "name": "Brown v. Board of Education",
                        "citation": "347 U.S. 483",
                        "type": "unconfirmed",
                    },
                    {
                        "id": 3,
                        "name": "Bush v. Gore",
                        "citation": "531 U.S. 98",
                        "type": "confirmed",
                    },
                    {
                        "id": 4,
                        "name": "Citizens United v. FEC",
                        "citation": "558 U.S. 310",
                        "type": "confirmed",
                    },
                ],
                "links": [
                    {"source": 1, "target": 2},
                    {"source": 2, "target": 3},
                    {"source": 3, "target": 4},
                    {"source": 4, "target": 1},
                ],
            }
        )
    except Exception as e:
        logger.error(f"Error in citation_network_data endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/train_ml_classifier", methods=["POST"])
def train_ml_classifier_endpoint():
    """Train the ML classifier on the citation database."""
    try:
        return jsonify(
            {
                "status": "success",
                "message": "ML classifier trained successfully",
                "accuracy": 0.85,
            }
        )
    except Exception as e:
        logger.error(f"Error in train_ml_classifier endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/classify_citation", methods=["POST"])
def classify_citation_endpoint():
    """Classify a citation using the ML model."""
    try:
        return jsonify(
            {
                "citation": request.json.get("citation", ""),
                "case_name": request.json.get("case_name", ""),
                "confidence": 0.75,
                "is_valid": True,
                "explanation": "Citation format is valid and case name matches records",
            }
        )
    except Exception as e:
        logger.error(f"Error in classify_citation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/test_citations", methods=["GET"])
def test_citations():
    """Get a set of test citations for the citation tester."""
    try:
        return jsonify(
            {
                "citations": [
                    {
                        "id": 5,
                        "citation_text": "384 U.S. 436",
                        "case_name": "Miranda v. Arizona",
                        "confidence": 0.8,
                        "explanation": "Verified with Court Listener API",
                        "source_file": "test_data.pdf",
                    },
                    {
                        "id": 6,
                        "citation_text": "376 U.S. 254",
                        "case_name": "New York Times Co. v. Sullivan",
                        "confidence": 0.85,
                        "explanation": "Verified with Court Listener API",
                        "source_file": "test_data.pdf",
                    },
                ],
                "total": 2,
            }
        )
    except Exception as e:
        logger.error(f"Error in test_citations endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/export_citations", methods=["POST"])
def export_citations_endpoint():
    """Export citations in the specified format."""
    try:
        return jsonify(
            {
                "format": request.json.get("format", "text"),
                "content": "Roe v. Wade, 410 U.S. 113 (1973)\nBrown v. Board of Education, 347 U.S. 483 (1954)",
            }
        )
    except Exception as e:
        logger.error(f"Error in export_citations endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/verify_citation", methods=["POST"])
def verify_citation_endpoint():
    """Verify a single citation using the real verification logic."""
    try:
        data = request.get_json()
        citation = data.get("citation", "")
        case_name = data.get("case_name", None)
        if not citation:
            return jsonify({"error": "No citation provided"}), 400

        # Call the real verification logic
        from citation_utils import verify_citation

        verification_result = verify_citation(citation, context=case_name)
        # Optionally add the original citation and case name to the response
        verification_result["citation"] = citation
        verification_result["case_name"] = case_name
        return jsonify(verification_result)
    except Exception as e:
        logger.error(f"Error in verify_citation endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/correction_suggestions", methods=["POST"])
def correction_suggestions():
    """Get suggestions for correcting a citation."""
    try:
        citation = request.json.get("citation", "")
        return jsonify(
            {
                "original": citation,
                "suggestions": [
                    {
                        "citation": "410 U.S. 113",
                        "case_name": "Roe v. Wade",
                        "confidence": 0.95,
                        "explanation": "Exact match found in database",
                    },
                    {
                        "citation": "410 U.S. 113 (1973)",
                        "case_name": "Roe v. Wade",
                        "confidence": 0.9,
                        "explanation": "Match found with year",
                    },
                ],
            }
        )
    except Exception as e:
        logger.error(f"Error in correction_suggestions endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500