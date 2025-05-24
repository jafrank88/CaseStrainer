#!/usr/bin/env python
"""
Simple HTTP server to serve the Vue.js frontend and redirect to the API
"""
from flask import Flask, send_from_directory, redirect, render_template_string

app = Flask(__name__)

# Landing page template
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer - Citation Verification Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }
        .hero {
            background-color: #f8f9fa;
            padding: 4rem 0;
            margin-bottom: 2rem;
        }
        .feature-icon {
            font-size: 2.5rem;
            color: #0d6efd;
            margin-bottom: 1rem;
        }
        .feature-card {
            padding: 2rem;
            border-radius: 0.5rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            height: 100%;
            transition: transform 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .btn-primary {
            padding: 0.75rem 1.5rem;
            font-weight: 600;
        }
        .footer {
            background-color: #343a40;
            color: white;
            padding: 2rem 0;
            margin-top: 3rem;
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
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/casestrainer/api/">Original Interface</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="https://github.com/jafrank88/CaseStrainer" target="_blank">GitHub</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <section class="hero">
        <div class="container text-center">
            <h1 class="display-4 mb-4">CaseStrainer Citation Verification Tool</h1>
            <p class="lead mb-5">Automatically verify legal citations in briefs and other legal documents</p>
            <a href="/casestrainer/api/" class="btn btn-primary btn-lg">Launch Original Interface</a>
        </div>
    </section>

    <section class="container">
        <h2 class="text-center mb-5">Key Features</h2>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>Citation Network Visualization</h3>
                    <p>Visualize relationships between citations to identify patterns and connections across different cases.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>ML Citation Classifier</h3>
                    <p>Machine learning model trained on verified citations to identify patterns in unreliable citation formats.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <h3>Multi-Source Verification</h3>
                    <p>Cross-reference citations across multiple legal databases for comprehensive verification.</p>
                </div>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="container text-center">
            <p>© 2025 CaseStrainer | University of Washington</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


@app.route("/")
@app.route("/casestrainer/")
def serve_landing():
    """Serve the landing page"""
    return render_template_string(LANDING_PAGE)


@app.route("/api/")
@app.route("/casestrainer/api/")
def redirect_to_api():
    """Redirect to the original interface"""
    return redirect("https://wolf.law.uw.edu/casestrainer/api/")


@app.route("/vue/<path:path>")
@app.route("/casestrainer/vue/<path:path>")
def serve_vue_static(path):
    """Serve static files from the Vue.js build"""
    return send_from_directory("static/vue", path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple HTTP server for CaseStrainer")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print(f"Starting simple server on http://{args.host}:{args.port}")
    print("External access will be available at: https://wolf.law.uw.edu/casestrainer/")
    print("Local access will be available at: http://127.0.0.1:5000")

    app.run(host=args.host, port=args.port, debug=args.debug)
