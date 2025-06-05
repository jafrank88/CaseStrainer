"""
CaseStrainer Flask application with Nginx compatibility.
This is a simplified version that works with the Nginx proxy.
"""

from flask import (
    Flask,
    send_from_directory,
    jsonify,
    render_template_string,
)
import os

# Create the Flask application
app = Flask(__name__)

# Constants
DATABASE_FILE = "citations.db"
UPLOAD_FOLDER = "uploads"

# Configure the upload folder
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


# Simple landing page HTML
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding-top: 20px;
        }
        .feature-icon {
            font-size: 2.5rem;
            color: #0d6efd;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/casestrainer/">CaseStrainer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/casestrainer/api/">Original Interface</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="https://github.com/jafrank88/CaseStrainer">GitHub</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container my-5">
        <div class="row text-center">
            <div class="col-lg-12">
                <h1 class="display-4">Welcome to CaseStrainer</h1>
                <p class="lead">A modern tool for legal citation analysis and verification</p>
                <hr class="my-4">
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-md-4 text-center">
                <div class="feature-icon">📊</div>
                <h3>Citation Network Visualization</h3>
                <p>Visualize the network of citations in your legal documents to understand relationships between cases.</p>
            </div>
            <div class="col-md-4 text-center">
                <div class="feature-icon">🤖</div>
                <h3>ML Classifier</h3>
                <p>Use machine learning to automatically classify and validate legal citations with high accuracy.</p>
            </div>
            <div class="col-md-4 text-center">
                <div class="feature-icon">✅</div>
                <h3>Multi-Source Verification</h3>
                <p>Verify citations against multiple authoritative sources to ensure accuracy and reliability.</p>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-lg-12 text-center">
                <a href="/casestrainer/api/" class="btn btn-primary btn-lg">Use Original Interface</a>
            </div>
        </div>
    </div>

    <footer class="bg-light py-4 mt-5">
        <div class="container text-center">
            <p>CaseStrainer &copy; 2023 - University of Washington School of Law</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


# Serve the landing page at the root URL
@app.route("/")
@app.route("/casestrainer/")
def serve_landing():
    return render_template_string(LANDING_PAGE)


# API endpoints
@app.route("/api/test")
@app.route("/casestrainer/api/test")
def test_api():
    return jsonify({"status": "success", "message": "API is working"})


# Redirect /api/ to the original CaseStrainer interface
@app.route("/api/")
@app.route("/casestrainer/api/")
def redirect_to_original():
    # In a real setup, this would redirect to the original interface
    # For now, just show a message
    return "Original CaseStrainer Interface"


# Serve static files
@app.route("/static/<path:path>")
@app.route("/casestrainer/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    # Get command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Run CaseStrainer with Nginx compatibility"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()

    # Run the application
    app.run(host=args.host, port=args.port, debug=args.debug)
