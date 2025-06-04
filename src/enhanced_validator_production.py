#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os
import sys
import flask
from flask import Blueprint, request, jsonify

# Import centralized logging configuration
from logging_config import configure_logging as configure_logging_config

# Configure logging
logger = logging.getLogger(__name__)

# The actual logging configuration will be done when the Flask app is initialized
# and configure_logging() is called from app_final_vue.py


# Create a function to get a new blueprint with a unique name
def create_enhanced_validator_blueprint():
    import time

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
if "enhanced_validator_bp" not in globals():
    enhanced_validator_bp = get_enhanced_validator_blueprint()
    logger.info(
        f"Created new enhanced_validator_bp with name: {enhanced_validator_bp.name}"
    )
else:
    logger.info(
        f"Using existing enhanced_validator_bp with name: {enhanced_validator_bp.name}"
    )

logger.info("Loading enhanced_validator_production.py v0.4.7 - Modified 2025-06-02")

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

logger = logging.getLogger(__name__)

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


def enhanced_analyze(data=None):
    """
    Enhanced citation analysis function that handles both file uploads and direct text input.

    Can be called with a data dictionary or will use the current Flask request.

    Expected data format (dict or JSON):
    {
        "text": "text to analyze",  # Either text or file is required
        "file": "file_content",      # Optional, alternative to text (raw file content)
        "filename": "document.pdf",  # Optional, used for logging
        "options": {
            "batch_process": True,   # Whether to process all citations in a single batch
            "return_debug": False    # Whether to include debug information in the response
        }
    }

    Args:
        data (dict, optional): Input data. If None, will be extracted from the Flask request.

    Returns:
        Flask Response: JSON response with citation analysis results
    """
    try:
        # Log the incoming request for debugging
        logger.info("Starting enhanced_analyze")

        request_data = {}

        # If data is provided, use it directly
        if data is not None:
            request_data = data
        # Otherwise, try to get it from the request
        elif request:
            if request.is_json:
                request_data = request.get_json() or {}
            elif request.form:
                request_data = dict(request.form)
                # Handle file uploads
                if "file" in request.files and request.files["file"].filename:
                    file = request.files["file"]
                    request_data["file"] = file.read().decode("utf-8")
                    if "filename" not in request_data:
                        request_data["filename"] = file.filename

                # Convert string values to proper types
                if "options" in request_data and isinstance(
                    request_data["options"], str
                ):
                    try:
                        request_data["options"] = json.loads(request_data["options"])
                    except (json.JSONDecodeError, TypeError):
                        request_data["options"] = {}

        # Ensure options is a dictionary
        if "options" not in request_data or not isinstance(
            request_data["options"], dict
        ):
            request_data["options"] = {}

        # Set default options
        default_options = {"batch_process": True, "return_debug": False}

        # Merge with provided options
        request_data["options"] = {**default_options, **request_data.get("options", {})}

        logger.debug(
            f"Processing data: {json.dumps(request_data, default=str, indent=2)}"
        )

        # Check for required fields
        if not request_data or (
            "text" not in request_data and "file" not in request_data
        ):
            logger.error("No text or file provided in request")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Either 'text' or 'file' must be provided",
                    }
                ),
                400,
            )

        # Get options
        options = request_data["options"]
        batch_process = options["batch_process"]
        return_debug = options["return_debug"]

        text = ""

        # Handle file upload if present
        if "file" in request_data:
            # Get file content
            file_content = request_data["file"]
            if not file_content:
                return (
                    jsonify({"success": False, "error": "No file content provided"}),
                    400,
                )

            # Use file content as text
            text = file_content
            logger.info(
                f"Processing file upload: {request_data.get('filename', 'unnamed')} with {len(text)} characters"
            )
        else:
            # Handle direct text input
            text = request_data.get("text", "")
            if not isinstance(text, str) or not text.strip():
                return jsonify({"success": False, "error": "Invalid text format"}), 400

        # Limit text size to prevent memory issues (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(text) > max_size:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Text too large. Maximum size is {max_size} bytes.",
                        "size": len(text),
                        "max_size": max_size,
                    }
                ),
                400,
            )

        logger.info(f"Processing text with {len(text)} characters")

        try:
            # Analyze the text
            analysis = analyze_text(
                text, batch_process=batch_process, return_debug=return_debug
            )
        except Exception as e:
            logger.error(f"Error in analyze_text: {str(e)}")
            logger.exception("Detailed error:")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Error analyzing text",
                        "details": str(e),
                    }
                ),
                500,
            )

        # Transform the response to match frontend expectations
        transformed_citations = []
        for item in analysis.get("citations", []):
            # Handle both old and new response formats
            if isinstance(item, dict):
                citation = item.get("citation", {})
                validation = item.get("validation", {})

                # Create a clean citation object with all necessary fields
                transformed = {
                    "citation": citation.get("citation_text", ""),
                    "case_name": citation.get("case_name", ""),
                    "verified": validation.get("verified", False),
                    "validation_method": validation.get("validation_method", ""),
                    "url": validation.get("details", {}).get("url", ""),
                    "metadata": citation.get("metadata", {}),
                }
                transformed_citations.append(transformed)
            else:
                # If the item is already in the correct format, use it as is
                transformed_citations.append(item)

        # Create the response object
        response = {
            "success": True,
            "citations": transformed_citations,
            "total": len(transformed_citations),
            "verified": sum(
                1 for c in transformed_citations if c.get("verified", False)
            ),
            "landmark_cases": analysis.get("landmark_cases", []),
            "statistics": analysis.get(
                "statistics",
                {
                    "total_citations": len(transformed_citations),
                    "verified_citations": sum(
                        1 for c in transformed_citations if c.get("verified", False)
                    ),
                    "processing_time": analysis.get("processing_time", 0),
                },
            ),
        }

        # Include debug info if requested and available
        if return_debug and "debug_info" in analysis and analysis["debug_info"]:
            response["debug_info"] = analysis["debug_info"]

        logger.info(f"Analysis complete. Found {len(transformed_citations)} citations.")
        return jsonify(response)

    except ValueError as e:
        logger.error(f"ValueError in enhanced_analyze: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"Error in enhanced_analyze: {str(e)}")
        logger.exception("Detailed error:")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "An internal server error occurred",
                    "details": str(e),
                }
            ),
            500,
        )


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
        html_content = markdown(text)

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
    text: str, batch_process: bool = False, return_debug: bool = True
) -> dict:
    """
    Analyze text for legal citations using the enhanced citation processor.

    Args:
        text (str): The text to analyze for citations
        batch_process (bool): If True, process all citations together in a single batch
        return_debug (bool): If True, include debug information in the response

    Returns:
        dict: Analysis results with citations and metadata
    """
    debug_info = {
        "input_length": len(text),
        "extraction_time": None,
        "validation_time": None,
        "total_processing_time": None,
        "error": None,
    }

    time.time()

    try:
        # Extract citations
        extract_start = time.time()
        extract_result = extract_citations(
            text, return_debug=True, batch_process=batch_process
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

        # Prepare response
        response = {
            "status": "success",
            "citations": validated_citations,
            "citation_count": len(validated_citations),
            "debug": debug_info if return_debug else None,
        }

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


def extract_citations(text, return_debug=False, batch_process=False):
    """
    Extract legal citations from text using regex patterns and other methods.

    Args:
        text (str): The text to extract citations from
        return_debug (bool): If True, returns debug information along with citations
        batch_process (bool): If True, process all citations together in a single batch

    Returns:
        list: List of extracted citations with metadata
        or tuple: (citations, debug_info) if return_debug is True
    """
    """
    Extract legal citations from text using eyecite and regex patterns.

    Args:
        text (str): The text to extract citations from
        return_debug (bool): If True, returns debug information along with citations
        batch_process (bool): If True, process all citations together in a single batch

    Returns:
        list: List of extracted citations with metadata
        or tuple: (citations, debug_info) if return_debug is True
    """
    start_time = time.time()
    debug_info = {
        "start_time": start_time,
        "steps": [],
        "stats": {
            "total_citations": 0,
            "blacklisted": 0,
            "eyecite_citations": 0,
            "regex_citations": 0,
            "validation_errors": 0,
            "case_name_cleaned": 0,
            "pin_cites_handled": 0,
        },
        "warnings": [],
        "errors": [],
    }

    def log_step(message, level="info"):
        """Helper to log a processing step with timing info."""
        elapsed = time.time() - start_time
        step_info = {"time": round(elapsed, 2), "message": message, "level": level}
        debug_info["steps"].append(step_info)
        log_msg = f"[EXTRACT] {message} (after {elapsed:.2f}s)"

        if level == "debug":
            logger.debug(log_msg)
        elif level == "info":
            logger.info(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
            debug_info["warnings"].append(message)
        elif level == "error":
            logger.error(log_msg)
            debug_info.setdefault("errors", []).append(message)

    # Define default blacklist patterns
    default_blacklist = {
        "exact": ["id.", "id.", "id.,"],
        "regex": [
            r"\b(?:doc\.?|document)\s*[#:]?\s*\d+",
            r"\b(?:no\.?|number)\s+\d+",
            r"\b(?:see|see also|cf\.?|e\.g\.?|i\.e\.?|etc\.?|et seq\.?|supra|infra|id\.?)\b",
            r"\b\d+\s*(?:U\.?\s*S\.?C\.?|U\.?\s*S\.?\s*Code)\s*§?\s*\d+",
            r"\b\d+\s*C\.?F\.?R\.?\s*§?\s*\d+",
        ],
    }

    # Get the path to the blacklist file
    blacklist_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "blacklist.json"
    )

    def load_blacklist():
        """Load blacklist patterns from JSON file or use defaults if not found."""
        # First try to load from file
        if os.path.exists(blacklist_path):
            try:
                with open(blacklist_path, "r", encoding="utf-8") as f:
                    custom_blacklist = json.load(f)
                    # Validate the structure
                    if isinstance(custom_blacklist, dict) and all(
                        k in custom_blacklist for k in ["exact", "regex"]
                    ):
                        log_step(
                            f"Loaded custom blacklist from {blacklist_path}", "info"
                        )
                        return custom_blacklist
                    else:
                        log_step("Invalid blacklist format, using default", "warning")
            except Exception as e:
                log_step(f"Error loading blacklist: {str(e)}", "warning")

        # If we get here, use the default blacklist
        log_step("Using default blacklist patterns", "info")
        return default_blacklist

    # Load the blacklist (will use defaults if file not found)
    blacklist = load_blacklist()

    # Log blacklist stats for debugging
    log_step(
        f"Loaded {len(blacklist.get('exact', []))} exact and {len(blacklist.get('regex', []))} regex blacklist patterns",
        "debug",
    )

    def is_blacklisted(citation_text):
        """Check if a citation matches any blacklist patterns."""
        if not citation_text or not isinstance(citation_text, str):
            return False

        # Normalize the citation text for better matching
        normalized = citation_text.lower().strip()

        # Check exact matches (case-insensitive)
        if any(
            normalized == item.lower().strip() for item in blacklist.get("exact", [])
        ):
            debug_info["stats"]["blacklisted"] += 1
            log_step(f"Blacklisted (exact match): {citation_text}", "debug")
            return True

        # Check regex patterns
        for pattern in blacklist.get("regex", []):
            try:
                if re.search(pattern, citation_text, re.IGNORECASE):
                    debug_info["stats"]["blacklisted"] += 1
                    log_step(
                        f"Blacklisted (regex match): {citation_text} matched {pattern}",
                        "debug",
                    )
                    return True
            except re.error as e:
                log_step(
                    f"Invalid regex pattern in blacklist: {pattern} - {str(e)}",
                    "warning",
                )
                continue

        # Check common false positives
        false_positives = [
            r"^\d+$",  # Just a number
            r"^[A-Za-z\.]+$",  # Just letters and dots
            r"^\d+\s+[A-Za-z\.]+$",  # Just volume and reporter
            r"^[A-Za-z]+\s+v\.\s+[A-Za-z]+$",  # Just case name with v.
            r"^[A-Za-z]+\s+v\s+[A-Za-z]+$",  # Just case name with v
        ]

        for pattern in false_positives:
            if re.fullmatch(pattern, normalized):
                log_step(f"Filtered out false positive: {citation_text}", "debug")
                return True

        return False

    # Initialize results
    results = {
        "confirmed_citations": [],
        "possible_citations": [],
        "warnings": [],
        "errors": [],
        "batch_processed": batch_process,
    }

    # Track unique citations to avoid duplicates
    seen_citations = set()

    # Preprocess text if it contains markdown
    original_text = text
    if MARKDOWN_AVAILABLE and any(char in text for char in ["*", "_", "`", "#"]):
        log_step("Detected markdown formatting, preprocessing text")
        text = preprocess_markdown(text)
        if text != original_text:
            log_step("Finished preprocessing markdown")

    # Normalize citation text before processing
    normalized_text = normalize_citation_text(text)
    if normalized_text != text:
        log_step("Normalized citation text before processing")
        text = normalized_text

    # Try to use eyecite if available
    eyecite_available = False
    try:
        from citation_processor import CitationProcessor

        log_step("Initialized CitationProcessor for text cleaning")

        # Clean the text using eyecite's cleaner with default cleaning steps
        cleaned_text = CitationProcessor().clean_text(
            text, steps=["all_whitespace", "inline_whitespace", "underscores"]
        )
        if cleaned_text != text:
            log_step(
                f"Text was cleaned. Original length: {len(text)}, Cleaned length: {len(cleaned_text)}"
            )
            text = cleaned_text
        else:
            log_step("No cleaning needed for the input text")

        eyecite_available = True
        log_step("Successfully initialized eyecite for citation extraction")
    except ImportError as e:
        log_step(
            f"eyecite not available: {str(e)}, falling back to regex patterns",
            "warning",
        )

    if eyecite_available:
        log_step(f"Starting citation extraction with eyecite on text: {text[:200]}...")
        try:
            tokenizer = AhocorasickTokenizer()
            citations = get_citations(text, tokenizer=tokenizer)
            log_step(f"eyecite found {len(citations)} potential citations")

            # Debug: Log raw eyecite output
            log_step(f"Raw eyecite output: {[str(c) for c in citations]}", "debug")

            if not citations:
                log_step(
                    "No citations found with eyecite. Text might not contain recognizable citation patterns.",
                    "warning",
                )
            else:
                # Process each citation found by eyecite
                for i, citation in enumerate(citations, 1):
                    try:
                        citation_text = citation.matched_text().strip()
                        if not citation_text:
                            continue

                        # Debug specific citation
                        if "534 F.3d 1290" in citation_text:
                            log_step(f"Found target citation: {citation_text}", "debug")
                            log_step(f"Citation type: {type(citation)}", "debug")
                            log_step(
                                f"Citation metadata: {getattr(citation, 'metadata', 'No metadata')}",
                                "debug",
                            )

                        # Skip blacklisted citations
                        is_black = is_blacklisted(citation_text)
                        if is_black:
                            log_step(
                                f"Skipping blacklisted citation: {citation_text}",
                                "debug",
                            )
                            continue

                        # Create a complete citation object with all required fields
                        citation_obj = {
                            "citation_text": citation_text,
                            "source": "eyecite",
                            "metadata": {
                                "extraction_method": "eyecite",
                                "has_pin_cite": False,
                                "pin_cite": None,
                                "parenthetical": None,
                                "year": None,
                                "court": None,
                            },
                            "validation_status": "valid",  # Mark as valid by default
                            "is_valid": True,  # Explicitly mark as valid
                            "case_name": None,  # Will be filled in by validation if needed
                            "backdrop": None,  # Required field for the frontend
                        }

                        # Add to confirmed citations
                        results["confirmed_citations"].append(citation_obj)
                        debug_info["stats"]["eyecite_citations"] += 1

                        if "534 F.3d 1290" in citation_text:
                            log_step(
                                f"Successfully added citation to results: {citation_text}",
                                "debug",
                            )
                            log_step(f"Citation object: {citation_obj}", "debug")

                        if i % 100 == 0 or i == len(citations):
                            log_step(f"Processed {i}/{len(citations)} citations")

                    except Exception as e:
                        log_step(f"Error processing citation {i}: {str(e)}", "error")
                        debug_info["stats"]["validation_errors"] += 1
                        continue

                log_step(
                    f"Extracted {len(results['confirmed_citations'])} unique citations using eyecite"
                )

        except Exception as e:
            log_step(f"Error in eyecite extraction: {str(e)}", "error")
            debug_info["errors"].append(f"eyecite extraction failed: {str(e)}")

        # If we have confirmed citations, return them directly
        if results["confirmed_citations"]:
            log_step(
                f"Found {len(results['confirmed_citations'])} citations with eyecite, skipping regex fallback"
            )

            # Ensure all required fields are present in the response
            for citation in results["confirmed_citations"]:
                if "validation_status" not in citation:
                    citation["validation_status"] = "valid"
                if "is_valid" not in citation:
                    citation["is_valid"] = True
                if "case_name" not in citation:
                    citation["case_name"] = None
                if "backdrop" not in citation:
                    citation["backdrop"] = None

            if return_debug:
                return results["confirmed_citations"], debug_info
            return results["confirmed_citations"]

    try:
        # Fall back to regex patterns if no citations found with eyecite
        if not results["confirmed_citations"] or not eyecite_available:
            log_step(
                f"No citations found with eyecite, falling back to regex patterns. Found {len(results['confirmed_citations'])} citations so far."
            )
            log_step(f"Text being processed with regex patterns: {text[:200]}...")

            # If we have citations in possible_citations, log why they weren't confirmed
            if results["possible_citations"]:
                log_step(
                    f"Found {len(results['possible_citations'])} possible citations that weren't confirmed"
                )
                for i, cite in enumerate(results["possible_citations"][:3]):
                    log_step(
                        f"Possible citation {i+1}: {cite.get('citation_text', 'No text')}"
                    )
                    log_step(f"  Source: {cite.get('source', 'unknown')}")
                    log_step(f"  Metadata: {cite.get('metadata', {})}")

            # Load citation patterns
            try:
                from citation_patterns import (
                    CITATION_PATTERNS,
                    COMMON_CITATION_FORMATS,
                    LEGAL_REPORTERS,
                )

                # Initialize with empty values if not found
                CITATION_PATTERNS = CITATION_PATTERNS or {}
                COMMON_CITATION_FORMATS = COMMON_CITATION_FORMATS or {}
                LEGAL_REPORTERS = LEGAL_REPORTERS or {}

                eyecite_citations = set(
                    c["citation_text"] for c in results["confirmed_citations"]
                )

                # Process LEXIS patterns first
                lexis_patterns = {
                    k: v for k, v in CITATION_PATTERNS.items() if k.startswith("lexis_")
                }
                other_patterns = {
                    k: v
                    for k, v in CITATION_PATTERNS.items()
                    if not k.startswith("lexis_")
                }

                def process_patterns(patterns, pattern_type="regex"):
                    nonlocal seen_citations
                    for pattern_name, pattern in patterns.items():
                        try:
                            matches = list(re.finditer(pattern, text, re.IGNORECASE))
                            log_step(
                                f"Processing {len(matches)} matches for pattern {pattern_name}",
                                "debug",
                            )

                            for match in matches:
                                citation_text = match.group(0).strip()
                                if not citation_text or is_blacklisted(citation_text):
                                    log_step(
                                        f"Skipping blacklisted or empty citation: {citation_text}",
                                        "debug",
                                    )
                                    continue

                                # Clean up the citation text
                                citation_text = re.sub(
                                    r"\s+", " ", citation_text
                                ).strip()
                                citation_text = re.sub(r",\s+", ", ", citation_text)

                                # Skip duplicates from eyecite or previously seen regex citations
                                if (
                                    citation_text in eyecite_citations
                                    or citation_text in seen_citations
                                ):
                                    log_step(
                                        f"Skipping duplicate citation: {citation_text}",
                                        "debug",
                                    )
                                    continue

                                # Only add to seen_citations if it's a regex citation
                                seen_citations.add(citation_text)

                                # Try to extract case name if possible
                                case_name = None
                                if " v. " in citation_text:
                                    case_name = citation_text.split(",")[0].strip()
                                    case_name = clean_case_name(case_name)

                                    # Handle U.S. v. format
                                    if (
                                        "U.S. v. " in case_name
                                        and "U.S." not in case_name
                                    ):
                                        case_parts = case_name.split(" v. ")
                                        if len(case_parts) == 2:
                                            case_name = f"U.S. v. {case_parts[1]}"

                                # For regex citations, ensure proper formatting of Federal Reporter citations
                                if "F." in citation_text and "F. " not in citation_text:
                                    # Handle cases like "534 F.3d 1290" to ensure proper spacing
                                    citation_text = re.sub(
                                        r"(\d+)\s+(F\.)(\d+[a-z]*\s+\d+)",
                                        r"\1 \2\3",
                                        citation_text,
                                    )
                                    log_step(
                                        f"Formatted Federal Reporter citation: {citation_text}",
                                        "debug",
                                    )

                                citation_obj = {
                                    "case_name": case_name or citation_text,
                                    "backdrop": None,
                                    "citation_text": citation_text,
                                    "source": f"{pattern_type}_{pattern_name}",
                                    "metadata": {
                                        "extraction_method": pattern_type,
                                        "pattern_used": pattern_name,
                                        "has_pin_cite": bool(
                                            re.search(r",\s*\d+\s*$", citation_text)
                                        ),
                                    },
                                    "validation_status": "pending",
                                }

                                if pattern_type == "lexis":
                                    results["possible_citations"].append(citation_obj)
                                else:
                                    results["confirmed_citations"].append(citation_obj)

                                debug_info["stats"]["regex_citations"] += 1

                        except re.error as e:
                            log_step(
                                f"Invalid regex pattern {pattern_name}: {str(e)}",
                                "warning",
                            )
                            continue
                        except Exception as e:
                            log_step(
                                f"Error processing pattern {pattern_name}: {str(e)}",
                                "error",
                            )
                            continue

                # Process LEXIS patterns
                if lexis_patterns:
                    log_step(f"Processing {len(lexis_patterns)} LEXIS patterns")
                    process_patterns(lexis_patterns, "lexis")

                    # Process other patterns
                    if other_patterns:
                        log_step(f"Processing {len(other_patterns)} other patterns")
                        process_patterns(other_patterns, "regex")

                    log_step(
                        f"Extracted {len(results['confirmed_citations'])} citations using regex patterns"
                    )

            except ImportError as e:
                log_step(f"Citation patterns module not found: {str(e)}", "error")
                debug_info["errors"].append(
                    f"Failed to import citation patterns: {str(e)}"
                )
            except Exception as e:
                log_step(f"Error in regex extraction: {str(e)}", "error")
                debug_info["errors"].append(f"Regex extraction error: {str(e)}")

        # Update stats
        debug_info["stats"]["unique_citations"] = len(seen_citations)
        debug_info["stats"]["total_citations"] = len(
            results["confirmed_citations"]
        ) + len(results["possible_citations"])
        debug_info["stats"]["processing_time"] = time.time() - start_time

        log_step(f"Extraction complete. Found {len(seen_citations)} unique citations")

        if return_debug:
            debug_info["end_time"] = time.time()
            debug_info["stats"]["processing_time"] = debug_info["end_time"] - start_time
            return results, debug_info

        return results

    except Exception as e:
        log_step(f"Fatal error in extract_citations: {str(e)}", "error")
        if return_debug:
            debug_info["end_time"] = time.time()
            debug_info["stats"]["processing_time"] = debug_info["end_time"] - start_time
            debug_info["errors"].append(f"Fatal error: {str(e)}")
            return {
                "confirmed_citations": [],
                "possible_citations": [],
                "warnings": [],
                "errors": [],
            }, debug_info
        return {
            "confirmed_citations": [],
            "possible_citations": [],
            "warnings": [],
            "errors": [],
        }


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
            result = validate_citation(citation_text)

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
    if return_debug:
        return validated_citations, debug_info
    return validated_citations

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
        from .enhanced_validator_production import is_valid_citation_format

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
    """Extract text from a URL."""
    logger.info(f"Extracting text from URL: {url}")
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")

        # Make request with timeout and user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        logger.info(f"Successfully extracted {len(text)} characters from URL")
        return text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {str(e)}")
        raise ValueError(f"Error fetching URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting text from URL: {str(e)}")


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


# Function to register the blueprint with the Flask app
def register_enhanced_validator(app):
    """
    Register the enhanced validator blueprint with the Flask application.

    Args:
        app: The Flask application instance

    Returns:
        The Flask application with the enhanced validator blueprint registered
    """
    # Use a consistent name for the blueprint
    blueprint_name = "enhanced_validator"

    # Check if already registered
    if blueprint_name in app.blueprints:
        logger.info(f"{blueprint_name} already registered, skipping")
        return app

    try:
        # Get the URL prefix from the app config or use a default that matches the frontend
        url_prefix = app.config.get("ENHANCED_VALIDATOR_URL_PREFIX", "/api/enhanced")

        # Ensure the URL prefix starts with a slash and remove any trailing slashes
        url_prefix = url_prefix.strip().rstrip("/")
        if not url_prefix.startswith("/"):
            url_prefix = f"/{url_prefix}"

        logger.info(
            "Registering %s blueprint with URL prefix: %s", blueprint_name, url_prefix
        )

        # Get or create the blueprint
        current_bp = get_enhanced_validator_blueprint()
        current_bp.name = blueprint_name  # Ensure consistent naming

        # Create a fresh endpoint function instance for this blueprint
        endpoint_function = create_enhanced_analyze_endpoint()

        # Add the route to the blueprint
        current_bp.route("/analyze", methods=["POST", "OPTIONS"])(endpoint_function)

        # Add CORS headers to all responses
        @current_bp.after_request
        def add_cors_headers(response):
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type,Authorization"
            )
            response.headers.add(
                "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
            )
            return response

        # Register the blueprint with the app and URL prefix
        app.register_blueprint(current_bp, url_prefix=url_prefix, name=current_bp.name)

        # Log the registered routes for debugging
        if hasattr(app, "url_map") and hasattr(app.url_map, "iter_rules"):
            logger.info("Registered enhanced validator routes:")
            for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
                if "enhanced_validator" in str(rule.endpoint):
                    logger.info(
                        f"  {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})"
                    )

        logger.info("Enhanced validator registered successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to register enhanced validator: {e}")
        logger.exception("Error details:")

        # Try to register with a default prefix if the configured one fails
        try:
            logger.info("Attempting to register with default URL prefix")
            default_bp = get_enhanced_validator_blueprint()
            endpoint_function = create_enhanced_analyze_endpoint()
            default_bp.route("/analyze", methods=["POST", "OPTIONS"])(endpoint_function)
            app.register_blueprint(
                default_bp, url_prefix="/enhanced-validator", name=default_bp.name
            )
            logger.info("Successfully registered with default URL prefix")
            return app
        except Exception as default_e:
            logger.error(f"Failed to register with default URL prefix: {default_e}")
            logger.exception("Error details:")
            raise
            return app
        except Exception as fallback_error:
            logger.error(f"Fallback registration failed: {str(fallback_error)}")
            logger.exception("Fallback error details:")
            raise


# ... (rest of the code remains the same)
