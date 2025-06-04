#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CaseStrainer - Legal Citation Verification System

This application helps legal professionals verify case citations in legal documents.
It uses multiple verification sources to identify unconfirmed or hallucinated citations.
"""

import sys
import os
import json
import time
import uuid
import socket
import hashlib
import logging
import sqlite3
import threading
import traceback
import re
import urllib.parse
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    send_from_directory,
    send_file,
    make_response,
)
from functools import lru_cache
from test_citations import get_random_test_citations

# Import Enhanced Validator functionality if available
try:
    from enhanced_validator_production import (
        extract_citations,
        validate_citation,
        extract_text_from_file,
    )

    print("Enhanced Validator functionality imported successfully")
    USE_ENHANCED_VALIDATOR = True
except ImportError:
    print("Enhanced Validator functionality not available")
    USE_ENHANCED_VALIDATOR = False

# Import citation correction module
try:
    from citation_correction import get_correction_suggestions

    print("Citation correction module imported successfully")
    USE_CORRECTION_SUGGESTIONS = True
except ImportError:
    print("Citation correction module not available")
    USE_CORRECTION_SUGGESTIONS = False

# Import the MultiSourceVerifier
try:
    from fixed_multi_source_verifier import MultiSourceVerifier

    print("Successfully imported MultiSourceVerifier from fixed_multi_source_verifier")
    USE_MULTI_SOURCE_VERIFIER = True
except ImportError:
    print("Could not import MultiSourceVerifier, using standard verification")
    USE_MULTI_SOURCE_VERIFIER = False

# Create the Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
app.logger.setLevel(logging.INFO)

# Constants
UPLOAD_FOLDER = "uploads"
DATABASE_FILE = "citations.db"
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "rtf", "odt", "html", "htm"}
DEFAULT_API_KEY = None  # Will be loaded from config.json

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Upload folder created at: {UPLOAD_FOLDER}")
else:
    print(f"Upload folder exists at: {UPLOAD_FOLDER}")

# Check if upload folder is writable
if os.access(UPLOAD_FOLDER, os.W_OK):
    print("Upload folder is writable")
else:
    print("WARNING: Upload folder is not writable")

# Create cache directory if it doesn't exist
CACHE_DIR = "citation_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
    print(f"Cache directory created at: {CACHE_DIR}")
else:
    print(f"Cache directory exists at: {CACHE_DIR}")

# Load API key from config file
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get("api_key")
        LANGSEARCH_API_KEY = config.get("langsearch_api_key")
        print(
            f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}..."
            if DEFAULT_API_KEY
            else "No API key found in config.json"
        )
        print(
            f"Loaded LangSearch API key from config.json: {LANGSEARCH_API_KEY[:5]}..."
            if LANGSEARCH_API_KEY
            else "No LangSearch API key found in config.json"
        )
except Exception as e:
    print(f"Error loading config.json: {e}")
    DEFAULT_API_KEY = None
    LANGSEARCH_API_KEY = None

# Load landmark cases database
try:
    with open("landmark_cases.json", "r") as f:
        LANDMARK_CASES = json.load(f)
        print(f"Loaded landmark cases database with {len(LANDMARK_CASES)} cases")
except Exception as e:
    print(f"Error loading landmark_cases.json: {e}")
    LANDMARK_CASES = {}

# Dictionary to store analysis results
analysis_results = {}


# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())


# Routes
@app.route("/")
def index():
    return render_template("fixed_form_ajax.html")


@app.route("/downloaded_briefs/<path:filename>")
def serve_downloaded_briefs(filename):
    """Serve files from the downloaded_briefs directory."""
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_briefs"),
        filename,
    )


@app.route("/downloaded_briefs/exports/<path:filename>")
def serve_exports(filename):
    """Serve files from the exports directory."""
    return send_from_directory(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "downloaded_briefs", "exports"
        ),
        filename,
    )


@app.route("/analyze", methods=["GET", "POST", "OPTIONS"])
def analyze():
    # Handle preflight OPTIONS request for CORS
    if request.method == "OPTIONS":
        response = jsonify({"status": "success"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    if request.method == "POST":
        print("\n\n==== ANALYZE ENDPOINT CALLED =====")
        print(f"Request method: {request.method}")
        print(f"Request headers: {request.headers}")
        print(f"Content-Type: {request.content_type}")
        print(f"Request form data: {request.form}")
        print(
            f"Request files: {list(request.files.keys()) if request.files else 'No files'}"
        )

        # Debug the raw request data
        try:
            raw_data = request.get_data()
            print(f"Raw request data length: {len(raw_data)} bytes")
            print(f"Raw request data (first 100 bytes): {raw_data[:100]}")
        except Exception as e:
            print(f"Error reading raw request data: {e}")
            traceback.print_exc()

        try:
            # Generate a unique analysis ID
            analysis_id = generate_analysis_id()
            print(f"Generated analysis ID: {analysis_id}")

            # Initialize variables
            brief_text = None
            file_path = None

            # Get the API key if provided, otherwise use the default from config.json
            api_key = DEFAULT_API_KEY  # Use the default API key loaded from config.json
            if "api_key" in request.form and request.form["api_key"].strip():
                api_key = request.form["api_key"].strip()
                print(f"API key provided in form: {api_key[:5]}...")
            else:
                print(
                    f"Using default API key from config.json: {api_key[:5]}..."
                    if api_key
                    else "No API key provided or found in config.json"
                )

            # Check if a file was uploaded
            if "file" in request.files:
                file = request.files["file"]
                print(
                    f"File object: {file}, filename: {file.filename if file else 'None'}"
                )
                if file and file.filename and allowed_file(file.filename):
                    print(f"File uploaded: {file.filename}")
                    filename = secure_filename(file.filename)

                    # Ensure upload folder exists
                    try:
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        print(f"Ensured upload folder exists: {UPLOAD_FOLDER}")
                    except Exception as e:
                        print(f"Error creating upload folder: {e}")
                        traceback.print_exc()
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"Error creating upload folder: {str(e)}",
                                }
                            ),
                            500,
                        )

                    # Save file
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    print(f"Attempting to save file to: {file_path}")
                    try:
                        file.save(file_path)
                        print(f"File successfully saved to: {file_path}")

                        # Debug: Print file size and first few bytes
                        try:
                            file_size = os.path.getsize(file_path)
                            print(f"File size: {file_size} bytes")
                            with open(file_path, "rb") as f:
                                first_bytes = f.read(100)
                                print(f"First few bytes: {first_bytes}")
                        except Exception as e:
                            print(f"Error reading file: {e}")
                            traceback.print_exc()
                            return (
                                jsonify(
                                    {
                                        "status": "error",
                                        "message": f"Error reading saved file: {str(e)}",
                                    }
                                ),
                                500,
                            )
                    except Exception as e:
                        print(f"Error saving file: {e}")
                        traceback.print_exc()
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"Error saving file: {str(e)}",
                                }
                            ),
                            500,
                        )
                else:
                    error_msg = f"File validation failed: filename={file.filename if file else 'None'}, allowed={allowed_file(file.filename) if file and file.filename else False}"
                    print(error_msg)
                    return jsonify({"status": "error", "message": error_msg}), 400
            else:
                print("No file found in request.files")

            # Check if a file path was provided
            if "file_path" in request.form:
                file_path = request.form["file_path"].strip()
                print(f"File path provided: {file_path}")

                # Handle file:/// URLs
                if file_path.startswith("file:///"):
                    file_path = file_path[8:]  # Remove 'file:///' prefix

                # Check if the file exists
                if not os.path.isfile(file_path):
                    print(f"File not found: {file_path}")
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File not found: {file_path}",
                            }
                        ),
                        404,
                    )

                # Check if the file extension is allowed
                if not allowed_file(file_path):
                    print(f"File extension not allowed: {file_path}")
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"File extension not allowed: {file_path}",
                            }
                        ),
                        400,
                    )

                print(f"Using file from path: {file_path}")

                # Debug: Print file size and first few bytes
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"File size: {file_size} bytes")
                    with open(file_path, "rb") as f:
                        first_bytes = f.read(100)
                        print(f"First few bytes: {first_bytes}")
                except Exception as e:
                    print(f"Error reading file: {e}")

            # Get brief text from form if provided
            if "brief_text" in request.form and request.form["brief_text"].strip():
                brief_text = request.form["brief_text"].strip()
                print(f"Brief text provided: {brief_text[:100]}...")
            elif "briefText" in request.form:  # For backward compatibility
                brief_text = request.form["briefText"]
                print(f"Brief text from form: {brief_text[:100]}...")

            # Check if we have either text or a file
            if not brief_text and not file_path:
                print("No text or file provided")
                return (
                    jsonify({"status": "error", "message": "No text or file provided"}),
                    400,
                )

            # Log before starting analysis
            print(f"About to start analysis with ID: {analysis_id}")
            print(f"Brief text: {'Present' if brief_text else 'None'}")
            print(f"File path: {file_path}")
            print(f"API key: {'Present' if api_key else 'None'}")

            # Extract text from file if needed and USE_ENHANCED_VALIDATOR is available
            if file_path and not brief_text and USE_ENHANCED_VALIDATOR:
                try:
                    brief_text = extract_text_from_file(file_path)
                    print(
                        f"Extracted {len(brief_text)} characters from file using Enhanced Validator"
                    )
                except Exception as e:
                    print(
                        f"Error extracting text from file with Enhanced Validator: {e}"
                    )
                    traceback.print_exc()

            # If we have text and Enhanced Validator is available, use it for immediate validation
            if brief_text and USE_ENHANCED_VALIDATOR:
                try:
                    # Extract citations from text
                    extracted_citations = extract_citations(brief_text)
                    print(f"Extracted {len(extracted_citations)} citations from text")

                    # Validate each citation
                    citations = []
                    for citation_text in extracted_citations:
                        validation_result = validate_citation(citation_text)

                        # Format the result to match the expected format by the Vue.js frontend
                        citations.append(
                            {
                                "citation": citation_text,
                                "found": validation_result["verified"],
                                "url": None,  # Not provided by Enhanced Validator
                                "found_case_name": validation_result["case_name"],
                                "name_match": (
                                    True if validation_result["verified"] else False
                                ),
                                "confidence": (
                                    1.0 if validation_result["verified"] else 0.0
                                ),
                                "explanation": (
                                    f"Validated by {validation_result['validation_method']}"
                                    if validation_result["verified"]
                                    else "Citation not found"
                                ),
                                "source": (
                                    validation_result["validation_method"]
                                    if validation_result["verified"]
                                    else None
                                ),
                            }
                        )

                    print(
                        f"Validated {len(citations)} citations using Enhanced Validator"
                    )

                    # Return immediate results
                    return jsonify(
                        {
                            "status": "success",
                            "analysis_id": analysis_id,
                            "citations": citations,
                            "file_name": (
                                os.path.basename(file_path) if file_path else None
                            ),
                            "citations_count": len(citations),
                        }
                    )
                except Exception as e:
                    print(f"Error using Enhanced Validator: {e}")
                    traceback.print_exc()
                    # Fall through to standard analysis

            # If Enhanced Validator is not available or failed, use standard analysis
            print("Using standard asynchronous analysis")
            analysis_thread = threading.Thread(
                target=run_analysis, args=(analysis_id, brief_text, file_path, api_key)
            )
            analysis_thread.daemon = True
            analysis_thread.start()
            print(f"Analysis thread started with ID: {analysis_id}")

            # Return the analysis ID
            return jsonify(
                {
                    "status": "success",
                    "message": "Analysis started",
                    "analysis_id": analysis_id,
                }
            )
        except Exception as e:
            print(f"Error in analyze endpoint: {e}")
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500
    else:
        # For GET requests, just return an empty response
        return jsonify({})


@app.route("/status")
def status():
    """Get the status of an analysis."""
    print("\n\n==== STATUS ENDPOINT CALLED =====")

    # Get the analysis ID from the query string
    analysis_id = request.args.get("id")
    if not analysis_id:
        return jsonify({"status": "error", "message": "No analysis ID provided"}), 400

    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({"status": "error", "message": "Analysis not found"}), 404

    # Return the current status
    response = jsonify(analysis_results[analysis_id])

    # Add CORS headers
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


# Function to run the citation analysis with the CourtListener API and multi-source verification
def run_analysis(analysis_id, brief_text=None, file_path=None, api_key=None):
    """
    Run the citation analysis with the CourtListener API and multi-source verification.

    Args:
        analysis_id (str): Unique ID for this analysis
        brief_text (str, optional): Text of the brief to analyze
        file_path (str, optional): Path to the file to analyze
        api_key (str, optional): CourtListener API key

    Returns:
        dict: Analysis results
    """
    print(f"Running analysis {analysis_id}")

    # Log whether we're using enhanced verification
    if USE_MULTI_SOURCE_VERIFIER:
        print("Using enhanced multi-source verification for this analysis")

    # Log system info
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"UPLOAD_FOLDER path: {os.path.abspath(UPLOAD_FOLDER)}")

    # Check if upload folder exists and is writable
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"WARNING: Upload folder does not exist: {UPLOAD_FOLDER}")
        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            print(f"Created upload folder: {UPLOAD_FOLDER}")
        except Exception as e:
            print(f"ERROR: Could not create upload folder: {e}")

    # Initialize the analysis results
    analysis_results[analysis_id] = {
        "status": "processing",
        "message": "Analysis started",
        "citations": [],
        "completed": False,
        "start_time": time.time(),
    }

    # Initialize the MultiSourceVerifier if available
    multi_source_verifier = None
    if USE_MULTI_SOURCE_VERIFIER:
        try:
            multi_source_verifier = MultiSourceVerifier(api_key=api_key)
            print("MultiSourceVerifier initialized")
        except Exception as e:
            print(f"Error initializing MultiSourceVerifier: {e}")
            traceback.print_exc()

    try:
        # Process the file if provided
        if file_path and not brief_text:
            print(f"Processing file: {file_path}")

            # Extract text from the file
            try:
                # Use the extract_text_from_file function from enhanced_validator_production if available
                if USE_ENHANCED_VALIDATOR:
                    brief_text = extract_text_from_file(file_path)
                    print(
                        f"Extracted {len(brief_text)} characters from file using Enhanced Validator"
                    )
                else:
                    # Otherwise use a simple text extraction
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        brief_text = f.read()
                    print(
                        f"Extracted {len(brief_text)} characters from file using simple text extraction"
                    )
            except Exception as e:
                print(f"Error extracting text from file: {e}")
                traceback.print_exc()
                analysis_results[analysis_id]["status"] = "error"
                analysis_results[analysis_id][
                    "message"
                ] = f"Error extracting text from file: {str(e)}"
                analysis_results[analysis_id]["completed"] = True
                return

        # Check if we have text to analyze
        if not brief_text:
            print("No text to analyze")
            analysis_results[analysis_id]["status"] = "error"
            analysis_results[analysis_id]["message"] = "No text to analyze"
            analysis_results[analysis_id]["completed"] = True
            return

        # Extract citations from the text
        citations = []
        try:
            # Use the extract_citations function from enhanced_validator_production if available
            if USE_ENHANCED_VALIDATOR:
                extracted_citations = extract_citations(brief_text)
                print(
                    f"Extracted {len(extracted_citations)} citations from text using Enhanced Validator"
                )

                # Validate each citation
                for citation_text in extracted_citations:
                    validation_result = validate_citation(citation_text)

                    # Format the result to match the expected format by the Vue.js frontend
                    citations.append(
                        {
                            "citation": citation_text,
                            "found": validation_result["verified"],
                            "url": None,  # Not provided by Enhanced Validator
                            "found_case_name": validation_result["case_name"],
                            "name_match": (
                                True if validation_result["verified"] else False
                            ),
                            "confidence": 1.0 if validation_result["verified"] else 0.0,
                            "explanation": (
                                f"Validated by {validation_result['validation_method']}"
                                if validation_result["verified"]
                                else "Citation not found"
                            ),
                            "source": (
                                validation_result["validation_method"]
                                if validation_result["verified"]
                                else None
                            ),
                        }
                    )
            else:
                # Otherwise use the MultiSourceVerifier if available
                if multi_source_verifier:
                    print("Using MultiSourceVerifier to extract and validate citations")
                    citations = multi_source_verifier.extract_and_validate_citations(
                        brief_text
                    )
                else:
                    print("No citation extraction method available")
                    analysis_results[analysis_id]["status"] = "error"
                    analysis_results[analysis_id][
                        "message"
                    ] = "No citation extraction method available"
                    analysis_results[analysis_id]["completed"] = True
                    return
        except Exception as e:
            print(f"Error extracting citations: {e}")
            traceback.print_exc()
            analysis_results[analysis_id]["status"] = "error"
            analysis_results[analysis_id][
                "message"
            ] = f"Error extracting citations: {str(e)}"
            analysis_results[analysis_id]["completed"] = True
            return

        # Update the analysis results
        analysis_results[analysis_id]["status"] = "success"
        analysis_results[analysis_id]["message"] = "Analysis completed"
        analysis_results[analysis_id]["citations"] = citations
        analysis_results[analysis_id]["citations_count"] = len(citations)
        analysis_results[analysis_id]["completed"] = True
        analysis_results[analysis_id]["end_time"] = time.time()
        analysis_results[analysis_id]["duration"] = (
            analysis_results[analysis_id]["end_time"]
            - analysis_results[analysis_id]["start_time"]
        )

        print(f"Analysis completed for ID: {analysis_id}")
        print(f"Found {len(citations)} citations")
        print(
            f"Analysis duration: {analysis_results[analysis_id]['duration']:.2f} seconds"
        )

    except Exception as e:
        print(f"Error in run_analysis: {e}")
        traceback.print_exc()
        analysis_results[analysis_id]["status"] = "error"
        analysis_results[analysis_id]["message"] = f"Error: {str(e)}"
        analysis_results[analysis_id]["completed"] = True


if __name__ == "__main__":
    # Get command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Run CaseStrainer")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--use-cheroot",
        action="store_true",
        help="Use Cheroot WSGI server (production mode)",
    )
    args = parser.parse_args()

    # Check if we should run with Cheroot (production) or Flask's dev server
    use_cheroot = args.use_cheroot or os.environ.get(
        "USE_CHEROOT", "False"
    ).lower() in ("true", "1", "t")

    # Log server information
    print(f"Starting CaseStrainer on {args.host}:{args.port}")
    print(f"Debug mode: {args.debug}")
    print(f"Using Cheroot: {use_cheroot}")

    if use_cheroot:
        try:
            from cheroot.wsgi import Server as WSGIServer

            print("Starting with Cheroot WSGI server (production mode)")
            server = WSGIServer((args.host, args.port), app)
            try:
                server.start()
            except KeyboardInterrupt:
                server.stop()
        except ImportError:
            print("Cheroot not installed, falling back to Flask's development server")
            app.run(host=args.host, port=args.port, debug=args.debug)
    else:
        print("Starting with Flask's development server")
        app.run(host=args.host, port=args.port, debug=args.debug)
