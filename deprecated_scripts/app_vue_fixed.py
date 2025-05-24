"""
CaseStrainer Flask application with Vue.js frontend.
This is the main entry point for the CaseStrainer application.
"""

from flask import Flask, send_from_directory, request, jsonify, redirect, url_for
import os
import sys
import json
import sqlite3
from werkzeug.utils import secure_filename

# Import the API blueprint from the fixed file
from vue_api_fixed import api_blueprint

# Create the Flask application
app = Flask(__name__)

# Register the API blueprint with different names for each URL prefix
app.register_blueprint(api_blueprint, url_prefix="/api")
app.register_blueprint(
    api_blueprint, url_prefix="/casestrainer/api", name="api_with_prefix"
)

# Constants
DATABASE_FILE = "citations.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "doc"}

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


# Serve the Vue.js static files
@app.route("/<path:path>")
@app.route("/casestrainer/<path:path>")
def serve_static(path):
    # Check if the path is for a static asset (js, css, img, etc.)
    if path.startswith(("js/", "css/", "img/", "fonts/")):
        # Extract the directory (js, css, img, fonts)
        directory = path.split("/")[0]
        # Get the file path after the directory
        file_path = "/".join(path.split("/")[1:])
        # Serve the file from the static/vue directory
        return send_from_directory(os.path.join("static", "vue", directory), file_path)

    # For all other paths, serve the index.html file
    return send_from_directory(os.path.join("static", "vue"), "index.html")


# Serve the Vue.js index.html at the root URL
@app.route("/")
@app.route("/casestrainer/")
def serve_index():
    return send_from_directory(os.path.join("static", "vue"), "index.html")


# Handle URL prefix for Nginx proxy
class PrefixMiddleware:
    def __init__(self, app, prefix=""):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"].startswith(self.prefix):
            environ["PATH_INFO"] = environ["PATH_INFO"][len(self.prefix) :]
            environ["SCRIPT_NAME"] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response("404", [("Content-Type", "text/plain")])
            return [b"Not Found"]


# Apply the prefix middleware
# This allows the application to work both with and without the /casestrainer prefix
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix="/casestrainer")


# Default landing page for users who haven't built the Vue.js frontend yet
@app.route("/default")
def default_landing():
    return """
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
                <p class="lead">The Vue.js frontend is not yet built. Please run the build script first.</p>
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


if __name__ == "__main__":
    # Get command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Run CaseStrainer with Vue.js frontend"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()

    # Check if the Vue.js frontend is built
    vue_dist_dir = os.path.join(os.path.dirname(__file__), "static", "vue")
    if not os.path.exists(vue_dist_dir) or not os.path.exists(
        os.path.join(vue_dist_dir, "index.html")
    ):
        print("WARNING: Vue.js frontend is not built. Serving default landing page.")
        print("To build the Vue.js frontend, run: build_and_deploy_vue.bat")

        # Redirect root to default landing page
        @app.route("/")
        @app.route("/casestrainer/")
        def redirect_to_default():
            return redirect("/default")

    # Run the application
    app.run(host=args.host, port=args.port, debug=args.debug)
