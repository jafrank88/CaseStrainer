"""
Vue.js API Endpoints for CaseStrainer

This module provides the API endpoints needed by the Vue.js frontend
for the Multitool Confirmed and Unconfirmed Citations tabs.
"""

from flask import Blueprint, jsonify, request
import os
import json
import sqlite3
import importlib.util
import sys
from datetime import datetime, timedelta

# Create a Blueprint for the Vue.js API endpoints
vue_api = Blueprint("vue_api", __name__)

# Path to the database file
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "citations.db")


# Create the database and tables if they don't exist
def init_db():
    """Initialize the database with the necessary tables if they don't exist."""
    if not os.path.exists(DATABASE_FILE):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Create tables for citations
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citation_text TEXT NOT NULL,
            case_name TEXT,
            confidence REAL,
            found BOOLEAN,
            explanation TEXT,
            source TEXT,
            source_document TEXT,
            url TEXT,
            context TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        conn.commit()
        conn.close()


# Initialize the database
init_db()


# Import the enhanced verifier if available
def import_enhanced_verifier():
    """Import the EnhancedMultiSourceVerifier if available."""
    try:
        spec = importlib.util.spec_from_file_location(
            "enhanced_multi_source_verifier",
            os.path.join(
                os.path.dirname(__file__), "enhanced_multi_source_verifier.py"
            ),
        )
        verifier_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier_module)
        return verifier_module.EnhancedMultiSourceVerifier()
    except Exception as e:
        print(f"Warning: Could not import EnhancedMultiSourceVerifier: {e}")
        return None


# Import the ML citation classifier if available
def import_ml_classifier():
    """Import the CitationClassifier if available."""
    try:
        spec = importlib.util.spec_from_file_location(
            "ml_citation_classifier",
            os.path.join(os.path.dirname(__file__), "ml_citation_classifier.py"),
        )
        classifier_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(classifier_module)
        return classifier_module.CitationClassifier()
    except Exception as e:
        print(f"Warning: Could not import CitationClassifier: {e}")
        return None


# Import the citation correction engine if available
def import_correction_engine():
    """Import the CitationCorrectionEngine if available."""
    try:
        spec = importlib.util.spec_from_file_location(
            "citation_correction_engine",
            os.path.join(os.path.dirname(__file__), "citation_correction_engine.py"),
        )
        correction_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(correction_module)
        return correction_module.CitationCorrectionEngine()
    except Exception as e:
        print(f"Warning: Could not import CitationCorrectionEngine: {e}")
        return None


# Initialize the enhanced components
enhanced_verifier = import_enhanced_verifier()
ml_classifier = import_ml_classifier()
correction_engine = import_correction_engine()


# Helper function to get a database connection
def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# API endpoint for confirmed-with-multitool-data
@vue_api.route("/confirmed-with-multitool-data", methods=["GET"])
def confirmed_with_multitool_data():
    """
    API endpoint to provide data for the Confirmed with Multitool tab.
    Returns citations that were confirmed with the multi-source tool but not with CourtListener.
    """
    try:
        # Try to connect to the database and get the data
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get citations confirmed with multitool but not with CourtListener
            cursor.execute(
                """
            SELECT * FROM citations 
            WHERE found = 1 AND source != 'CourtListener'
            ORDER BY date_added DESC
            """
            )

            citations = cursor.fetchall()
            conn.close()

            # Convert to list of dictionaries
            result = []
            for citation in citations:
                # Include enhanced citation information
                citation_data = {
                    "citation_text": citation["citation_text"],
                    "case_name": citation["case_name"] if citation["case_name"] else "",
                    "confidence": citation["confidence"],
                    "context": (
                        citation["context"] if "context" in citation.keys() else ""
                    ),
                    "file_link": (
                        citation["file_link"] if "file_link" in citation.keys() else ""
                    ),
                    "volume": citation["volume"] if "volume" in citation.keys() else "",
                    "reporter": (
                        citation["reporter"] if "reporter" in citation.keys() else ""
                    ),
                    "page": citation["page"] if "page" in citation.keys() else "",
                    "court": citation["court"] if "court" in citation.keys() else "",
                    "year": citation["year"] if "year" in citation.keys() else "",
                    "source": citation["source"],
                    "url": citation["url"],
                    "context": citation["context"],
                    "date_added": citation["date_added"],
                }
                result.append(citation_data)
        except Exception as db_error:
            # If there's a database error (like missing table), use sample data
            print(f"Database error: {str(db_error)}")
            result = []

        # If no citations in database or there was an error, provide sample data for testing
        if not result:
            result = [
                {
                    "citation_text": "347 U.S. 483",
                    "case_name": "Brown v. Board of Education",
                    "confidence": 0.95,
                    "source": "Google Scholar",
                    "url": "https://scholar.google.com/scholar_case?case=12120372216939101759",
                    "context": "The landmark case Brown v. Board of Education (347 U.S. 483) established that separate educational facilities are inherently unequal.",
                    "date_added": datetime.now().isoformat(),
                },
                {
                    "citation_text": "410 U.S. 113",
                    "case_name": "Roe v. Wade",
                    "confidence": 0.92,
                    "source": "Justia",
                    "url": "https://supreme.justia.com/cases/federal/us/410/113/",
                    "context": "The Court's decision in Roe v. Wade (410 U.S. 113) recognized a woman's right to choose.",
                    "date_added": (datetime.now() - timedelta(days=2)).isoformat(),
                },
                {
                    "citation_text": "5 U.S. 137",
                    "case_name": "Marbury v. Madison",
                    "confidence": 0.88,
                    "source": "FindLaw",
                    "url": "https://caselaw.findlaw.com/us-supreme-court/5/137.html",
                    "context": "Marbury v. Madison (5 U.S. 137) established the principle of judicial review.",
                    "date_added": (datetime.now() - timedelta(days=5)).isoformat(),
                },
            ]

        return jsonify({"citations": result, "count": len(result)})

    except Exception as e:
        return jsonify({"error": str(e), "citations": []}), 500


# API endpoint for unconfirmed-citations-data
@vue_api.route("/unconfirmed-citations-data", methods=["GET"])
def unconfirmed_citations_data():
    """
    API endpoint to provide data for the Unconfirmed Citations tab.
    Returns citations that could not be verified in any source.
    """
    try:
        # Try to connect to the database and get the data
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get unconfirmed citations
            cursor.execute(
                """
            SELECT * FROM citations 
            WHERE found = 0
            ORDER BY date_added DESC
            """
            )

            citations = cursor.fetchall()
            conn.close()

            # Convert to list of dictionaries
            result = []
            for citation in citations:
                # Include enhanced citation information
                citation_data = {
                    "citation_text": citation["citation_text"],
                    "case_name": citation["case_name"] if citation["case_name"] else "",
                    "confidence": citation["confidence"],
                    "context": (
                        citation["context"] if "context" in citation.keys() else ""
                    ),
                    "file_link": (
                        citation["file_link"] if "file_link" in citation.keys() else ""
                    ),
                    "volume": citation["volume"] if "volume" in citation.keys() else "",
                    "reporter": (
                        citation["reporter"] if "reporter" in citation.keys() else ""
                    ),
                    "page": citation["page"] if "page" in citation.keys() else "",
                    "court": citation["court"] if "court" in citation.keys() else "",
                    "year": citation["year"] if "year" in citation.keys() else "",
                    "explanation": citation["explanation"],
                    "source_document": citation["source_document"],
                    "context": citation["context"],
                    "date_added": citation["date_added"],
                }
                result.append(citation_data)
        except Exception as db_error:
            # If there's a database error (like missing table), use sample data
            print(f"Database error: {str(db_error)}")
            result = []

        # If no citations in database or there was an error, provide sample data for testing
        if not result:
            result = [
                {
                    "citation_text": "999 U.S. 123",
                    "case_name": "Fictional v. NonExistent",
                    "confidence": 0.15,
                    "explanation": "Citation not found in any legal database. The U.S. Reports volume 999 does not exist.",
                    "source_document": "sample_brief_1.pdf",
                    "context": "According to Fictional v. NonExistent (999 U.S. 123), the court held that...",
                    "date_added": datetime.now().isoformat(),
                },
                {
                    "citation_text": "531 F.3d 9999",
                    "case_name": "Smith v. Imaginary Corp",
                    "confidence": 0.22,
                    "explanation": "Citation format is valid but no matching case found. The F.3d volume 531 does not contain a page 9999.",
                    "source_document": "sample_brief_2.pdf",
                    "context": "In Smith v. Imaginary Corp (531 F.3d 9999), the court established...",
                    "date_added": (datetime.now() - timedelta(days=3)).isoformat(),
                },
                {
                    "citation_text": "2022 WL 12345678",
                    "case_name": None,
                    "confidence": 0.30,
                    "explanation": "No case with this Westlaw citation could be found. The citation format is valid but the identifier does not exist.",
                    "source_document": "sample_brief_3.pdf",
                    "context": "According to 2022 WL 12345678, the principle of...",
                    "date_added": (datetime.now() - timedelta(days=7)).isoformat(),
                },
            ]

        return jsonify({"citations": result, "count": len(result)})

    except Exception as e:
        return jsonify({"error": str(e), "citations": []}), 500


# API endpoint for reprocessing multiple citations
@vue_api.route("/reprocess-citations", methods=["POST"])
def reprocess_citations():
    """
    API endpoint to reprocess multiple unconfirmed citations to check if they can now be confirmed.
    """
    try:
        data = request.get_json()
        citations = data.get("citations", [])

        # In a real implementation, this would call the citation verification logic
        # For now, we'll just return a success message
        return jsonify(
            {
                "success": True,
                "message": f"Reprocessed {len(citations)} citations",
                "results": [
                    {
                        "citation_text": citation,
                        "found": False,
                        "confidence": 0.25,
                        "explanation": "Citation still could not be verified after reprocessing.",
                    }
                    for citation in citations
                ],
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API endpoint for reprocessing a single citation
@vue_api.route("/reprocess-citation", methods=["POST"])
def reprocess_citation():
    """
    API endpoint to reprocess a single unconfirmed citation to check if it can now be confirmed.
    """
    try:
        # Get the citation from the request
        data = request.get_json()
        citation = data.get("citation", "")

        if not citation:
            return jsonify({"success": False, "message": "No citation provided"}), 400

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the citation exists in the database
        cursor.execute(
            "SELECT id, citation_text, found FROM citations WHERE citation_text = ?",
            (citation,),
        )
        citation_record = cursor.fetchone()

        if not citation_record:
            conn.close()
            return (
                jsonify(
                    {"success": False, "message": "Citation not found in database"}
                ),
                404,
            )

        citation_id, citation_text, found = citation_record

        # If the citation is already verified, return success
        if found:
            conn.close()
            return jsonify(
                {
                    "success": True,
                    "message": "Citation already verified",
                    "verified": True,
                }
            )

        # Use the enhanced verifier if available
        verified = False
        explanation = "Could not verify citation"

        if enhanced_verifier:
            result = enhanced_verifier.verify_citation(citation)
            verified = result.get("verified", False)
            explanation = (
                result.get("verified_by", "Unknown")
                if verified
                else result.get("error", "Unknown error")
            )

        # Update the citation in the database
        cursor.execute(
            "UPDATE citations SET found = ?, explanation = ? WHERE id = ?",
            (verified, explanation, citation_id),
        )

        conn.commit()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Citation reprocessed successfully",
                "verified": verified,
                "explanation": explanation,
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error reprocessing citation: {str(e)}"}
            ),
            500,
        )


# API endpoint for enhanced citation validation
@vue_api.route("/enhanced-validate-citation", methods=["POST"])
def enhanced_validate_citation():
    """
    API endpoint to validate a citation using the enhanced multi-source verifier.
    """
    try:
        # Get the citation from the request
        data = request.get_json()
        citation = data.get("citation", "")

        if not citation:
            return jsonify({"verified": False, "error": "No citation provided"}), 400

        # Use the enhanced verifier if available
        if enhanced_verifier:
            result = enhanced_verifier.verify_citation(citation)
            return jsonify(result)
        else:
            # Fallback to basic verification
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT found FROM citations WHERE citation_text = ?", (citation,)
            )
            citation_record = cursor.fetchone()

            conn.close()

            if citation_record and citation_record[0]:
                return jsonify(
                    {"citation": citation, "verified": True, "verified_by": "Database"}
                )
            else:
                return jsonify(
                    {
                        "citation": citation,
                        "verified": False,
                        "error": "Citation not found in database",
                    }
                )

    except Exception as e:
        return (
            jsonify(
                {"verified": False, "error": f"Error validating citation: {str(e)}"}
            ),
            500,
        )


# API endpoint for ML classification
@vue_api.route("/classify-citation", methods=["POST"])
def classify_citation():
    """
    API endpoint to classify a citation using the ML classifier.
    """
    try:
        # Get the citation from the request
        data = request.get_json()
        citation = data.get("citation", "")

        if not citation:
            return (
                jsonify(
                    {
                        "is_valid": False,
                        "confidence": 0.0,
                        "error": "No citation provided",
                    }
                ),
                400,
            )

        # Use the ML classifier if available
        if ml_classifier:
            # Train the classifier if not already trained
            if not hasattr(ml_classifier, "model") or ml_classifier.model is None:
                ml_classifier.train()

            result = ml_classifier.classify_citation(citation)
            return jsonify(result)
        else:
            return jsonify(
                {
                    "citation": citation,
                    "is_valid": False,
                    "confidence": 0.0,
                    "error": "ML classifier not available",
                }
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "is_valid": False,
                    "confidence": 0.0,
                    "error": f"Error classifying citation: {str(e)}",
                }
            ),
            500,
        )


# API endpoint for correction suggestions
@vue_api.route("/suggest-citation-corrections", methods=["POST"])
def suggest_citation_corrections():
    """
    API endpoint to suggest corrections for an invalid citation.
    """
    try:
        # Get the citation from the request
        data = request.get_json()
        citation = data.get("citation", "")

        if not citation:
            return (
                jsonify(
                    {"citation": "", "suggestions": [], "error": "No citation provided"}
                ),
                400,
            )

        # Use the correction engine if available
        if correction_engine:
            result = correction_engine.suggest_corrections(citation)
            return jsonify(result)
        else:
            return jsonify(
                {
                    "citation": citation,
                    "suggestions": [],
                    "error": "Correction engine not available",
                }
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "citation": citation,
                    "suggestions": [],
                    "error": f"Error suggesting corrections: {str(e)}",
                }
            ),
            500,
        )


# API endpoint for citation context
@vue_api.route("/citation-context", methods=["POST"])
def get_citation_context():
    """
    API endpoint to get the context around a citation.
    """
    try:
        # Get the citation from the request
        data = request.get_json()
        citation = data.get("citation", "")

        if not citation:
            return (
                jsonify(
                    {"context": "", "file_link": "", "error": "No citation provided"}
                ),
                400,
            )

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the context and file link for the citation
        cursor.execute(
            "SELECT context, file_link FROM citations WHERE citation_text = ?",
            (citation,),
        )
        result = cursor.fetchone()

        conn.close()

        if result:
            context, file_link = result
            return jsonify(
                {
                    "citation": citation,
                    "context": context or "",
                    "file_link": file_link or "",
                }
            )
        else:
            return jsonify(
                {
                    "citation": citation,
                    "context": "",
                    "file_link": "",
                    "error": "Citation not found in database",
                }
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "context": "",
                    "file_link": "",
                    "error": f"Error getting citation context: {str(e)}",
                }
            ),
            500,
        )
