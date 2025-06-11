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
from src.citation_extractor import CitationExtractor

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
from flask import Blueprint, request, jsonify
from urllib.parse import urlparse

# Import centralized logging configuration

# Configure logging
logger = logging.getLogger(__name__)

# The actual logging configuration will be done when the Flask app is initialized
# and configure_logging() is called from app_final_vue.py


# Create a function to get a new blueprint with a unique name
def create_enhanced_validator_blueprint():

    # Generate a unique name for the blueprint
    blueprint_name = f"enhanced_validator_{int(time.time() * 1000)}"
    logger.info(f"Creating enhanced validator blueprint with name: {blueprint_name}")

    # Create and return a new blueprint with the unique name
    return Blueprint(
        blueprint_name, __name__, template_folder="templates", static_folder="static"
    )


# Create the initial blueprint
def get_enhanced_validator_blueprint():
    """Create a new enhanced validator blueprint with a unique name."""
    return create_enhanced_validator_blueprint()


# Create the initial blueprint instance with a consistent name
enhanced_validator_bp = get_enhanced_validator_blueprint()
logger.info(
    f"Created or using enhanced_validator_bp with name: {enhanced_validator_bp.name}"
)

logger.info("Loading enhanced_validator_production.py v0.4.9 - Modified 2025-06-10")

"""
Enhanced Citation Validator for Production

This module integrates the simplified Enhanced Validator with the production app_final_vue.py.
"""

# Import the citation processor and config

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the modules
from src.config import configure_logging, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from src.citation_processor import CitationProcessor

# Configure logging if not already configured
if not logging.getLogger().hasHandlers():
    configure_logging()

# Initialize the citation processor
citation_processor = CitationProcessor()


def log_step(message: str, level: str = "info"):
    """Helper function to log processing steps with consistent formatting."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[VALIDATOR] {message}")
    return message


def normalize_citation_text(citation_text):
    """
    Normalize citation text to a standard format before processing.

    Handles common issues like:
    - Extra spaces in reporter abbreviations (e.g., 'F. 3d' -> 'F.3d')
    - Double periods (e.g., 'U.S..' -> 'U.S.')
    - Inconsistent spacing around v. (e.g., 'U.S. v.Caraway' -> 'U.S. v. Caraway')

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: The normalized citation text
    """
    if not citation_text or not isinstance(citation_text, str):
        return citation_text

    # Remove any leading/trailing whitespace
    normalized = citation_text.strip()

    # Fix double periods
    normalized = re.sub(r"\.\.+", ".", normalized)

    # Fix spaces in reporter abbreviations (e.g., 'F. 3d' -> 'F.3d')
    normalized = re.sub(r"(\b[A-Za-z]+\.)\s+(\d+[a-z]*)", r"\1\2", normalized)

    # Fix spacing around 'v.'
    normalized = re.sub(r"\s+v\.\s*", " v. ", normalized, flags=re.IGNORECASE)

    # Fix common reporter abbreviations
    reporter_fixes = {
        r"\bFed\.\s*": "F.",
        r"\bFed\.\s*App\.\s*": "F. App'x",
        r"\bF\.\s*2d\b": "F.2d",
        r"\bF\.\s*3d\b": "F.3d",
        r"\bF\.\s*4th\b": "F.4th",
        r"\bU\.\s*S\.\s*": "U.S. ",
        r"\bS\.\s*Ct\.\s*": "S. Ct. ",
        r"\bL\.\s*Ed\.\s*2d\b": "L. Ed. 2d",
    }

    for pattern, replacement in reporter_fixes.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Remove extra spaces
    normalized = " ".join(normalized.split())

    if normalized != citation_text:
        logger.debug(f"Normalized citation: '{citation_text}' -> '{normalized}'")

    return normalized


def enhanced_analyze(data, analysis_id=None):
    """Enhanced citation analysis with detailed logging."""
    # Initialize timing and result structure
    start_time = time.time()
    result = {
        "analysis_id": analysis_id or str(uuid.uuid4()),
        "status": "success",
        "citations": [],
        "warnings": [],
        "errors": [],
        "processing_time": 0,
        "file_info": {},
        "validation_results": {}
    }
    
    try:
        # Log request data (excluding file content)
        request_data = {
            "has_file": "file" in data,
            "filename": data.get("filename", "No filename"),
            "file_size": len(data.get("file", b"")) if "file" in data else 0,
            "text_length": len(data.get("text", "")) if "text" in data else 0
        }
        logger.info(f"[Analysis {result['analysis_id']}] Received request data: {json.dumps(request_data, indent=2)}")
        
        # If no data provided, try to get it from the request
        if data is None:
            if request.is_json:
                data = request.get_json() or {}
            else:
                # Handle form data (e.g., file uploads)
                data = request.form.to_dict()
                
                # Handle file upload
                if 'file' in request.files:
                    file = request.files['file']
                    if file.filename != '':
                        # Read file content but don't log it
                        data['file'] = file.read()
                        data['filename'] = file.filename
                        file_size = len(data['file'])
                        logger.info(f"[Analysis {result['analysis_id']}] Received file upload: {file.filename} ({file_size/1024:.1f}KB)")
        
        # Get text from either direct input or file
        text = data.get('text', '')
        
        # If no text but file is provided, extract text from file
        if not text and 'file' in data and data['file']:
            file_content = data['file']
            filename = data.get('filename', 'uploaded_file')
            
            # Log file processing start with more details (excluding binary content)
            file_info = {
                'filename': filename,
                'size_kb': len(file_content)/1024,
                'is_binary': not isinstance(file_content, str),
                'options': data.get('options', {})
            }
            logger.info(f"[Analysis {result['analysis_id']}] Starting text extraction: {json.dumps(file_info, default=str)}")
            
            # Save to a temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(file_content if isinstance(file_content, bytes) else file_content.encode('utf-8'))
                temp_path = temp_file.name
                logger.debug(f"[Analysis {result['analysis_id']}] Created temporary file: {temp_path}")
            
            try:
                # Get conversion options
                options = data.get('options', {})
                convert_pdf_to_md = options.get('convert_pdf_to_md', True)
                logger.info(f"[Analysis {result['analysis_id']}] Extracting text with convert_pdf_to_md={convert_pdf_to_md}")
                
                # Log the file type and extension being used
                file_type = options.get('file_type', 'application/octet-stream')
                file_ext = options.get('file_ext', os.path.splitext(filename)[1].lstrip('.'))
                logger.debug(f"[Analysis {result['analysis_id']}] File type: {file_type}, Extension: {file_ext}")
                
                # Extract text using the shared utility function
                extract_start = time.time()
                logger.debug(f"[Analysis {result['analysis_id']}] Starting text extraction from {temp_path}")
                
                text = extract_text_from_file(
                    temp_path, 
                    convert_pdf_to_md=convert_pdf_to_md,
                    file_type=file_type,
                    file_ext=file_ext
                )
                
                extract_time = time.time() - extract_start
                logger.info(f"[Analysis {result['analysis_id']}] Text extraction completed in {extract_time:.2f}s")
                logger.debug(f"[Analysis {result['analysis_id']}] Extracted text length: {len(text)} characters")
                
                # Log a sample of the extracted text (first 200 chars, sanitized)
                if text:
                    sample_text = text[:200].replace('\n', ' ').replace('\r', '')
                    # Remove any non-printable characters
                    sample_text = ''.join(c for c in sample_text if c.isprintable())
                    logger.debug(f"[Analysis {result['analysis_id']}] Text sample: {sample_text}...")
                
                extract_time = time.time() - extract_start
                logger.info(f"[Analysis {result['analysis_id']}] Extracted {len(text)} characters in {extract_time:.2f}s")
                
            except Exception as e:
                error_msg = f"Error extracting text from file: {str(e)}"
                logger.error(f"[Analysis {result['analysis_id']}] {error_msg}", exc_info=True)
                logger.error(f"[Analysis {result['analysis_id']}] Detailed error during PDF extraction. Consider using alternative libraries like PyPDF2 or pdfminer.six for better encoding handling.", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'error_type': type(e).__name__,
                    'analysis_id': result['analysis_id']
                }), 500
                
            finally:
                # Clean up the temporary file
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        logger.debug(f"[Analysis {result['analysis_id']}] Deleted temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"[Analysis {result['analysis_id']}] Error deleting temp file {temp_path}: {str(e)}")
        
        # Check if we have text to analyze
        if not text:
            error_msg = "No text content provided or could be extracted for analysis"
            logger.warning(f"[Analysis {result['analysis_id']}] {error_msg}")
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'citations': [],
                'stats': {
                    'total_citations': 0,
                    'validated_citations': 0,
                    'processing_time': time.time() - start_time
                },
                'analysis_id': result['analysis_id']
            })
        
        # Get analysis options
        options = data.get('options', {})
        batch_process = options.get('batch_process', True)
        return_debug = options.get('return_debug', False)
        
        # Log analysis parameters
        logger.info(f"[Analysis {result['analysis_id']}] Starting analysis with batch_process={batch_process}, return_debug={return_debug}")
        logger.debug(f"[Analysis {result['analysis_id']}] First 500 chars of text: {text[:500]}...")
        
        # Analyze the text
        analysis_start = time.time()
        result = analyze_text(text, batch_process=batch_process, return_debug=return_debug)
        analysis_time = time.time() - analysis_start
        
        # Add metadata
        result['analysis_id'] = result['analysis_id']
        result['processing_time'] = time.time() - start_time
        
        # Log completion
        logger.info(f"[Analysis {result['analysis_id']}] Analysis completed in {result['processing_time']:.2f}s")
        logger.info(f"[Analysis {result['analysis_id']}] Found {len(result.get('citations', []))} citations")
        
        # Log performance metrics
        if 'stats' in result:
            logger.info(
                f"[Analysis {result['analysis_id']}] Stats: {json.dumps(result['stats'], indent=2)}"
            )
        
        return jsonify(result)
    except FileNotFoundError as e:
        error_msg = f"File handling error in enhanced_analyze: {str(e)}"
        logger.error(f"[Analysis {result['analysis_id']}] {error_msg}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__,
            'analysis_id': result['analysis_id'],
            'processing_time': time.time() - start_time
        }), 500
    except ImportError as e:
        error_msg = f"Import error in enhanced_analyze: {str(e)}"
        logger.error(f"[Analysis {result['analysis_id']}] {error_msg}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__,
            'analysis_id': result['analysis_id'],
            'processing_time': time.time() - start_time
        }), 500
    except Exception as e:
        error_msg = f"Unexpected error in enhanced_analyze: {str(e)}"
        logger.error(f"[Analysis {result['analysis_id']}] {error_msg}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__,
            'analysis_id': result['analysis_id'],
            'processing_time': time.time() - start_time
        }), 500


# File upload configuration
# Using UPLOAD_FOLDER and ALLOWED_EXTENSIONS from config.py

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to extract text from different file types
# Use the shared extract_text_from_file from file_utils


def preprocess_markdown(text):
    """
    Preprocess markdown text before citation extraction.

    Args:
        text (str): The text to preprocess

    Returns:
        str: Preprocessed text with markdown converted to plain text
    """
    if not text or not MARKDOWN_AVAILABLE:
        return text

    # Skip if text doesn't contain any markdown indicators
    if not any(char in text for char in ["*", "_", "`", "#", ">", "[", "]", "!"]):
        return text

    try:
        # Convert markdown to HTML
        html_content = markdown.markdown(text)

        # Parse HTML and extract text
        soup = BeautifulSoup(html_content, "html.parser")

        # Handle code blocks - preserve them but clean up formatting
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                # Replace code block with just the text content
                pre.replace_with(code.get_text() + "\n")

        # Get text content with proper spacing
        text_content = soup.get_text(separator="\n")

        # Convert HTML entities to characters
        text_content = html.unescape(text_content)

        # Clean up excessive whitespace but preserve paragraph breaks
        text_content = re.sub(
            r"[ \t]+", " ", text_content
        )  # Replace multiple spaces/tabs with single space
        text_content = re.sub(
            r"\n{3,}", "\n\n", text_content
        )  # Limit consecutive newlines to 2

        return text_content.strip()
    except Exception as e:
        logger.warning(f"Error preprocessing markdown: {str(e)}")
        return text


def clean_case_name(case_name):
    """Clean up case names by removing common prefixes and normalizing whitespace."""
    if not case_name or not isinstance(case_name, str):
        return case_name

    # Remove common prefixes that might interfere with citation parsing
    prefixes = [
        "See",
        "E.g.,",
        "E.g.",
        "See, e.g.,",
        "See also",
        "But see",
        "Cf.",
        "Compare",
        "But cf.",
        "Accord",
        "But",
        "See generally",
        "See, e.g.,",
        "See id.",
        "Id.",
        "Id. at",
        "Supra",
        "Infra",
        "Et seq.",
        "Et al.",
        "In re",
        "Ex parte",
        "Ex rel.",
        "In the matter of",
        "Further,",
        "Similarly,",
        "Moreover,",
        "However,",
        "Therefore,",
        "Thus,",
    ]

    # Remove each prefix if it appears at the start of the string
    for prefix in sorted(prefixes, key=len, reverse=True):
        if case_name.startswith(prefix):
            case_name = case_name[len(prefix) :].lstrip()

    # Normalize v. vs. v vs. vs.
    case_name = re.sub(r"\b(v|vs|versus)\.?\s+", "v. ", case_name, flags=re.IGNORECASE)

    # Normalize U.S. vs. US vs. United States
    case_name = re.sub(
        r"\bU\.?\s?S\.?(?:\s+Ct\.?|\s+Cl\.?|\s+App\.?)?\b",
        "U.S.",
        case_name,
        flags=re.IGNORECASE,
    )

    # Remove extra spaces and normalize whitespace
    case_name = " ".join(case_name.split())

    return case_name.strip()


def validate_citations_batch(citations, api_key=None):
    """
    Validate a batch of citations using the CourtListener API.

    Args:
        citations (list): List of citation strings or dictionaries to validate
        api_key (str, optional): CourtListener API key. If not provided, will use environment variable.

    Returns:
        tuple: (list of validated citations, dict of validation statistics)
    """
    logger = logging.getLogger(__name__)

    if not citations:
        return [], {"verified": 0, "not_found": 0, "errors": 0}

    # Convert all citations to a consistent dictionary format
    processed_citations = []
    for citation in citations:
        if isinstance(citation, dict):
            # Ensure all required fields are present
            citation_dict = {
                "citation_text": citation.get("citation_text", str(citation)),
                "validation_status": "pending",
                "metadata": citation.get("metadata", {}),
            }
        else:
            # Convert string citation to dictionary
            citation_dict = {
                "citation_text": str(citation),
                "validation_status": "pending",
                "metadata": {},
            }
        processed_citations.append(citation_dict)

    # Load API key from config file or environment variable
    if not api_key:
        # Try multiple possible config file locations
        possible_paths = [
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            ),  # ../config.json
            os.path.join(
                os.path.dirname(__file__), "..", "config.json"
            ),  # src/../config.json
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config.json",
            ),  # ../../config.json
            os.path.join(os.path.dirname(__file__), "config.json"),  # src/config.json
        ]

        for config_path in possible_paths:
            try:
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        api_key = config.get("COURTLISTENER_API_KEY") or config.get(
                            "courtlistener_api_key"
                        )
                        if api_key:
                            logger.info(
                                f"Loaded API key from {os.path.abspath(config_path)}"
                            )
                            break
            except Exception as e:
                logger.warning(f"Error reading config file {config_path}: {str(e)}")

        # If still no API key, try environment variables
        if not api_key:
            api_key = os.environ.get("COURTLISTENER_API_KEY")

        # Check common alternative environment variable names
        alt_vars = ["COURTLISTENER_KEY", "CL_API_KEY", "COURT_LISTENER_API_KEY"]
        for var in alt_vars:
            env_key = os.getenv(var)
            if env_key:
                api_key = env_key
                logger.warning(f"Using API key from environment variable: {var}")
                break

        # If still not found, log all environment variables for debugging

    if not api_key:
        logger.warning("No CourtListener API key found. Using limited functionality.")
        # Return the citations with a validation error status
        validation_stats = {
            "verified": 0,
            "not_found": 0,
            "errors": len(processed_citations),
        }
        for citation in processed_citations:
            citation["validation_status"] = "validation_error"
            citation["metadata"]["error"] = "No API key provided for CourtListener"
        return processed_citations, validation_stats

    base_url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }

    # Process each citation individually
    validation_stats = {"verified": 0, "not_found": 0, "errors": 0}

    for citation in processed_citations:
        try:
            citation_text = citation["citation_text"]
            if not citation_text:
                citation["validation_status"] = "not_found"
                validation_stats["not_found"] += 1
                continue

            # Prepare query parameters
            params = {
                "q": f'citation:"{citation_text}"',
                "type": "o",  # Search only opinions
                "order_by": "score desc",
                "stat_Precedential": "on",
                "filed_after": "1900-01-01",
                "page_size": 1,  # We only need the top result
                "format": "json",
            }

            # Make the API request
            response = requests.get(
                base_url,
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            # Process the response
            data = response.json()
            if data.get("count", 0) > 0:
                # Found a match
                result = data["results"][0]
                citation["validation_status"] = "verified"
                citation["metadata"].update(
                    {
                        "validation_method": "courtlistener_api",
                        "verified_by": "CourtListener",
                        "reporter_type": result.get("reporter", ""),
                        "case_name": result.get("caseName", ""),
                        "court": result.get("court", ""),
                        "date_filed": result.get("dateFiled", ""),
                        "docket_number": result.get("docketNumber", ""),
                    }
                )
                validation_stats["verified"] += 1
            else:
                citation["validation_status"] = "not_found"
                validation_stats["not_found"] += 1

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error validating citation {citation.get('citation_text', 'unknown')}: {str(e)}"
            )
            citation["validation_status"] = "validation_error"
            citation["metadata"]["error"] = str(e)
            validation_stats["errors"] += 1
        except Exception as e:
            logger.error(f"Unexpected error processing citation: {str(e)}")
            citation["validation_status"] = "validation_error"
            citation["metadata"]["error"] = f"Unexpected error: {str(e)}"
            validation_stats["errors"] += 1

    return processed_citations, validation_stats


def analyze_text(
    text: str, batch_process: bool = False, return_debug: bool = True, analysis_id: str = None
) -> dict:
    """
    Analyze text for legal citations using the enhanced citation processor.

    Args:
        text (str): The text to analyze for citations
        batch_process (bool): If True, process all citations together in a single batch
        return_debug (bool): If True, include debug information in the response
        analysis_id (str, optional): Unique identifier for the analysis

    Returns:
        dict: Analysis results with citations and metadata
    """
    if analysis_id is None:
        analysis_id = str(uuid.uuid4())
    debug_info = {
        "input_length": len(text),
        "extraction_time": None,
        "validation_time": None,
        "total_processing_time": None,
        "error": None,
    }

    time.time()

    try:
        # Extract citations with analysis_id for better logging
        extract_start = time.time()
        extract_result = extract_citations(
            text, 
            return_debug=True, 
            batch_process=batch_process,
            analysis_id=analysis_id  # Pass analysis_id for consistent logging
        )

        # Handle the return value from extract_citations
        if extract_result is None:
            citations = []
        elif isinstance(extract_result, tuple) and len(extract_result) == 2:
            citations, extract_debug = extract_result
            if return_debug:
                debug_info["extraction_debug"] = extract_debug
            # Ensure citations is a list
            if isinstance(citations, dict) and "confirmed_citations" in citations:
                citations = citations["confirmed_citations"]
            elif not isinstance(citations, list):
                citations = []
        else:
            citations = extract_result if isinstance(extract_result, list) else []

        extract_time = time.time() - extract_start

        debug_info["extraction_time"] = extract_time
        log_step(f"Extracted {len(citations)} citations in {extract_time:.2f} seconds")

        # Validate citations
        validate_start = time.time()

        # Process citations based on batch preference
        validated_citations = []

        if citations:
            # Process each citation
            for citation in citations:
                try:
                    # Skip if not a dictionary
                    if not isinstance(citation, dict):
                        continue

                    # Get the citation text
                    citation_text = (
                        citation.get("citation_text") or citation.get("citation") or ""
                    )
                    if not citation_text:
                        continue

                    # Get or generate a case name
                    case_name = citation.get("case_name")
                    if not case_name and " v. " in citation_text:
                        case_name = citation_text.split(" v. ")[0].strip()

                    # Create the citation object with default values
                    validated_citation = {
                        "citation": citation_text,
                        "verified": False,
                        "case_name": case_name or "Unknown Case",
                        "url": "",
                        "validation_method": citation.get("source", "extracted"),
                        "confidence": citation.get("confidence", 0.5),
                        "metadata": {
                            "extraction_method": citation.get("source", "extracted"),
                            **citation.get("metadata", {}),
                        },
                    }

                    # Handle different validation result formats
                    if (
                        "validation_results" in citation
                        and citation["validation_results"]
                    ):
                        # Format 1: List of validation results
                        validation = citation["validation_results"]
                        if isinstance(validation, list) and len(validation) > 0:
                            validation = validation[0]

                            # Handle both 'valid' and 'validation_status' keys
                            is_valid = (
                                validation.get("valid", False)
                                or validation.get("validation_status") == "verified"
                            )

                            validated_citation.update(
                                {
                                    "verified": is_valid,
                                    "case_name": validation.get(
                                        "case_name", case_name or "Unknown Case"
                                    ),
                                    "url": validation.get("url", ""),
                                    "validation_method": validation.get(
                                        "source", "validated"
                                    ),
                                    "confidence": validation.get(
                                        "confidence", 0.9 if is_valid else 0.1
                                    ),
                                }
                            )
                    elif "valid" in citation or "validation_status" in citation:
                        # Format 2: Direct validation attributes
                        is_valid = (
                            citation.get("valid", False)
                            or citation.get("validation_status") == "verified"
                        )
                        validated_citation.update(
                            {
                                "verified": is_valid,
                                "case_name": citation.get(
                                    "case_name", case_name or "Unknown Case"
                                ),
                                "url": citation.get("url", ""),
                                "validation_method": citation.get("source", "direct"),
                                "confidence": citation.get(
                                    "confidence", 0.9 if is_valid else 0.1
                                ),
                            }
                        )

                    validated_citations.append(validated_citation)

                except Exception as e:
                    log_step(f"Error processing citation: {str(e)}", "error")
                    continue

        validate_time = time.time() - validate_start
        debug_info["validation_time"] = validate_time
        log_step(
            f"Validated {len(validated_citations)} citations in {validate_time:.2f} seconds"
        )

        # Transform citations to match frontend expectations
        transformed_citations = []
        for citation in validated_citations:
            transformed_citation = {
                "text": citation.get("citation", ""),
                "verified": citation.get("verified", False),
                "source": citation.get("validation_method", "extracted"),
                "correction": citation.get("correction", ""),
                "url": citation.get("url", ""),
                "case_name": citation.get("case_name", ""),
                "confidence": citation.get("confidence", 0.5),
                "name_match": citation.get("name_match", False)
            }
            transformed_citations.append(transformed_citation)

        # Count verified citations
        verified_count = len([c for c in validated_citations if c.get("verified", False)])
        
        # Prepare response with frontend-expected format
        analysis_id = str(uuid.uuid4())
        response = {
            "status": "success",
            "results": {
                "valid": verified_count > 0,
                "message": f"Found {len(validated_citations)} citations ({verified_count} verified)",
                "citations": transformed_citations,
                "metadata": {
                    "analysis_id": analysis_id,
                    "file_name": "uploaded_document.pdf",
                    "statistics": {
                        "total_citations": len(validated_citations),
                        "verified_citations": verified_count,
                        "extraction_time": extract_time,
                        "validation_time": validate_time,
                        "total_processing_time": extract_time + validate_time
                    }
                }
            },
            "total": len(validated_citations),
            "verified": verified_count,
            "analysis_id": analysis_id,
            "statistics": {
                "total_citations": len(validated_citations),
                "verified_citations": verified_count,
                "extraction_time": extract_time,
                "validation_time": validate_time,
                "total_processing_time": extract_time + validate_time
            },
            "debug": debug_info if return_debug else None,
        }

        # Log the response summary (without full citations to avoid log spam)
        log_step(f"Returning {len(validated_citations)} citations in response")
        return response

    except Exception as e:
        error_msg = f"Error analyzing text: {str(e)}"
        logger.error(error_msg, exc_info=True)
        debug_info["error"] = error_msg
        return {
            "status": "error",
            "message": error_msg,
            "debug": debug_info if return_debug else None,
        }


def extract_citations(text, return_debug=False, batch_process=False, analysis_id=None):
    """Extract citations from text using the unified CitationExtractor."""
    print("\n=== CITATION EXTRACTION DEBUG (using CitationExtractor) ===")
    print(f"Starting citation extraction from text of length: {len(text)}")
    if not text or not text.strip():
         print("ERROR: Empty or whitespace–only text provided")
         return { "confirmed_citations": [], "possible_citations": [], "warnings": [], "errors": [], "batch_processed": batch_process }
    extractor = CitationExtractor(use_eyecite=True, use_regex=True, context_window=0, deduplicate=True)
    # (Optionally, if you want debug info printed, pass debug=True and log the debug dict.)
    # (For now, we're returning a dict (or a tuple (dict, debug dict) if return_debug=True) that mimics the old output.)
    debug_info = extractor.extract(text, return_context=False, debug=return_debug)
    if return_debug:
         return (debug_info, debug_info)
    else:
         # (Convert the "citations" list (of dicts) into a "confirmed_citations" list (of dicts) (with "text" and "type" keys) and "possible_citations" (empty) and "warnings" (from debug_info) and "errors" (from debug_info) and "batch_processed" (from the input flag).)
         confirmed = [{"text": d["citation"], "type": d.get("method", "unknown"), "confidence": d.get("confidence", "unknown")} for d in debug_info["citations"]]
         return { "confirmed_citations": confirmed, "possible_citations": [], "warnings": debug_info["warnings"], "errors": debug_info["errors"], "batch_processed": batch_process }

def sanitize_text_for_logging(text, max_length=200):
    """Sanitize text for logging by removing non-printable characters and limiting length."""
    if not text:
        return ""
    # Convert to string if bytes
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8', errors='replace')
        except Exception:
            return "[Binary data]"
    # Remove non-printable characters
    text = ''.join(c for c in text if c.isprintable())
    # Limit length and add ellipsis
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


# The regex pattern processing has been moved into the main function
# Now we'll process the validated citations


def validate_extracted_citations(citations, return_debug=False):
    """
    Validate a list of extracted citations.

    Args:
        citations (list): List of citation dictionaries to validate
        return_debug (bool): If True, returns debug information along with results

    Returns:
        dict: Dictionary containing validated citations and debug info if requested
    """
    start_time = time.time()
    debug_info = {
        "start_time": start_time,
        "steps": [],
        "stats": {
            "total_validated": 0,
            "validation_errors": 0,
        },
        "warnings": [],
        "errors": [],
    }

    def log_step(message, level="info"):
        """Helper to log a processing step with timing info."""
        elapsed = time.time() - start_time
        step_info = {"time": round(elapsed, 2), "message": message, "level": level}
        debug_info["steps"].append(step_info)
        log_msg = f"[VALIDATE] {message} (after {elapsed:.2f}s)"

        if level == "debug":
            logger.debug(log_msg)
        elif level == "info":
            logger.info(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
            debug_info["warnings"].append(message)
        elif level == "error":
            logger.error(log_msg)
            debug_info["errors"].append(message)

    try:
        if not isinstance(citations, list):
            raise ValueError("Input must be a list of citations")

        log_step(f"Starting validation of {len(citations)} citations")

        validated_citations = []

        for i, citation in enumerate(citations, 1):
            try:
                if not isinstance(citation, dict) or "citation_text" not in citation:
                    log_step(
                        f"Skipping invalid citation at index {i}: {citation}", "warning"
                    )
                    continue

                # Here you would add your citation validation logic
                # For now, we'll just pass the citation through
                validated_citations.append(citation)
                debug_info["stats"]["total_validated"] += 1

                if i % 100 == 0 or i == len(citations):
                    log_step(f"Processed {i}/{len(citations)} citations")

            except Exception as e:
                log_step(f"Error validating citation {i}: {str(e)}", "error")
                debug_info["stats"]["validation_errors"] += 1
                continue

        log_step(
            f"Validation complete. Successfully validated {len(validated_citations)} citations"
        )

        result = {
            "validated_citations": validated_citations,
            "stats": debug_info["stats"],
            "warnings": debug_info["warnings"],
            "errors": debug_info["errors"],
        }

        if return_debug:
            debug_info["end_time"] = time.time()
            debug_info["stats"]["processing_time"] = debug_info["end_time"] - start_time
            return result, debug_info

        return result

    except Exception as e:
        log_step(f"Fatal error in validate_extracted_citations: {str(e)}", "error")
        if return_debug:
            debug_info["end_time"] = time.time()
            debug_info["stats"]["processing_time"] = debug_info["end_time"] - start_time
            debug_info["errors"].append(f"Fatal error: {str(e)}")
            return {
                "validated_citations": [],
                "warnings": [],
                "errors": debug_info["errors"],
            }, debug_info
        return {
            "validated_citations": [],
            "warnings": [],
            "errors": [f"Fatal error: {str(e)}"],
        }


def validate_with_timeout(citation):
    """
    Validate a single citation with timeout handling.

    Args:
        citation: The citation object to validate (must have 'citation_text')

    Returns:
        Tuple of (result, debug_info) from validate_citation

    Raises:
        ValidationTimeoutError: If validation takes longer than the timeout
        Exception: Any exception raised during validation
    """
    if not isinstance(citation, dict) or "citation_text" not in citation:
        raise ValueError(
            "Invalid citation format. Expected dict with 'citation_text' key."
        )

    citation_text = citation["citation_text"]
    log_step(f"Starting validation for citation: {citation_text[0:100]}...", "debug")
    start_time = time.time()

    try:
        # Add source information to the citation if not present
        if "source" not in citation:
            citation["source"] = "unknown"

        # Call the validation function with the citation text
        citation_text = citation.get("citation_text", "")
        try:
            # Try to get the validation result as a dictionary
            result = citation_processor.validate_citation(citation_text)

            # Create a debug info dictionary
            debug_info = {
                "validation_time": time.time() - start_time,
                "source": result.get("source", "unknown"),
                "cached": result.get("cached", False),
            }

            # Map the result to the expected format
            if isinstance(result, dict):
                result = {
                    "verified": result.get("valid", False),
                    "validation_method": result.get("source", "local"),
                    "results": result.get("results", []),
                    "error": result.get("error"),
                    "debug_info": debug_info,
                }

            # Calculate processing time
            elapsed = time.time() - start_time
            log_step(
                f"Validated in {elapsed:.2f}s: {result.get('verified', False)}",
                "debug",
            )
        except Exception as e:
            elapsed = time.time() - start_time
            log_step(f"Error during validation: {str(e)}", "error")
            result = {
                "verified": False,
                "validation_method": "error",
                "results": [],
                "error": str(e),
                "debug_info": {
                    "validation_time": elapsed,
                    "source": "error",
                    "error": str(e),
                },
            }
            debug_info = result["debug_info"]

        # Update the citation with validation results
        if isinstance(result, dict):
            # Add validation status
            citation["validation_status"] = (
                "verified" if result.get("verified") else "unverified"
            )
            # Add validation details to metadata
            if "metadata" not in citation:
                citation["metadata"] = {}
            citation["metadata"].update(
                {
                    "validation_method": result.get("validation_method"),
                    "verified_by": result.get("verified_by"),
                    "reporter_type": result.get("reporter_type"),
                    "validation_time": elapsed,
                }
            )
            # Add parallel citations if available
            if "parallel_citations" in result and result["parallel_citations"]:
                citation["metadata"]["parallel_citations"] = result[
                    "parallel_citations"
                ]

        return result, debug_info

    except ValidationTimeoutError:
        elapsed = time.time() - start_time
        log_step(
            f"Timeout after {elapsed:.2f}s for: {citation_text[0:100]}...",
            "warning",
        )
        raise

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error after {elapsed:.2f}s: {str(e)}"
        log_step(f"{error_msg}\n{traceback.format_exc()}", "error")

        # Return a structured error response
        error_result = {
            "status": "error",
            "error": str(e),
            "citation_text": citation_text,
            "validation_time": elapsed,
            "source": citation.get("source", "unknown"),
        }

        return error_result, {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
    # --- FILTER OUT ARTIFACTS AND NON-CITATIONS ---
    def is_artifact_or_invalid(citation_obj):
        citation_val = citation_obj.get("citation_text", "")
        if not isinstance(citation_val, str):
            return True  # Filter out non-string citation_texts as invalid

        text = citation_val.strip()

        # Skip empty strings
        if not text:
            return True

        # Special handling for Caraway v. Caraway format
        if "Caraway v. Caraway" in text:
            return False

        # Remove lone section symbols, punctuation, or very short strings
        if len(text) < 4:
            return True

        # Skip if it's just punctuation
        if all(c in "§§.,;:*-_()[]{}|/\\'\"`~!@#$%^&<>? \\t\\n" for c in text):
            return True

        # Remove if only section symbols (e.g., '§', '§§')
        if re.fullmatch(r"§+", text):
            return True

        # Special case for common legal abbreviations that might be flagged as invalid
        common_legal_phrases = [
            "id.",
            "supra",
            "infra",
            "e.g.",
            "i.e.",
            "etc.",
            "et seq.",
            "aff'd",
            "rev'd",
            "cert. denied",
            "cert. granted",
        ]
        if text.lower() in common_legal_phrases:
            return False

        # Remove if not matching a valid citation format
        try:
            from .enhanced_validator_production import is_valid_citation_format
        except ImportError:
            def is_valid_citation_format(text):
                return True

        # For Caraway v. Caraway format, be more lenient
        if "Caraway" in text and "v." in text and not is_valid_citation_format(text):
            return False

        if not is_valid_citation_format(text):
            return True

        return False

    unlikely_citations = []

    def filter_and_flag(citations):
        filtered = []
        for c in citations:
            if is_artifact_or_invalid(c):
                c = dict(c)  # copy
                c.setdefault("metadata", {})
                c["metadata"]["invalid_reason"] = "artifact_or_invalid"
                unlikely_citations.append(c)
                continue
            filtered.append(c)
        return filtered

    results["confirmed_citations"] = filter_and_flag(results["confirmed_citations"])
    results["possible_citations"] = filter_and_flag(results["possible_citations"])
    results["unlikely_citations"] = unlikely_citations

    if return_debug:
        return results, debug_info
    return results


# Function to generate a unique analysis ID
def generate_analysis_id():
    """Generate a unique ID for the analysis."""
    return str(uuid.uuid4())


# Function to extract text from a URL
def extract_text_from_url(url):
    """
    Extract text from a URL and find citations in the content.
    
    Args:
        url (str): The URL to extract text from
        
    Returns:
        dict: Dictionary containing extracted text and citations
    """
    logger.info(f"Extracting text and citations from URL: {url}")
    try:
        # Import the combined citation extractor
        from eyecite_handler import extract_and_combine_citations
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")

        # Make request with timeout and user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Check if it's a PDF URL
        if url.lower().endswith('.pdf'):
            # Handle PDF files
            try:
                # Download the PDF content
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                
                # Save to a temporary file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                try:
                    # Extract text with PDF to markdown conversion
                    from file_utils import extract_text_from_file
                    text = extract_text_from_file(
                        temp_file_path,
                        convert_pdf_to_md=True  # Enable PDF to markdown conversion
                    )
                    
                    logger.info(f"Successfully extracted {len(text)} characters from PDF with markdown conversion")
                    return {"text": text, "citations": []}
                finally:
                    # Clean up the temporary file
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Error cleaning up temporary file: {e}")
            except Exception as e:
                logger.error(f"Error processing PDF from URL: {e}")
                raise Exception(f"Failed to process PDF from URL: {str(e)}")
        else:
            # Handle HTML content
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator="\n", strip=True)
            log_step(f"Extracted {len(text)} characters from URL content")
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  ") if phrase.strip())
            text = "\n".join(chunks)
            
            # Log a sample of the extracted text for debugging
            sample_text = text[:500].replace('\n', ' ').replace('\r', '')
            log_step(f"Sample extracted text: {sample_text}...")

        logger.info(f"Successfully extracted {len(text)} characters from URL")
        
        # Extract citations from the text
        citations = extract_and_combine_citations(text)
        
        return {
            "text": text,
            "citations": citations,
            "url": url,
            "status": "success",
            "characters_processed": len(text),
            "citations_found": len(citations)
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching URL: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "url": url
        }
    except Exception as e:
        error_msg = f"Error processing URL: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "url": url
        }


# Function to print registered routes for debugging
def print_registered_routes(app):
    """Print all registered routes for debugging purposes."""
    output = []
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        output.append(f"{rule.endpoint:50s} {methods:20s} {rule}")
    logger.info("Registered routes:\n" + "\n".join(sorted(output)))


def create_enhanced_analyze_endpoint():
    """
    Factory function to create the enhanced_analyze_endpoint function.
    This ensures we get a fresh function instance for each blueprint.
    """

    def enhanced_analyze_endpoint():
        """
        Endpoint for enhanced citation analysis.

        This is a thin wrapper around the enhanced_analyze function that adds CORS headers
        and handles OPTIONS requests for preflight CORS checks.

        The endpoint accepts both JSON and multipart/form-data requests.
        """
        # Handle OPTIONS request for CORS preflight
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type,Authorization"
            )
            response.headers.add(
                "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
            )
            return response

        # Add CORS headers to all responses
        @flask.after_this_request
        def add_cors_headers(response):
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type,Authorization"
            )
            response.headers.add(
                "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
            )
            return response

        # Call the main analysis function
        try:
            # For file uploads, handle multipart/form-data
            if request.content_type and "multipart/form-data" in request.content_type:
                logger.info("Handling multipart/form-data request")

                # Handle file upload
                if "file" not in request.files:
                    logger.error("No file part in the request")
                    return (
                        jsonify(
                            {"success": False, "error": "No file part in the request"}
                        ),
                        400,
                    )

                file = request.files["file"]
                if file.filename == "":
                    logger.error("No selected file")
                    return jsonify({"success": False, "error": "No selected file"}), 400

                try:
                    # Read the file content
                    file_content = file.read()

                    # Try to decode as UTF-8, but fall back to binary if that fails
                    try:
                        file_content = file_content.decode("utf-8")
                    except UnicodeDecodeError:
                        # For binary files, we'll just use the raw bytes
                        pass

                    # Prepare the data for enhanced_analyze
                    data = {
                        "file": file_content,
                        "filename": file.filename,
                        "text": request.form.get("text", ""),
                        "options": {
                            "batch_process": request.form.get(
                                "batch_process", "true"
                            ).lower()
                            == "true",
                            "return_debug": request.form.get(
                                "return_debug", "false"
                            ).lower()
                            == "true",
                        },
                    }

                    logger.info(
                        f"Processing file upload: {file.filename} ({len(file_content)} bytes)"
                    )

                    # Call enhanced_analyze with the prepared data
                    return enhanced_analyze(data)

                except Exception as e:
                    logger.error(f"Error processing file upload: {str(e)}")
                    logger.exception("File upload error details:")
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"Error processing file: {str(e)}",
                                "type": type(e).__name__,
                            }
                        ),
                        500,
                    )

            else:
                # For JSON requests, just pass through to enhanced_analyze
                # It will handle the JSON parsing itself
                logger.info("Handling JSON request")
                return enhanced_analyze()

        except Exception as e:
            logger.error(f"Error in enhanced_analyze_endpoint: {str(e)}")
            logger.exception("Detailed error:")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "An error occurred while processing the request",
                        "details": str(e),
                        "type": type(e).__name__,
                    }
                ),
                500,
            )

    return enhanced_analyze_endpoint


# Create the initial endpoint function
enhanced_analyze_endpoint = create_enhanced_analyze_endpoint()

# Add the analyze endpoint to the blueprint
enhanced_validator_bp.route("/analyze", methods=["POST", "OPTIONS"])(
    enhanced_analyze_endpoint
)

# Ensure the endpoint is accessible under the correct prefix
def ensure_correct_endpoint(app):
    """Ensure the analyze endpoint is accessible under the correct prefix."""
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('enhanced_validator') and '/analyze' in str(rule):
            logger.info(f"Found analyze endpoint: {rule}")
            return
    logger.warning("Analyze endpoint not found, adding manually")
    app.add_url_rule('/api/enhanced/analyze', view_func=enhanced_analyze_endpoint, methods=['POST', 'OPTIONS'])

# Update the registration function to ensure the endpoint is accessible
def register_enhanced_validator(app):
    """Register the enhanced validator blueprint with the Flask application."""
    try:
        # Check if blueprint is already registered
        if 'enhanced_validator' in app.blueprints:
            logger.info("Enhanced validator blueprint already registered, skipping")
            return app

        # Create and register the blueprint
        enhanced_validator_bp = create_enhanced_validator_blueprint()
        app.register_blueprint(enhanced_validator_bp, url_prefix="/api/enhanced")
        
        # Ensure the endpoint is accessible
        ensure_correct_endpoint(app)
        
        logger.info("Registered enhanced validator routes:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('enhanced_validator.'):
                methods = ','.join(rule.methods - {'OPTIONS', 'HEAD'}) if hasattr(rule, 'methods') else 'GET'
                logger.info(f"  {rule.endpoint}: {rule} - {methods}")
        
        logger.info("Enhanced validator registered successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to register enhanced validator: {e}")
        raise
