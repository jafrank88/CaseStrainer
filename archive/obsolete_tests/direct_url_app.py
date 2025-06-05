import os
import re
import uuid
import json
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask_session import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("direct_url_app.log"), logging.StreamHandler()],
)

# Create a logger for this module
logger = logging.getLogger("direct_url_app")

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure server-side session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(
    os.environ.get("TEMP", "/tmp"), "casestrainer_sessions"
)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "casestrainer-secret-key")

# Ensure session directory exists
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
logger.info(
    f"Configured server-side session storage at {app.config['SESSION_FILE_DIR']}"
)

# Initialize server-side session
Session(app)

logger.info("Starting Direct URL Analysis Application")


# CORS preflight response builder
def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return response


# API endpoint to directly analyze a URL for citations
@app.route("/api/direct_url_analyze", methods=["POST", "OPTIONS"])
def direct_url_analyze():
    """API endpoint to directly analyze a URL for citations."""
    # Log request details for debugging
    logger.info("Direct URL analysis request received")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request data: {request.data}")

    # Handle OPTIONS request for CORS
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    try:
        # Parse the JSON data from the request
        try:
            data = request.get_json(force=True)
        except:
            # If that fails, try to parse the raw data
            data = json.loads(request.data)

        logger.info(f"JSON data received: {data}")

        if not data or "url" not in data:
            error_msg = "Missing URL in request data"
            logger.error(error_msg)
            return jsonify({"status": "error", "message": error_msg}), 400

        url = data["url"]
        logger.info(f"URL provided from request: {url}")

        # Generate a unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        logger.info(f"Analyzing URL: {url} (Analysis ID: {analysis_id})")

        # Set headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Fetch the URL content
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        # Check content type to handle different file types
        content_type = response.headers.get("Content-Type", "").lower()
        logger.info(f"Content type: {content_type}")

        # Extract text based on content type
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            # Handle PDF files (simplified for this test)
            text = "PDF content would be extracted here"
        else:
            # Handle HTML and other text-based content
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text = soup.get_text(separator=" ", strip=True)

            # Clean up the text (remove excessive whitespace)
            text = re.sub(r"\s+", " ", text).strip()

        logger.info(f"Successfully extracted text from URL (length: {len(text)})")

        # Return the URL analysis results
        return jsonify(
            {
                "status": "success",
                "analysis_id": analysis_id,
                "url": url,
                "citations_count": 0,
                "citations": [],  # In a real implementation, we would extract citations from the text
            }
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
        return (
            jsonify({"status": "error", "message": f"Error fetching URL: {str(e)}"}),
            500,
        )
    except Exception as e:
        logger.error(f"Error in direct_url_analyze: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
