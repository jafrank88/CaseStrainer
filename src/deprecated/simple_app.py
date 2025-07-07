from flask import Flask, send_from_directory, request
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "static"
    ),
    template_folder=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "templates"
    ),
)


@app.route("/")
def root():
    """Serve the Vue.js index.html file at the root."""
    logger.info(f"Accessing root path: {request.path}")
    vue_dist_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "static", "vue"
    )
    return send_from_directory(vue_dist_dir, "index.html")


@app.route("/casestrainer/")
@app.route("/casestrainer/index.html")
def serve_vue_index():
    """Serve the Vue.js index.html file."""
    logger.info(f"Accessing casestrainer path: {request.path}")
    vue_dist_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "static", "vue"
    )
    return send_from_directory(vue_dist_dir, "index.html")


@app.route("/js/<path:path>")
@app.route("/casestrainer/js/<path:path>")
def serve_js(path):
    """Serve JavaScript files."""
    logger.info(f"Serving JS file: {path}")
    js_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "static", "vue", "js"
    )
    return send_from_directory(js_dir, path)


@app.route("/css/<path:path>")
@app.route("/casestrainer/css/<path:path>")
def serve_css(path):
    """Serve CSS files."""
    logger.info(f"Serving CSS file: {path}")
    css_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "static", "vue", "css"
    )
    return send_from_directory(css_dir, path)


@app.route("/casestrainer/<path:path>")
def serve_vue_static(path):
    """Serve static files for the Vue.js frontend."""
    logger.info(f"Serving static file: {path}")
    vue_dist_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "static", "vue"
    )
    return send_from_directory(vue_dist_dir, path)


# API endpoints for testing
@app.route("/casestrainer/api/upload", methods=["POST"])
def api_upload():
    return {"error": "This endpoint is deprecated. Use /casestrainer/api/analyze."}, 410


@app.route("/casestrainer/api/text", methods=["POST"])
def api_text():
    """Handle text paste submissions."""
    logger.info("Received text analysis request")
    return {
        "success": True,
        "message": "Text analyzed successfully",
        "citations": [
            {"text": "410 U.S. 113", "valid": True, "name": "Roe v. Wade"},
            {
                "text": "347 U.S. 483",
                "valid": True,
                "name": "Brown v. Board of Education",
            },
            {"text": "5 U.S. 137", "valid": True, "name": "Marbury v. Madison"},
        ],
    }


@app.route("/casestrainer/api/url", methods=["POST"])
def api_url():
    """Handle URL submissions."""
    logger.info("Received URL analysis request")
    return {
        "success": True,
        "message": "URL content analyzed successfully",
        "citations": [
            {"text": "410 U.S. 113", "valid": True, "name": "Roe v. Wade"},
            {
                "text": "347 U.S. 483",
                "valid": True,
                "name": "Brown v. Board of Education",
            },
            {"text": "5 U.S. 137", "valid": True, "name": "Marbury v. Madison"},
        ],
    }


if __name__ == "__main__":
    print("Starting simplified CaseStrainer application on port 5000...")
    print("Access the Vue.js frontend at: http://127.0.0.1:5000/casestrainer/")
    app.run(host="0.0.0.0", port=5000, debug=True)
