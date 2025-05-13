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

# Import the API blueprint
from vue_api import api_blueprint

# Create the Flask application
app = Flask(__name__)

# Register the API blueprint
app.register_blueprint(api_blueprint, url_prefix='/api')
app.register_blueprint(api_blueprint, url_prefix='/casestrainer/api')

# Constants
DATABASE_FILE = 'citations.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# Configure the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

# Serve the Vue.js static files
@app.route('/<path:path>')
@app.route('/casestrainer/<path:path>')
def serve_static(path):
    # Check if the path is for a static asset (js, css, img, etc.)
    if path.startswith(('js/', 'css/', 'img/', 'fonts/')):
        # Extract the directory (js, css, img, fonts)
        directory = path.split('/')[0]
        # Get the file path after the directory
        file_path = '/'.join(path.split('/')[1:])
        # Serve from the Vue.js build directory
        vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue', directory)
        return send_from_directory(vue_dist_dir, file_path)
    
    # For all other paths, serve the Vue.js index.html
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
    return send_from_directory(vue_dist_dir, 'index.html')

# Serve the Vue.js index.html at the root URL
@app.route('/')
@app.route('/casestrainer/')
def serve_index():
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
    return send_from_directory(vue_dist_dir, 'index.html')

# Handle URL prefix for Nginx proxy
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        # Check if request has our prefix
        if self.prefix and environ['PATH_INFO'].startswith(self.prefix):
            # Strip the prefix
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
        
        # Ensure PATH_INFO starts with a slash
        if not environ['PATH_INFO']:
            environ['PATH_INFO'] = '/'
        elif not environ['PATH_INFO'].startswith('/'):
            environ['PATH_INFO'] = '/' + environ['PATH_INFO']
            
        # Pass the modified environment to the app
        return self.app(environ, start_response)

# Apply the prefix middleware
# This allows the application to work both with and without the /casestrainer prefix
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/casestrainer')

# Create a placeholder index.html file in the static/vue directory if it doesn't exist
vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
if not os.path.exists(vue_dist_dir):
    os.makedirs(vue_dist_dir)
    
index_html_path = os.path.join(vue_dist_dir, 'index.html')
if not os.path.exists(index_html_path):
    with open(index_html_path, 'w') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer - Modern Legal Citation Verification</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .feature-icon {
            font-size: 2.5rem;
            color: #0d6efd;
            margin-bottom: 1rem;
        }
        .feature-card {
            transition: transform 0.3s;
            height: 100%;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .navbar-brand {
            font-weight: bold;
        }
        .hero-section {
            background-color: #f8f9fa;
            padding: 4rem 0;
            margin-bottom: 2rem;
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
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/casestrainer/">Home</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <section class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-4 fw-bold">CaseStrainer</h1>
                    <p class="lead">Advanced legal citation verification system with modern Vue.js interface</p>
                    <p>CaseStrainer helps legal professionals verify citations with confidence using multiple verification sources and machine learning.</p>
                    <div class="d-grid gap-2 d-md-flex justify-content-md-start">
                        <a href="https://github.com/jafrank88/CaseStrainer" class="btn btn-primary btn-lg px-4 me-md-2" target="_blank">GitHub Repository</a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <div class="alert alert-info p-4">
                        <h4>Vue.js Frontend Under Development</h4>
                        <p>The Vue.js frontend is currently being built. Please check back soon for the full application.</p>
                        <p class="mb-0"><small>This is a placeholder page until the Vue.js build is deployed.</small></p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <div class="container mb-5">
        <h2 class="text-center mb-4">Key Features</h2>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card h-100 feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">📊</div>
                        <h5 class="card-title">Citation Network Visualization</h5>
                        <p class="card-text">Interactive network graphs showing relationships between citations and highlighting patterns.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card h-100 feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">🤖</div>
                        <h5 class="card-title">ML Citation Classifier</h5>
                        <p class="card-text">Machine learning model trained on citation data to identify patterns in unreliable citations.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card h-100 feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">🔍</div>
                        <h5 class="card-title">Multi-Source Verification</h5>
                        <p class="card-text">Verify citations against multiple authoritative sources for maximum confidence.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-light py-4 mt-auto">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <p class="mb-0">CaseStrainer - Legal Citation Verification System</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p class="mb-0"><small>University of Washington School of Law</small></p>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')
    print(f"Created placeholder index.html at {index_html_path}")
else:
    print(f"Found existing index.html at {index_html_path}")

if __name__ == '__main__':
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run CaseStrainer with Vue.js frontend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    print(f"Starting CaseStrainer with Vue.js frontend on {args.host}:{args.port}")
    
    # Check if we should run with Cheroot (production) or Flask's dev server
    use_cheroot = os.environ.get('USE_CHEROOT', 'True').lower() in ('true', '1', 't')
    
    if use_cheroot:
        try:
            from cheroot.wsgi import Server as WSGIServer
            print("Starting with Cheroot WSGI server (production mode)")
            
            server = WSGIServer((args.host, args.port), app)
            try:
                print(f"Server started on http://{args.host}:{args.port}")
                server.start()
            except KeyboardInterrupt:
                server.stop()
                print("Server stopped.")
        except ImportError:
            print("Cheroot not installed. Installing now...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cheroot"])
                print("Cheroot installed. Please restart the application.")
                sys.exit(0)
            except Exception as e:
                print(f"Failed to install Cheroot: {e}")
                print("Falling back to Flask development server")
                app.run(debug=args.debug, host=args.host, port=args.port)
    else:
        print("Starting with Flask development server")
        app.run(debug=args.debug, host=args.host, port=args.port)
