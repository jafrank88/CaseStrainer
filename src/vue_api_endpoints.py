"""
Vue.js API Endpoints for CaseStrainer

This module provides the API endpoints needed by the Vue.js frontend
for the Multitool Confirmed and Unconfirmed Citations tabs.
"""

from datetime import datetime, timezone
import json
from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
)

# Create a Blueprint for Vue.js API endpoints
vue_api = Blueprint("vue_api", __name__)

from flask_mail import Message
from citation_utils import verify_citation

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


def enhanced_validate_citation(citation_text=None, api_key=None):
    """Enhanced citation validation using multiple sources."""
    # Get the citation from the request
    data = request.get_json() or {}
    current_app.logger.debug(f"[enhanced_validate_citation] Received data: {data}")

    # Handle different input formats
    if isinstance(data.get("citation"), dict):
        # Handle citation object format
        citation_obj = data["citation"]
        citation = citation_obj.get("text", citation_obj.get("citation_text", ""))
        case_name = citation_obj.get("case_name", citation_obj.get("name", ""))
    else:
        # Handle direct string citation
        citation = data.get("citation", citation_text or "")
        case_name = data.get("case_name", "")

    # If citation is a dictionary, try to get the text
    if isinstance(citation, dict):
        citation = citation.get("text", citation.get("citation_text", ""))

    # Convert to string if not already
    if citation is not None and not isinstance(citation, str):
        citation = str(citation)

    # Clean and validate the citation
    if not citation or not citation.strip():
        current_app.logger.warning("[enhanced_validate_citation] No citation provided")
        return (
            jsonify(
                {
                    "citation": "",
                    "verified": False,
                    "verified_by": "Validation",
                    "error": "No citation provided",
                    "metadata": {"case_name": case_name} if case_name else {},
                    "backdrop": "",
                }
            ),
            400,
        )

    current_app.logger.info(
        f"[enhanced_validate_citation] Validating citation: {citation}"
    )
    if case_name:
        current_app.logger.debug(
            f"[enhanced_validate_citation] With case name: {case_name}"
        )

    # Use the enhanced verifier if available
    if ENHANCED_VALIDATOR_AVAILABLE and register_enhanced_validator_func:
        enhanced_verifier = register_enhanced_validator_func()
        if enhanced_verifier:
            try:
                # Get the verification result from the enhanced verifier
                current_app.logger.info(
                    f"[enhanced_validate_citation] Starting verification for: {citation}"
                )
                result = enhanced_verifier.verify_citation(citation)

                # Log the raw result for debugging
                current_app.logger.debug(
                    f"[enhanced_validate_citation] Verifier result type: {type(result).__name__}, "
                    f"content: {json.dumps(result, default=str, indent=2) if hasattr(result, 'get') else str(result)}"
                )
            except Exception as e:
                current_app.logger.error(
                    f"[enhanced_validate_citation] Error in enhanced verifier: {str(e)}"
                )
                result = None

            try:
                # Handle different return types from the verifier
                if result is None:
                    response = {
                        "citation": citation,
                        "verified": False,
                        "verified_by": "Enhanced Validator",
                        "error": "Verification returned no result",
                        "metadata": {"case_name": case_name} if case_name else {},
                        "backdrop": "",
                        "verification_steps": [
                            "Verification process did not return a result"
                        ],
                    }
                elif isinstance(result, dict):
                    # Handle dictionary result
                    response = {
                        "citation": citation,
                        "verified": result.get("exists", False),
                        "verified_by": "Enhanced Validator",
                        "metadata": result.get("metadata", {}),
                        "backdrop": result.get("backdrop", ""),
                        "error": result.get("error", ""),
                        "warnings": result.get("warnings", []),
                        "verification_steps": result.get("verification_steps", []),
                        "sources": result.get("sources", {}),
                    }

                    # Ensure case_name is preserved if provided
                    if case_name and "case_name" not in response["metadata"]:
                        response["metadata"]["case_name"] = case_name
                elif hasattr(result, "__dict__"):
                    # Handle object result
                    response = {
                        "citation": citation,
                        "verified": getattr(result, "exists", False),
                        "verified_by": "Enhanced Validator",
                        "metadata": getattr(result, "metadata", {}),
                        "backdrop": getattr(result, "backdrop", ""),
                        "error": getattr(result, "error", ""),
                        "warnings": getattr(result, "warnings", []),
                        "verification_steps": getattr(result, "verification_steps", []),
                        "sources": getattr(result, "sources", {}),
                    }

                    # Ensure case_name is preserved if provided
                    if case_name and "case_name" not in response["metadata"]:
                        response["metadata"]["case_name"] = case_name
                else:
                    # Handle unexpected result type
                    response = {
                        "citation": citation,
                        "verified": False,
                        "verified_by": "Enhanced Validator",
                        "error": f"Unexpected result type: {type(result).__name__}",
                        "metadata": {"case_name": case_name} if case_name else {},
                        "backdrop": "",
                        "verification_steps": [
                            f"Verification returned unexpected type: {type(result).__name__}"
                        ],
                    }

                # Log the final response
                current_app.logger.debug(
                    f"[enhanced_validate_citation] Final response: {json.dumps(response, default=str, indent=2)}"
                )

                return jsonify(response)

            except Exception as e:
                current_app.logger.error(
                    f"[enhanced_validate_citation] Error processing verification: {str(e)}",
                    exc_info=True,
                )
                return (
                    jsonify(
                        {
                            "citation": citation,
                            "verified": False,
                            "verified_by": "Error",
                            "error": f"Error processing verification: {str(e)}",
                            "metadata": {"case_name": case_name} if case_name else {},
                            "backdrop": "",
                        }
                    ),
                    500,
                )

    # Fall back to basic validation if enhanced validation is not available or fails
    try:
        exists, method = False, "Not Implemented"
        # Try to verify using the basic verifier if available
        if "verify_citation" in globals():
            exists, method = verify_citation(citation)

        return jsonify(
            {
                "citation": citation,
                "verified": exists,
                "verified_by": method,
                "error": "" if exists else "Citation not found",
                "metadata": {"case_name": case_name} if case_name else {},
                "backdrop": "",
            }
        )
    except Exception as e:
        current_app.logger.error(
            f"[enhanced_validate_citation] Error in basic verification: {str(e)}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "citation": citation,
                    "verified": False,
                    "verified_by": "Error",
                    "error": f"Error in basic verification: {str(e)}",
                    "metadata": {"case_name": case_name} if case_name else {},
                    "backdrop": "",
                }
            ),
            500,
        )
    # Format the results for the response
    formatted_results = []
    for result in validation_results:
        try:
            # Get the citation text from the result
            citation_text = result.get("citation", "")
            # Get verification details - handle both direct fields and nested details
            details = result.get("details", {})
            if not isinstance(details, dict):
                details = {}

            # Get verification status - check multiple possible fields
            is_verified = result.get("exists", result.get("verified", False))

            # Get the verification method - check multiple possible fields
            verification_method = result.get(
                "method",
                result.get("verified_by", result.get("validation_method", "unknown")),
            )

            # Get case name from multiple possible locations
            case_name = result.get(
                "case_name",
                details.get(
                    "case_name", result.get("metadata", {}).get("case_name", "")
                ),
            )

            # Get confidence score with fallback
            confidence = float(details.get("confidence", result.get("confidence", 0.0)))

            # Get verification steps if available
            verification_steps = details.get(
                "verification_steps", result.get("verification_steps", [])
            )

            # Get sources if available
            sources = details.get("sources", result.get("sources", {}))

            # Get URL from multiple possible locations
            url = details.get(
                "url", result.get("url", result.get("metadata", {}).get("url", ""))
            )

            # Get any error message
            error_msg = result.get("error", "")

            # Create the formatted result with all required fields
            formatted_result = {
                "id": f"citation-{datetime.utcnow().timestamp()}-{len(formatted_results)}",
                "citation": citation_text,
                "citation_text": citation_text,  # Duplicate for compatibility
                "case_name": case_name,
                "verified": is_verified,
                "status": "verified" if is_verified else "unverified",
                "validation_method": verification_method,
                "confidence": confidence,
                "source": verification_method.lower(),
                "verified_by": verification_method,
                "contexts": details.get("contexts", []),
                "context": details.get("context", ""),
                "details": details,
                "metadata": {
                    **details.get("metadata", {}),
                    "url": url,
                    "source": verification_method,
                    "verified": is_verified,
                    "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
                    "case_name": case_name,
                },
                "url": url,
                "error": error_msg,
                "verification_steps": verification_steps,
                "sources": sources,
            }

            # Add the formatted result to the list
            formatted_results.append(formatted_result)

        except Exception as e:
            logger.error(f"Error formatting citation result: {str(e)}", exc_info=True)
            # Add a minimal valid result with error information
            formatted_results.append(
                {
                    "id": f"error-{datetime.utcnow().timestamp()}-{len(formatted_results)}",
                    "citation": f"Error processing citation: {str(e)[:100]}",
                    "citation_text": "Error",
                    "case_name": "Error",
                    "verified": False,
                    "status": "error",
                    "validation_method": "error",
                    "confidence": 0.0,
                    "source": "error",
                    "verified_by": "error",
                    "contexts": [],
                    "context": "",
                    "details": {"error": str(e)},
                    "metadata": {
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "url": "",
                    "error": f"Error processing citation: {str(e)}",
                    "verification_steps": [{"method": "Error", "error": str(e)}],
                    "sources": {},
                }
            )

        # Create response data
        response_data = {
            "status": "success",
            "validation_results": formatted_results,
            "total_citations": len(formatted_results),
            "verified_count": sum(
                1 for r in formatted_results if r.get("verified", False)
            ),
            "unverified_count": sum(
                1 for r in formatted_results if not r.get("verified", True)
            ),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "CaseStrainer API",
                "version": get_version(),
            },
        }

        # Ensure all data is JSON serializable
        def make_serializable(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, "isoformat"):  # Handle datetime objects
                return obj.isoformat()
            elif hasattr(obj, "__dict__"):  # Handle objects with __dict__
                return make_serializable(obj.__dict__)
            else:
                return str(obj)  # Fallback to string representation

        # Create response data
        response_data = {
            "status": "success",
            "validation_results": formatted_results,
            "total_citations": len(formatted_results),
            "valid_citations": len(
                [r for r in formatted_results if r.get("verified", False)]
            ),
            "invalid_citations": len(
                [r for r in formatted_results if not r.get("verified", False)]
            ),
            "timestamp": datetime.utcnow().isoformat(),
            "version": get_version(),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "CaseStrainer API",
            },
        }

        # Convert to JSON-serializable format
        try:
            serializable_data = make_serializable(response_data)

            # Return the JSON response
            return current_app.response_class(
                response=json.dumps(serializable_data, indent=2, ensure_ascii=False),
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


@vue_api.route("/verify-citation", methods=["POST"])
def verify_citation():
    """
    API endpoint to verify a single citation.
    Wraps the enhanced_validate_citation function for backward compatibility.
    """
    # Initialize default response
    default_error_response = {
        "verified": False,
        "error": "",
        "metadata": {},
        "backdrop": "",
        "citation": "",
    }

    try:
        # Log the incoming request
        current_app.logger.info("[verify_citation] Received request")

        # Parse request data
        try:
            data = request.get_json() or {}
            current_app.logger.debug(f"[verify_citation] Request data: {data}")
        except Exception as e:
            current_app.logger.error(f"[verify_citation] Error parsing JSON: {str(e)}")
            default_error_response["error"] = "Invalid JSON data"
            return jsonify(default_error_response), 400

        # Handle empty data
        if not data:
            default_error_response["error"] = "No data provided"
            return jsonify(default_error_response), 400

        # Initialize variables
        citation = None
        case_name = ""

        try:
            # Handle different input formats
            if isinstance(data, dict):
                current_app.logger.debug(
                    "[verify_citation] Processing dictionary input"
                )

                # Handle direct citation text
                if "citation" in data:
                    citation_obj = data["citation"]
                    current_app.logger.debug(
                        f"[verify_citation] Citation object: {citation_obj}"
                    )

                    # Handle different citation object formats
                    if isinstance(citation_obj, dict):
                        current_app.logger.debug(
                            "[verify_citation] Processing citation dict"
                        )
                        # Try to get citation text from various possible fields
                        for field in [
                            "text",
                            "citation",
                            "citation_text",
                            "citationText",
                            "citation_text_original",
                        ]:
                            if citation_obj.get(field):
                                citation = citation_obj[field]
                                current_app.logger.debug(
                                    f"[verify_citation] Extracted from citation.{field}: {citation}"
                                )
                                break
                    elif isinstance(citation_obj, str):
                        citation = citation_obj
                        current_app.logger.debug(
                            f"[verify_citation] Direct string citation: {citation}"
                        )

                # Handle direct text field
                if not citation and "text" in data:
                    citation = data["text"]
                    current_app.logger.debug(
                        f"[verify_citation] Extracted from direct text: {citation}"
                    )

                # Extract case name if available
                case_name = data.get("case_name", "")
                if not case_name and isinstance(data.get("citation"), dict):
                    case_name = data["citation"].get(
                        "name", data["citation"].get("case_name", "")
                    )

                current_app.logger.debug(
                    f"[verify_citation] Extracted case name: {case_name}"
                )

            elif isinstance(data, str):
                # If data is just a string, use it as the citation
                citation = data
                current_app.logger.debug(
                    f"[verify_citation] Direct string data: {citation}"
                )

            # Convert to string if not already and clean up
            if citation is not None:
                if not isinstance(citation, str):
                    citation = str(citation)
                # Clean up whitespace
                citation = citation.strip()
                current_app.logger.debug(
                    f"[verify_citation] Processed citation: {citation}"
                )

        except Exception as e:
            current_app.logger.error(
                f"[verify_citation] Error processing input data: {str(e)}",
                exc_info=True,
            )
            default_error_response["error"] = f"Error processing input: {str(e)}"
            return jsonify(default_error_response), 400

        # Validate we have a citation
        if not citation:
            current_app.logger.warning(
                "[verify_citation] No citation provided after processing"
            )
            default_error_response["error"] = "No valid citation found in request"
            default_error_response["citation"] = ""
            return jsonify(default_error_response), 400

        current_app.logger.info(f"[verify_citation] Validating citation: {citation}")

        # Check if this is a standard Federal Reporter citation


        try:
            current_app.logger.info(
                f"[verify_citation] Starting validation for citation: {citation}"
            )

            # Process all citations through the standard verification flow
            # including Federal Reporter citations
            current_app.logger.debug(
                "[verify_citation] Processing citation through standard verification flow"
            )

            # Prepare the citation data for validation
            citation_data = {"citation": citation}
            if case_name:
                citation_data["case_name"] = case_name

            # Log the data being passed to enhanced_validate_citation
            current_app.logger.debug(
                f"[verify_citation] Citation data for validation: {citation_data}"
            )

            # Create a new request context with the citation data
            with current_app.test_request_context(
                method="POST", json=citation_data, content_type="application/json"
            ):
                # Make sure the request context is pushed
                ctx = current_app.test_request_context()
                ctx.push()
                current_app.logger.debug(
                    f"[verify_citation] Request context created. Method: {request.method}, "
                    f"Content-Type: {request.content_type}, Data: {request.get_json(silent=True)}"
                )

                try:
                    # Call the enhanced validation function
                    result = enhanced_validate_citation()

                    # Handle the response
                    if hasattr(result, "get_json"):
                        response_data = result.get_json()
                        status_code = result.status_code
                    else:
                        response_data = result if isinstance(result, dict) else {}
                        status_code = 200
                finally:
                    # Always pop the request context
                    ctx.pop()

                # Ensure response_data is a dictionary
                if not isinstance(response_data, dict):
                    response_data = {
                        "verified": False,
                        "error": f"Unexpected response type: {type(response_data).__name__}",
                        "citation": citation,
                    }
                    status_code = 500

            # Ensure required fields are present
            if "metadata" not in response_data or response_data["metadata"] is None:
                response_data["metadata"] = {}

            if "backdrop" not in response_data:
                response_data["backdrop"] = ""

            if "citation" not in response_data:
                response_data["citation"] = citation

            # Add case name to metadata if provided
            if case_name and not response_data["metadata"].get("case_name"):
                response_data["metadata"]["case_name"] = case_name

            # Ensure we have a verified field
            if "verified" not in response_data:
                response_data["verified"] = status_code < 400

            # Log the final response
            current_app.logger.debug(
                f"[verify_citation] Final response: {response_data}"
            )

            return jsonify(response_data), status_code

        except Exception as e:
            error_msg = str(e)
            current_app.logger.error(
                f"[verify_citation] Error in direct validation call: {error_msg}",
                exc_info=True,
            )

            # Prepare error response with consistent structure
            error_response = {
                "verified": False,
                "error": f"Error in validation service: {error_msg}",
                "metadata": {"case_name": case_name} if case_name else {},
                "backdrop": "",
                "citation": citation,
            }

            # Determine appropriate status code based on error type
            status_code = 500
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                status_code = 503  # Service Unavailable

            return jsonify(error_response), status_code

    except Exception as e:
        error_msg = f"Unexpected error in verify_citation: {str(e)}"
        current_app.logger.error(f"[verify_citation] {error_msg}", exc_info=True)
        default_error_response["error"] = "An unexpected error occurred"
        return jsonify(default_error_response), 500


# API endpoint for sending feedback
@vue_api.route("/api/send-feedback", methods=["POST"])
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
            # Send email
            msg = Message(
                subject=subject,
                recipients=[MAIL_RECIPIENT],
                html=email_body,
                sender=current_app.config.get(
                    "MAIL_DEFAULT_SENDER", MAIL_DEFAULT_SENDER
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
        from ml_classifier import (
            CitationClassifier,
        )  # Update with your actual import path

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


# API endpoint for citation context
@vue_api.route("/api/citation-context", methods=["GET"])
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
        response = {
            "status": "success",
            "citation": citation,
            "metadata": metadata,
            "context": context,
            "file_link": file_link,
            "classification": classification,
            "sources": list(set(metadata.get("sources", []))),  # Remove duplicates
        }

        return jsonify(response)

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
