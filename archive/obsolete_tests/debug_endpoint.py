from flask import Flask, jsonify, session, request
import logging
import sys

# Create a Flask application for debugging
app = Flask(__name__)
app.secret_key = "debug-secret-key"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@app.route("/debug_session")
def debug_session():
    """API endpoint to debug the session data."""
    try:
        # Get the user's session data
        user_citations = session.get("user_citations", [])
        logger.info(
            f"Session debug request received. Citations available: {len(user_citations)}"
        )

        # Return the session data
        return jsonify(
            {"status": "success", "session_data": {"user_citations": user_citations}}
        )
    except Exception as e:
        logger.error(f"Error in debug_session: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/debug_courtlistener_gaps")
def debug_courtlistener_gaps():
    """API endpoint to debug the CourtListener gaps functionality."""
    try:
        # Get the user's session data
        user_citations = session.get("user_citations", [])
        logger.info(
            f"CourtListener gaps debug request received. Citations available: {len(user_citations)}"
        )

        # Log all citation sources
        sources = {}
        for citation in user_citations:
            source = citation.get("source", "Unknown")
            if source in sources:
                sources[source] += 1
            else:
                sources[source] = 1

        logger.info(f"Citation sources: {sources}")

        # Filter for citations that represent gaps in the CourtListener database
        # Include all citations that weren't explicitly validated by CourtListener
        gap_citations = [
            {
                "citation_text": c["citation"],
                "case_name": c.get("found_case_name", "Unknown"),
                "found": c.get("found", False),
                "source": c.get("source", "Unknown"),
                "confidence": c.get("confidence", 0.0),
                "explanation": c.get("explanation", "Not in CourtListener database"),
                "document": "",
            }
            for c in user_citations
            if c.get("source") != "CourtListener"
        ]

        logger.info(
            f"Found {len(gap_citations)} potential gaps in CourtListener database"
        )

        # Return the gap citations (even if empty)
        return jsonify(
            {
                "status": "success",
                "citation_sources": sources,
                "citations": gap_citations,
            }
        )
    except Exception as e:
        logger.error(f"Error in debug_courtlistener_gaps: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
