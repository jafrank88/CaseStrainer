#!/usr/bin/env python
# -*- coding: utf-8 -*-
print(
    "DEBUG: Loading enhanced_validator_production.py v0.5.0 - Updated with CitationProcessor"
)

"""
Enhanced Citation Validator for Production

This module integrates the simplified Enhanced Validator with the production app_final_vue.py.
"""

# Standard library imports
import logging
import time

# Third-party imports
from flask import Blueprint, jsonify, request

# Local imports
from citation_processor import CitationProcessor

# Set up logging
log_format = (
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_validator_bp = Blueprint("enhanced_validator", __name__)

# Global circuit breaker state
CIRCUIT_BREAKER = {
    "tripped": False,
    "trip_time": 0,
    "failure_count": 0,
    "last_failure": 0,
}

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD = 3  # Number of failures before tripping
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes in seconds
MIN_REQUESTS_BEFORE_TRIP = 5  # Minimum requests before allowing circuit to trip

# API configuration
COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v4/"
API_TIMEOUT = 15  # seconds

# Initialize citation processor
citation_processor = CitationProcessor()


def log_step(message: str, level: str = "info"):
    """Log a processing step with consistent formatting."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[VALIDATOR] {message}")


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

    start_time = time.time()

    try:
        # Extract citations
        extract_start = time.time()
        citations = citation_processor.extract_citations(text)
        extract_time = time.time() - extract_start

        debug_info["extraction_time"] = extract_time
        log_step(f"Extracted {len(citations)} citations in {extract_time:.2f} seconds")

        # Validate citations
        validate_start = time.time()
        citation_texts = [str(citation) for citation in citations]

        if batch_process:
            # Process all citations in a single batch
            validation_results = citation_processor.process_batch(citation_texts)
        else:
            # Process citations one by one
            validation_results = []
            for citation in citation_texts:
                try:
                    result = citation_processor.validate_citation(citation)
                    validation_results.append(result)
                except Exception as e:
                    log_step(f"Error validating citation {citation}: {str(e)}", "error")
                    validation_results.append(
                        {
                            "citation": citation,
                            "valid": False,
                            "error": str(e),
                            "cached": False,
                            "results": [],
                        }
                    )

        validate_time = time.time() - validate_start
        debug_info["validation_time"] = validate_time

        # Prepare the final result
        result = {
            "citations": validation_results,
            "stats": {
                "total_citations": len(validation_results),
                "valid_citations": sum(1 for c in validation_results if c.get("valid")),
                "processing_time": time.time() - start_time,
                "extraction_time": extract_time,
                "validation_time": validate_time,
            },
        }

        if return_debug:
            result["debug"] = debug_info

        log_step(
            f"Analysis completed in {result['stats']['processing_time']:.2f} seconds"
        )
        return result

    except Exception as e:
        error_msg = f"Error analyzing text: {str(e)}"
        log_step(error_msg, "error")
        debug_info["error"] = error_msg

        if return_debug:
            return {"citations": [], "stats": {"error": error_msg}, "debug": debug_info}
        raise ValueError(error_msg)


@enhanced_validator_bp.route("/api/analyze", methods=["POST"])
def enhanced_analyze():
    """API endpoint to analyze text for legal citations."""
    start_time = time.time()

    try:
        # Get request data
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "No text provided", "status": "error"}), 400

        text = data["text"]
        batch_process = data.get("batch_process", False)

        if not text or not isinstance(text, str):
            return jsonify({"error": "Invalid text input", "status": "error"}), 400

        # Analyze the text
        result = analyze_text(text, batch_process=batch_process)

        # Calculate processing time
        processing_time = time.time() - start_time
        result["stats"]["api_processing_time"] = processing_time

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "error": error_msg,
                    "processing_time": time.time() - start_time,
                }
            ),
            500,
        )


def register_enhanced_validator(app):
    """Register the enhanced validator blueprint with the Flask app."""
    try:
        app.register_blueprint(enhanced_validator_bp, url_prefix="/enhanced-validator")
        logger.info("Enhanced Validator blueprint registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register Enhanced Validator blueprint: {str(e)}")
        return False


if __name__ == "__main__":
    # Example usage
    test_text = """
    The court in Brown v. Board of Education, 347 U.S. 483 (1954), 
    held that racial segregation in public schools was unconstitutional.
    This was later affirmed in Cooper v. Aaron, 358 U.S. 1 (1958).
    """

    result = analyze_text(test_text)
    print(f"Found {len(result['citations'])} citations")
    for citation in result["citations"]:
        print(
            f"- {citation['citation']}: {'Valid' if citation['valid'] else 'Invalid'}"
        )
