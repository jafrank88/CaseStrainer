"""
CaseStrainer Flask application with a simple landing page.
This is a simplified version that works with the Nginx proxy.
"""

from flask import Flask, send_from_directory, request, jsonify, redirect, render_template_string
import os
import sys

# Create the Flask application
app = Flask(__name__)

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
            <a class="navbar-brand" href="/">CaseStrainer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/api/">Original Interface</a>
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
                <a href="/api/" class="btn btn-primary btn-lg">Use Original Interface</a>
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
@app.route('/')
def serve_landing():
    return render_template_string(LANDING_PAGE)

# Redirect /casestrainer/ to the root URL
@app.route('/casestrainer/')
def redirect_to_root():
    return redirect('/')

# Add a test endpoint
@app.route('/api/test')
def test_api():
    return jsonify({'status': 'success', 'message': 'API is working'})

# Redirect /api/ to the original CaseStrainer interface
@app.route('/api/')
def redirect_to_original():
    # This assumes the original interface is running on a different port or path
    # You'll need to modify this based on your actual setup
    return redirect('/casestrainer/api/')

# Handle URL prefix for Nginx proxy
class PrefixMiddleware:
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            # If not prefixed, just pass through
            return self.app(environ, start_response)

# Apply the prefix middleware
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/casestrainer')

if __name__ == '__main__':
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run CaseStrainer with a simple landing page')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Run the application
    app.run(host=args.host, port=args.port, debug=args.debug)
