"""
CaseStrainer Flask application with a simple landing page.
This is a minimal version that works with the Nginx proxy.
"""

from flask import Flask, render_template_string, redirect

# Create the Flask application
app = Flask(__name__)

# Simple landing page HTML
LANDING_PAGE = """
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
                    <li class="nav-item">
                        <a class="nav-link" href="/casestrainer/api/">Original Interface</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <section class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-8 mx-auto text-center">
                    <h1 class="display-4 fw-bold">CaseStrainer</h1>
                    <p class="lead mb-4">A modern tool for legal citation analysis and verification</p>
                    <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
                        <a href="/casestrainer/api/" class="btn btn-primary btn-lg px-4 gap-3">Use Original Interface</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <div class="container py-5">
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card feature-card">
                    <div class="card-body text-center p-4">
                        <div class="feature-icon">📊</div>
                        <h3>Citation Network Visualization</h3>
                        <p>Visualize the network of citations in your legal documents to understand relationships between cases.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card feature-card">
                    <div class="card-body text-center p-4">
                        <div class="feature-icon">🤖</div>
                        <h3>ML Classifier</h3>
                        <p>Use machine learning to automatically classify and validate legal citations with high accuracy.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card feature-card">
                    <div class="card-body text-center p-4">
                        <div class="feature-icon">✅</div>
                        <h3>Multi-Source Verification</h3>
                        <p>Verify citations against multiple authoritative sources to ensure accuracy and reliability.</p>
                    </div>
                </div>
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

# Serve the landing page at the root URL
@app.route('/')
def serve_landing():
    return render_template_string(LANDING_PAGE)

# Redirect /api/ to the original CaseStrainer interface
@app.route('/api/')
def redirect_to_original():
    # In a real setup, this would redirect to the original interface
    # For now, just show a message
    return "Original CaseStrainer Interface"

if __name__ == '__main__':
    # Run the application
    app.run(host='0.0.0.0', port=5000)
