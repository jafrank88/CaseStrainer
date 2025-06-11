"""
Vue.js API Endpoints for CaseStrainer

This module provides the API endpoints needed by the Vue.js frontend
for the Multitool Confirmed and Unconfirmed Citations tabs.
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
from citation_utils import verify_citation, extract_citations_from_text

# Import configuration
from config import get_config_value

# Get API key
COURTLISTENER_API_KEY = get_config_value("COURTLISTENER_API_KEY")

# Import enhanced validator utilities
try:
    from enhanced_validator_utils import register_enhanced_validator_func
    ENHANCED_VALIDATOR_AVAILABLE = True
except ImportError:
    register_enhanced_validator_func = None
    ENHANCED_VALIDATOR_AVAILABLE = False

from src.file_utils import extract_text_from_file

import re
import logging
from src.pdf_handler import PDFHandler, PDFExtractionMethod, PDFExtractionConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a Blueprint for Vue.js API endpoints
vue_api = Blueprint('vue_api', __name__)

def enhanced_validate_citation(citation_text=None, api_key=None, case_name=None, request_data=None):
    """Enhanced citation validation using multiple sources.
    
    Args:
        citation_text (str, optional): The citation text to validate.
        api_key (str, optional): API key for external services.
        case_name (str, optional): The name of the case associated with the citation.
        request_data (dict, optional): Pre-parsed request data.
    
    Returns:
        tuple: A tuple containing (response_json, status_code)
    """
    def create_error_response(error_msg, status_code=400):
        """Helper to create consistent error responses."""
        return {
            "citation": "" if citation_text is None else citation_text,
            "verified": False,
            "verified_by": "Error",
            "error": error_msg,
            "metadata": {"case_name": case_name} if case_name else {},
            "backdrop": "",
            "verification_steps": [error_msg]
        }, status_code

    # Get the data from request if not provided
    if request_data is None:
        try:
            if hasattr(request, 'is_json') and request.is_json:
                request_data = request.get_json(silent=True) or {}
            elif hasattr(request, 'form'):
                request_data = request.form.to_dict()
                # Handle file uploads if present
                if hasattr(request, 'files') and 'file' in request.files:
                    request_data['file'] = request.files['file']
            else:
                request_data = {}
        except Exception as e:
            current_app.logger.error(f"[enhanced_validate_citation] Error parsing request data: {str(e)}")
            return create_error_response(f"Error parsing request data: {str(e)}", 400)
    
    current_app.logger.debug(f"[enhanced_validate_citation] Received data: {request_data}")
    
    # Handle document analysis case
    if citation_text == 'document_analysis':
        if 'file' not in request_data and (not hasattr(request, 'files') or 'file' not in request.files):
            return {
                'valid': False,
                'message': 'No file provided for document analysis',
                'citation': 'document_analysis',
                'case_name': case_name or '',
                'verification_steps': ['Error: No file provided for document analysis']
            }, 400
        
        # Process the file here or pass it to the appropriate handler
        # For now, just return a success response
        return {
            'valid': True,
            'message': 'Document analysis started',
            'citation': 'document_analysis',
            'case_name': case_name or '',
            'verification_steps': ['Document uploaded successfully']
        }, 200
    
    # Handle different input formats
    if not citation_text and isinstance(request_data.get("citation"), dict):
        # Handle citation object format
        citation_obj = request_data["citation"]
        citation_text = citation_obj.get("text", citation_obj.get("citation_text", ""))
        case_name = case_name or citation_obj.get("case_name", citation_obj.get("name", ""))
    elif not citation_text:
        # Handle direct string citation from request data
        citation_text = request_data.get("citation", request_data.get("citation_text", ""))
        case_name = case_name or request_data.get("case_name", "")

    # If citation_text is a dictionary, try to get the text
    if isinstance(citation_text, dict):
        citation_text = citation_text.get("text", citation_text.get("citation_text", ""))

    # Convert to string if not already
    if citation_text is not None and not isinstance(citation_text, str):
        citation_text = str(citation_text)

    # Clean and validate the citation
    if not citation_text or not citation_text.strip():
        current_app.logger.warning("[enhanced_validate_citation] No citation provided")
        return create_error_response("No citation provided", 400)

    current_app.logger.info(f"[enhanced_validate_citation] Validating citation: {citation_text}")
    if case_name:
        current_app.logger.debug(f"[enhanced_validate_citation] With case name: {case_name}")

    # Try enhanced verifier first if available
    if ENHANCED_VALIDATOR_AVAILABLE and register_enhanced_validator_func:
        try:
            enhanced_verifier = register_enhanced_validator_func()
            if enhanced_verifier:
                try:
                    # Get the verification result from the enhanced verifier
                    current_app.logger.info(
                        f"[enhanced_validate_citation] Starting verification for: {citation_text}"
                    )
                    # Use validate_citation instead of verify_citation
                    result = enhanced_verifier.validate_citation(citation_text)
                    
                    # Log the raw result for debugging
                    current_app.logger.debug(
                        f"[enhanced_validate_citation] Verifier result type: {type(result).__name__}, "
                        f"content: {json.dumps(result, default=str, indent=2) if hasattr(result, 'get') else str(result)}"
                    )
                    
                    # Process the result
                    if result is None:
                        return create_error_response("Verification returned no result")
                        
                    response = None
                    if isinstance(result, dict):
                        # Handle dictionary result
                        response = {
                            "citation": citation_text,
                            "valid": result.get("exists", False),
                            "verified": result.get("exists", False),  # For backward compatibility
                            "verified_by": result.get("verified_by", "Enhanced Validator"),
                            "metadata": result.get("metadata", {}),
                            "backdrop": result.get("backdrop", ""),
                            "error": result.get("error", ""),
                            "warnings": result.get("warnings", []),
                            "verification_steps": result.get("verification_steps", []),
                            "sources": result.get("sources", {})
                        }
                    elif hasattr(result, "__dict__"):
                        # Handle object result
                        response = {
                            "citation": citation_text,
                            "valid": getattr(result, "exists", False),
                            "verified": getattr(result, "exists", False),  # For backward compatibility
                            "verified_by": getattr(result, "verified_by", "Enhanced Validator"),
                            "metadata": getattr(result, "metadata", {}),
                            "backdrop": getattr(result, "backdrop", ""),
                            "error": getattr(result, "error", ""),
                            "warnings": getattr(result, "warnings", []),
                            "verification_steps": getattr(result, "verification_steps", []),
                            "sources": getattr(result, "sources", {})
                        }
                    
                    if response is not None:
                        # Ensure case_name is preserved if provided
                        if case_name and "case_name" not in response["metadata"]:
                            response["metadata"]["case_name"] = case_name
                        
                        # Add message if not present
                        if not response.get("message"):
                            if response.get("valid"):
                                response["message"] = "Citation verified successfully"
                            else:
                                response["message"] = response.get("error", "Citation verification failed")
                        
                        return response
                    
                    return create_error_response(f"Unexpected result type: {type(result).__name__}")
                        
                except Exception as e:
                    error_msg = f"Error in verification service: {str(e)}"
                    current_app.logger.error(
                        f"[enhanced_validate_citation] {error_msg}",
                        exc_info=True
                    )
                    return create_error_response(error_msg, 500)
                    
        except Exception as e:
            error_msg = f"Error initializing enhanced verifier: {str(e)}"
            current_app.logger.error(
                f"[enhanced_validate_citation] {error_msg}",
                exc_info=True
            )
            return create_error_response(error_msg, 500)
            return create_error_response("Failed to initialize verification service", 500)
    
    # Fall back to basic validation if enhanced validation is not available or fails
    try:
        # Import the citation verifier directly
        from citation_verification import CitationVerifier
        
        # Log that we're falling back to basic verification
        current_app.logger.info("[enhanced_validate_citation] Falling back to basic verification")
        
        # Initialize the verifier with the API key from config
        verifier = CitationVerifier(api_key=COURTLISTENER_API_KEY)
        
        # Call the verification function directly
        result = verifier.verify_citation(citation_text)
        
        # Process the verification result
        if isinstance(result, dict):
            # Start with the basic response structure
            response = {
                "citation": citation_text,
                "valid": result.get("found", False),
                "verified": result.get("found", False),  # For backward compatibility
                "verified_by": result.get("source", "Basic Validator"),
                "metadata": {},
                "backdrop": "",
                "error": result.get("error", ""),
                "verification_steps": ["Basic verification completed"],
                "message": "Citation verified using basic validation" if result.get("found") else "Citation validation failed"
            }
            
            # Add metadata if available
            if "metadata" in result and isinstance(result["metadata"], dict):
                response["metadata"].update(result["metadata"])
            
            # Ensure we have the basic fields
            if "case_name" in result and not response["metadata"].get("case_name"):
                response["metadata"]["case_name"] = result["case_name"]
            if "url" in result and not response["metadata"].get("url"):
                response["metadata"]["url"] = result["url"]
            if "explanation" in result and not response["metadata"].get("explanation"):
                response["metadata"]["explanation"] = result["explanation"]
            
            # Add any additional details
            if "details" in result and isinstance(result["details"], dict):
                response["details"] = result["details"]
                
                # Map details to top-level metadata for backward compatibility
                if "volume" in result["details"] and not response["metadata"].get("volume"):
                    response["metadata"]["volume"] = result["details"]["volume"]
                if "reporter" in result["details"] and not response["metadata"].get("reporter"):
                    response["metadata"]["reporter"] = result["details"]["reporter"]
                if "page" in result["details"] and not response["metadata"].get("page"):
                    response["metadata"]["page"] = result["details"]["page"]
            
            # Add any other top-level fields from result to metadata if they don't exist
            for key in ["court", "docket_number", "date_filed", "citation_count", "precedential_status"]:
                if key in result and key not in response["metadata"]:
                    response["metadata"][key] = result[key]
                
            return response
    except Exception as e:
        error_msg = f"Error in basic validation: {str(e)}"
        current_app.logger.error(
            f"[enhanced_validate_citation] {error_msg}",
            exc_info=True
        )
        return create_error_response(error_msg, 500)
    
    # If we reach here, no validation was successful
    current_app.logger.warning(
        f"[enhanced_validate_citation] No validation method succeeded for citation: {citation_text}"
    )
    
    try:
        # Create response data
        response_data = {
            "status": "success",
            "validation_results": [{
                "citation": citation_text,
                "valid": False,
                "verified": False,
                "verified_by": "No Validator Available",
                "metadata": {"case_name": case_name} if case_name else {},
                "backdrop": "",
                "error": "Unable to verify citation with any available validator",
                "verification_steps": ["No validation method was successful"],
                "message": "Citation could not be verified with any available validator"
            }],
            "total_citations": 1,
            "valid_citations": 0,
            "invalid_citations": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "CaseStrainer API",
            },
        }
        
        # Return the JSON response
        return current_app.response_class(
            response=json.dumps(response_data, indent=2, ensure_ascii=False),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"Error formatting citation result: {str(e)}", exc_info=True)
        # Return a minimal error response
        error_response = {
            "status": "error",
            "message": f"Error processing request: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "url": "",
        }
        return jsonify(error_response), 500


@vue_api.route("/verify-citation", methods=["POST", "OPTIONS"])
def verify_citation():
    """
    API endpoint to verify a single citation.
    Handles both JSON and form-encoded requests.
    
    This endpoint is available at /casestrainer/api/verify-citation.
    """
    return handle_verify_citation()

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
        
        # Handle OPTIONS request for CORS preflight
        if request.method == 'OPTIONS':
            response = make_response(jsonify({'status': 'ok'}), 200)
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

        # Check if this is a file upload or document analysis request
        if 'file' in request.files or 'file' in request.form or (request.is_json and 'file' in (request.get_json(silent=True) or {})):
            current_app.logger.info("[ANALYZE] Routing to analyze_document")
            return analyze_document()
            
        # Otherwise, treat it as a citation verification request
        current_app.logger.info("[ANALYZE] Routing to handle_verify_citation")
        return handle_verify_citation()
        
    except Exception as e:
        current_app.logger.error(f"[ANALYZE] Error in /api/analyze endpoint: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Create a proper error response
        error_response = {
            'status': 'error',
            'message': 'An internal server error occurred',
            'error': str(e)
        }
        
        # Set CORS headers for the error response
        response = jsonify(error_response)
        response.status_code = 500
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response

def handle_verify_citation():
    # Create a response object that we'll modify in the after_request handler
    response_headers = {}
    
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = make_response('', 204)
        response_headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', 'http://localhost:5173'),
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '3600'
        })
        response.headers.update(response_headers)
        return response
    
    # Add CORS headers to the response
    @after_this_request
    def add_cors_headers(response):
        response.headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', 'http://localhost:5173'),
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Max-Age': '3600'
        })
        return response
    
    # Initialize default response
    default_error_response = {
        "verified": False,
        "error": "",
        "metadata": {},
        "backdrop": "",
        "citation": "",
    }

    try:
        # Log the incoming request details
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
        
        # Initialize data dict and citation variables
        data = {}
        citation = None
        case_name = ""
        
        # Parse request data based on content type
        if request.is_json:
            current_app.logger.info("Processing JSON request")
            try:
                data = request.get_json(force=True, silent=True) or {}
                current_app.logger.info(f"Successfully parsed JSON data: {data}")
                
                # Extract citation and case_name from JSON data
                if isinstance(data, dict):
                    # Try different possible keys for citation
                    citation = data.get("citation", data.get("citation_text", ""))
                    case_name = data.get("case_name", "")
                else:
                    citation = str(data)
                
                current_app.logger.info(f"Extracted citation: {citation}, case_name: {case_name}")
                
            except Exception as e:
                current_app.logger.error(f"Error parsing JSON data: {str(e)}")
                error_response = default_error_response.copy()
                error_response.update({
                    "error": f"Invalid JSON data: {str(e)}",
                    "verification_steps": [f"Error: Invalid JSON data - {str(e)}"]
                })
                return jsonify(error_response), 400
                
        # Handle form data and file uploads
        elif request.form or request.files:
            current_app.logger.info("Processing form data")
            data = request.form.to_dict()
            
            # Handle file upload if present
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    current_app.logger.info(f"Processing file upload: {file.filename}")
                    try:
                        # Read file content as bytes first
                        file_content = file.read()
                        
                        # Create a temporary file to store the upload
                        import tempfile
                        import os
                        
                        # Create temp directory if it doesn't exist
                        temp_dir = os.path.join(current_app.root_path, 'temp_uploads')
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Save the file with a secure filename
                        filename = secure_filename(file.filename)
                        temp_path = os.path.join(temp_dir, filename)
                        
                        # Write the file content to the temporary file
                        with open(temp_path, 'wb') as temp_file:
                            temp_file.write(file_content)
                        
                        current_app.logger.info(f"[ANALYZE_DOCUMENT] Saved uploaded file to {temp_path}")
                        
                        # Store metadata
                        request_data = {}
                        request_data['filename'] = filename
                        
                        # Initialize options if not present
                        options = request_data.get('options', {})
                        if not isinstance(options, dict):
                            options = {}
                            request_data['options'] = options
                        
                        # Set file type and extension if not already set
                        if hasattr(file, 'content_type') and 'file_type' not in options:
                            options['file_type'] = file.content_type
                        
                        if hasattr(file, 'filename') and 'file_ext' not in options:
                            file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
                            options['file_ext'] = file_ext if file_ext else ''
                        
                        # Ensure binary flag is set for non-text files
                        if hasattr(file, 'content_type') and file.content_type != 'text/plain':
                            options['is_binary'] = True
                        
                        # Get text from file if no text provided
                        if 'text' not in request_data or not request_data.get('text'):
                            try:
                                # Get text content from file using the saved file path
                                text = extract_text_from_file(temp_path, options)
                                request_data['text'] = text
                                current_app.logger.info("[ANALYZE_DOCUMENT] Successfully extracted text from file")
                            except Exception as e:
                                error_msg = f'Error extracting text from file: {str(e)}'
                                current_app.logger.error(f'[ANALYZE_DOCUMENT] {error_msg}')
                                current_app.logger.error(traceback.format_exc())
                                return jsonify({
                                    'status': 'error',
                                    'message': error_msg,
                                    'code': 'TEXT_EXTRACTION_ERROR'
                                }), 500
                            finally:
                                # Clean up the temporary file
                                try:
                                    os.remove(temp_path)
                                    current_app.logger.debug(f"[ANALYZE_DOCUMENT] Deleted temporary file: {temp_path}")
                                except Exception as e:
                                    current_app.logger.warning(f"[ANALYZE_DOCUMENT] Error deleting temp file {temp_path}: {str(e)}")
                    except Exception as e:
                        error_msg = f'Error processing file: {str(e)}'
                        current_app.logger.error(f'[ANALYZE_DOCUMENT] {error_msg}')
                        current_app.logger.error(traceback.format_exc())
                        return jsonify({
                            'status': 'error',
                            'message': error_msg,
                            'code': 'FILE_PROCESSING_ERROR'
                        }), 500

        # Handle form data and file uploads
        elif request.form or request.files:
            current_app.logger.info("Processing form data")
            data = request.form.to_dict()
            
            # Handle file upload if present
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    current_app.logger.info(f"Processing file upload: {file.filename}")
                    try:
                        # Read file content
                        file_content = file.read()
                        
                        # For this endpoint, we'll just log the file info and continue with other form data
                        current_app.logger.info(f"Received file: {file.filename}, size: {len(file_content)} bytes")
                        
                        # Store file info in the data dict
                        data = request.form.to_dict()
                        data['file_info'] = {
                            'filename': file.filename,
                            'content_type': file.content_type,
                            'size': len(file_content)
                        }
                    except Exception as e:
                        current_app.logger.error(f"Error processing uploaded file: {str(e)}")
                        error_response = default_error_response.copy()
                        error_response.update({
                            "error": f"Error processing uploaded file: {str(e)}",
                            "verification_steps": [f"Error: Failed to process uploaded file - {str(e)}"]
                        })
                        return jsonify(error_response), 400
            else:
                data = request.form.to_dict()
            
            current_app.logger.info(f"Form data: {data}")
            
            # Extract citation and case_name from form data
            citation = data.get("citation", data.get("citation_text", ""))
            case_name = data.get("case_name", "")
            
            # If we have options as a JSON string, parse it
            if 'options' in data and isinstance(data['options'], str):
                try:
                    data['options'] = json.loads(data['options'])
                except json.JSONDecodeError:
                    current_app.logger.warning("Could not parse options as JSON")
                    data['options'] = {}
            current_app.logger.info(f"Extracted from form - citation: {citation}, case_name: {case_name}")
        
        # If still no data, try to parse raw data
        elif request.data:
            current_app.logger.info("Processing raw request data")
            raw_data = request.data.decode('utf-8')
            current_app.logger.info(f"Raw data: {raw_data}")
            
            # Try to parse as JSON
            try:
                data = json.loads(raw_data)
                current_app.logger.info("Successfully parsed raw data as JSON")
                if isinstance(data, dict):
                    citation = data.get("citation", "")
                    case_name = data.get("case_name", "")
                else:
                    citation = str(data)
            except json.JSONDecodeError:
                # Try to parse as URL-encoded form data
                try:
                    data = {}
                    for item in raw_data.split('&'):
                        if '=' in item:
                            k, v = item.split('=', 1)
                            data[k] = v
                    current_app.logger.info("Parsed as URL-encoded form data")
                    citation = data.get("citation", "")
                    case_name = data.get("case_name", "")
                except Exception as e:
                    error_msg = f"Could not parse request data: {str(e)}"
                    current_app.logger.error(error_msg)
                    default_error_response["error"] = error_msg
                    return jsonify(default_error_response), 400, response_headers
        
        # Log final parsed data
        current_app.logger.info(f"Final parsed data: {data}")
        
        # Handle document analysis case
        if citation == 'document_analysis':
            if 'file_info' not in data and 'file' not in request.files:
                error_msg = "No file provided for document analysis"
                current_app.logger.error(error_msg)
                default_error_response["error"] = error_msg
                return jsonify(default_error_response), 400, response_headers
            
            # Process the file here or pass it to the appropriate handler
            # For now, just return a success response
            response_data = {
                'valid': True,
                'message': 'Document analysis started',
                'citation': 'document_analysis',
                'case_name': case_name,
                'verification_steps': ['Document uploaded successfully']
            }
            return jsonify(response_data), 200, response_headers
        
        # If we still don't have a citation, return an error
        if not citation:
            error_msg = "No citation provided in request"
            current_app.logger.error(error_msg)
            default_error_response["error"] = error_msg
            return jsonify(default_error_response), 400, response_headers

        # If citation is a dictionary, extract the text
        if isinstance(citation, dict):
            citation = citation.get("text", citation.get("citation_text", ""))
            if not citation:
                error_msg = "Invalid citation format"
                current_app.logger.error(error_msg)
                default_error_response["error"] = error_msg
                return jsonify(default_error_response), 400, response_headers

        # Log the citation being validated
        current_app.logger.info(f"[verify_citation] Validating citation: {citation}")
        if case_name:
            current_app.logger.info(f"[verify_citation] With case name: {case_name}")
        
        try:
            # Call the enhanced validation function with the citation data
            current_app.logger.info(f"[verify_citation] Starting validation for citation: {citation}")
            
            # Call the enhanced validation function directly with the citation text
            current_app.logger.info(f"[verify_citation] Calling enhanced_validate_citation with citation: {citation}")
            try:
                result = enhanced_validate_citation(
                    citation_text=citation,
                    case_name=case_name,
                    request_data=data  # Pass the parsed request data
                )
                current_app.logger.info(f"[verify_citation] enhanced_validate_citation returned: {type(result)}")
                
                # Handle the response from enhanced_validate_citation
                if isinstance(result, tuple):
                    current_app.logger.info(f"[verify_citation] Result tuple length: {len(result)}")
                    if len(result) > 0 and hasattr(result[0], 'get_data'):
                        current_app.logger.info(f"[verify_citation] Response data: {result[0].get_data()}")
                    
                    # Unpack the response tuple
                    if len(result) == 3:
                        response_data, status_code, response_headers = result
                    elif len(result) == 2:
                        response_data, status_code = result
                        response_headers = response_headers
                    else:
                        response_data = result[0] if result else {}
                        status_code = 200
                        response_headers = response_headers
                    
                    # Ensure we have a valid response
                    if not isinstance(response_data, (dict, list)):
                        response_data = {"error": "Invalid response format from validation service"}
                        status_code = 500
                else:
                    # If it's not a tuple, assume it's the response data
                    response_data = result
                    status_code = 200
                    response_headers = response_headers
                
                return jsonify(response_data), status_code, response_headers
                
            except Exception as e:
                current_app.logger.error(f"[verify_citation] Error in enhanced_validate_citation: {str(e)}", exc_info=True)
                raise
                
        except Exception as e:
            current_app.logger.error(f"[verify_citation] Error during citation validation: {str(e)}", exc_info=True)
            error_response = default_error_response.copy()
            error_response.update({
                "error": f"Error during citation validation: {str(e)}",
                "verification_steps": [f"Error: {str(e)}"]
            })
            return jsonify(error_response), 500, response_headers
            
            # Handle the response from enhanced_validate_citation
            if isinstance(result, tuple):
                # If it's a tuple, it might be (response, status_code) or (response, status_code, headers)
                if len(result) == 3:
                    response_data, status_code, response_headers = result
                elif len(result) == 2:
                    response_data, status_code = result
                    response_headers = response_headers
                else:
                    response_data = result[0] if result else {}
                    status_code = 200
                    response_headers = response_headers
                
                # Ensure we have a valid response
                if not isinstance(response_data, (dict, list)):
                    response_data = {"error": "Invalid response format from validation service"}
                
                # Add the citation to the response if not present
                if isinstance(response_data, dict) and "citation" not in response_data:
                    response_data["citation"] = citation
                
                return jsonify(response_data), status_code, response_headers
                
            elif hasattr(result, 'get_json'):
                # If it's a Flask response object, return it as is
                return result
                
            # If it's a dictionary but not a tuple or response object
            elif isinstance(result, dict):
                # Ensure citation is included in the response
                if "citation" not in result:
                    result["citation"] = citation
                return jsonify(result)

    except Exception as e:
        error_msg = f"Unexpected error in verify_citation: {str(e)}"
        current_app.logger.error(f"[verify_citation] {error_msg}", exc_info=True)
        
        # Include traceback in development
        error_response = {
            **default_error_response,
            "error": error_msg,
            "traceback": traceback.format_exc() if current_app.debug else None
        }
        
        # The CORS headers will be added by the @after_this_request decorator
        return jsonify(error_response), 500


# API endpoint for sending feedback
@vue_api.route("/send-feedback", methods=["POST"])
def send_feedback():
    """
    API endpoint to handle feedback submission.
    Sends an email to the configured admin email.
    """
    try:
        # Get feedback data from the request
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"success": False, "error": "Message is required"}), 400

        message = data["message"]
        page = data.get("page", "Unknown page")
        user_agent = data.get("userAgent", "Unknown browser")

        # Prepare email content
        subject = f"CaseStrainer Feedback from {page}"
        email_body = f"""
        <h2>New feedback from CaseStrainer</h2>
        <p><strong>Page:</strong> {page}</p>
        <p><strong>User Agent:</strong> {user_agent}</p>
        <p><strong>Message:</strong></p>
        <div style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
        {message}
        </div>
        """

        # Log the feedback
        logger.info(f"Sending feedback from {page} with message: {message[:100]}...")

        # Ensure we're in an application context
        from flask import current_app

        with current_app.app_context():
            # Initialize mail (this should ideally be done in app setup)
            mail = Mail(current_app)
            
            # Send email
            msg = Message(
                subject=subject,
                recipients=[current_app.config.get("MAIL_RECIPIENT", "admin@example.com")],
                html=email_body,
                sender=current_app.config.get(
                    "MAIL_DEFAULT_SENDER", "noreply@example.com"
                ),
            )

            mail.send(msg)
            logger.info("Feedback email sent successfully")

        return jsonify(
            {
                "success": True,
                "message": "Thank you for your feedback! We will get back to you soon.",
            }
        )

    except Exception as e:
        error_msg = f"Error sending feedback email: {str(e)}"
        logger.error(error_msg)
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Failed to send feedback. Please try again later.",
                }
            ),
            500,
        )


def get_db_connection():
    """Helper function to get a database connection."""
    # Add your database connection logic here
    pass


def import_ml_classifier():
    """Helper function to import the ML classifier if available."""
    try:
        from ml_classifier import (  # type: ignore
            CitationClassifier,
        )  # Optional import, may not be available in all environments

        return CitationClassifier()
    except ImportError:
        return None


def get_case_metadata(citation):
    """
    Enhanced function to get case metadata from various sources.
    Returns a dictionary with case metadata.
    """
    metadata = {
        "citation": citation,
        "case_name": "",
        "court": "",
        "date_decided": "",
        "docket_number": "",
        "jurisdiction": "federal",  # Default to federal
        "reporter": "",
        "volume": "",
        "page": "",
        "year": "",
        "url": "",
        "sources": [],
    }

    try:
        # Extract basic components from citation
        import re

        match = re.match(r"(\d+)\s+([A-Za-z0-9\.]+)\s+(\d+)", citation)
        if match:
            metadata["volume"], metadata["reporter"], metadata["page"] = match.groups()

        # Try to extract year from reporter (common formats like F.3d, F.Supp.2d, etc.)
        year_match = re.search(r"(\d{4})", citation)
        if year_match:
            metadata["year"] = year_match.group(1)

        # Determine court based on reporter
        if "F.3d" in citation or "F.2d" in citation or "F.Supp" in citation:
            metadata["court"] = "U.S. Court of Appeals"
            metadata["jurisdiction"] = "federal"
        elif "U.S." in citation:
            metadata["court"] = "U.S. Supreme Court"
            metadata["jurisdiction"] = "federal"

        # Try to get case name from database if available
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT case_name, court, docket_number, date_decided FROM citations WHERE citation_text = ?",
            (citation,),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            db_case_name, db_court, db_docket, db_date = result
            metadata.update(
                {
                    "case_name": db_case_name or metadata["case_name"],
                    "court": db_court or metadata["court"],
                    "docket_number": db_docket or metadata["docket_number"],
                    "date_decided": db_date or metadata["date_decided"],
                    "sources": metadata["sources"] + ["database"],
                }
            )

        # Add timestamp
        metadata["retrieved_at"] = datetime.now(timezone.utc).isoformat()

        return metadata

    except Exception as e:
        logger.warning(f"Error getting case metadata: {str(e)}")
        return metadata


# API endpoint for document analysis
@vue_api.route('/analyze-document', methods=['POST', 'OPTIONS'])
def analyze_document():
    """Analyze a document for citations."""
    logger.info("Starting document analysis")
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST')
            return response

        # Log request details
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Request files: {list(request.files.keys())}")
        logger.debug(f"Request form: {list(request.form.keys())}")

        # Initialize request data
        request_data = {}
        file = None
        text = None

        # Check for file upload
        if 'file' in request.files:
            file = request.files['file']
            logger.info(f"Received file: {file.filename}")
            
            if not file or not file.filename:
                logger.error("No file provided in request")
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided',
                    'code': 'NO_FILE'
                }), 400

            # Read file content
            file_content = file.read()
            if not file_content:
                logger.error("Empty file received")
                return jsonify({
                    'status': 'error',
                    'message': 'Empty file',
                    'code': 'EMPTY_FILE'
                }), 400

            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(current_app.root_path, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            logger.debug(f"Using temp directory: {temp_dir}")

            # Save file with secure filename
            filename = secure_filename(file.filename)
            temp_file_path = os.path.join(temp_dir, filename)
            
            try:
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content)
                logger.info(f"Saved uploaded file to: {temp_file_path}")

                # Initialize PDF handler with pdfminer as primary method
                handler = PDFHandler(PDFExtractionConfig(
                    preferred_method=PDFExtractionMethod.PDFMINER,
                    use_fallback=True,
                    timeout=30,
                    clean_text=True,
                    debug=True  # Enable debug logging
                ))

                # Extract text from file
                logger.info("Starting text extraction from PDF")
                text = handler.extract_text(temp_file_path)
                if text.startswith("Error:"):
                    logger.error(f"Text extraction failed: {text}")
                    return jsonify({
                        'status': 'error',
                        'message': text,
                        'code': 'TEXT_EXTRACTION_ERROR'
                    }), 500

                logger.info(f"Successfully extracted {len(text)} characters from file")
                logger.debug(f"Sample of extracted text: {text[:500]}...")

            except Exception as e:
                logger.error(f"Error processing file: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': f'Error processing file: {str(e)}',
                    'code': 'FILE_PROCESSING_ERROR'
                }), 500

            finally:
                # Clean up temp file
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Error cleaning up temporary file: {str(e)}")

        # Process the extracted text for citations
        if text:
            try:
                logger.info("Starting citation extraction")
                logger.info(f"Extracted text length: {len(text)} characters")
                logger.info("First 1000 characters of extracted text:")
                logger.info("-" * 80)
                logger.info(text[:1000])
                logger.info("-" * 80)
                
                # Extract citations from the text
                logger.info("Calling extract_citations_from_text...")
                citations = extract_citations_from_text(text)
                logger.info(f"Raw citations found: {citations}")
                
                if not citations:
                    logger.warning("No citations found in document")
                    # Try to find the specific citation we're looking for
                    if "534 F.3d 1290" in text:
                        logger.info("Found '534 F.3d 1290' in text but citation extractor missed it")
                    return jsonify({
                        'status': 'Invalid',
                        'message': 'No citations found in document',
                        'citations': [],
                        'metadata': {
                            'analysis_id': '',
                            'file_name': filename if file else 'unknown',
                            'statistics': {
                                'total_citations': 0,
                                'verified_citations': 0
                            }
                        }
                    }), 200

                # Process and validate citations
                logger.info("Processing and validating citations")
                processed_citations = []
                for citation in citations:
                    citation_text = citation.get('citation_text', '')
                    if citation_text:
                        logger.debug(f"Processing citation: {citation_text}")
                        # Validate the citation
                        validation_result = enhanced_validate_citation(
                            citation_text=citation_text,
                            request_data=request_data
                        )
                        processed_citations.append({
                            'citation': citation_text,
                            'status': validation_result.get('status', 'Invalid'),
                            'details': validation_result.get('details', {})
                        })

                # Return the results
                logger.info(f"Analysis complete. Found {len(processed_citations)} citations")
                return jsonify({
                    'status': 'success',
                    'message': 'Document analyzed successfully',
                    'citations': processed_citations,
                    'metadata': {
                        'analysis_id': '',
                        'file_name': filename if file else 'unknown',
                        'statistics': {
                            'total_citations': len(processed_citations),
                            'verified_citations': sum(1 for c in processed_citations if c['status'] == 'Valid')
                        }
                    }
                }), 200

            except Exception as e:
                logger.error(f"Error processing citations: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': f'Error processing citations: {str(e)}',
                    'code': 'CITATION_PROCESSING_ERROR'
                }), 500

        logger.error("No text content provided for analysis")
        return jsonify({
            'status': 'error',
            'message': 'No text content provided for analysis',
            'code': 'NO_TEXT_CONTENT'
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error in analyze_document: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
            'code': 'UNEXPECTED_ERROR'
        }), 500


# API endpoint for citation context
@vue_api.route("/citation-context", methods=["GET"])
def get_citation_context():
    """
    Enhanced API endpoint to get comprehensive context around a citation.
    Returns detailed metadata, context, and classification.
    """
    try:
        # Get the citation from the request
        data = request.get_json(silent=True) or {}
        citation = data.get("citation", request.args.get("citation", "")).strip()
        case_name = data.get("case_name", request.args.get("case_name", "")).strip()

        if not citation:
            return (
                jsonify(
                    {"status": "error", "error": "No citation provided", "code": 400}
                ),
                400,
            )

        # Get enhanced metadata
        metadata = get_case_metadata(citation)

        # If we have a case name from the request, use it
        if case_name and not metadata.get("case_name"):
            metadata["case_name"] = case_name

        # Get classification
        classification = {}
        try:
            classifier = import_ml_classifier()
            if classifier:
                classification = classifier.classify(citation)
                metadata["sources"].append("ml_classifier")
        except Exception as e:
            logger.warning(f"Classification failed: {str(e)}")

        # Get context from database
        context = ""
        file_link = ""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT context, file_link FROM citations WHERE citation_text = ?",
                (citation,),
            )
            result = cursor.fetchone()
            if result:
                context, file_link = result or ("", "")
                metadata["sources"].append("database")
            conn.close()
        except Exception as e:
            logger.warning(f"Database query failed: {str(e)}")

        # Build response
        response = jsonify({
            "status": "success",
            "citation": citation,
            "metadata": metadata,
            "context": context,
            "file_link": file_link,
            "classification": classification,
            "sources": list(set(metadata.get("sources", []))),  # Remove duplicates
        })
        
        # The CORS headers will be added by the @after_this_request decorator
        return response, 200

    except Exception as e:
        logger.error(f"Error in get_citation_context: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "code": 500,
                    "citation": citation if "citation" in locals() else "",
                    "case_name": case_name if "case_name" in locals() else "",
                }
            ),
            500,
        )

def clean_extracted_text(text):
    """Clean extracted text by removing extra whitespace and normalizing line endings."""
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove any non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char.isspace())
    return text.strip()
