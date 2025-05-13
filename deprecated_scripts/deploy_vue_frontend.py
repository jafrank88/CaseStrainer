"""
Deploy Vue.js Frontend for CaseStrainer

This script creates a simplified Vue.js frontend in the static/vue directory
without requiring a full Node.js build process.
"""

import os
import shutil
import json
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).resolve().parent
VUE_SRC_DIR = BASE_DIR / 'casestrainer-vue' / 'src'
STATIC_VUE_DIR = BASE_DIR / 'static' / 'vue'

# Create static/vue directory if it doesn't exist
os.makedirs(STATIC_VUE_DIR, exist_ok=True)

# Create a simplified index.html file with proper paths
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer - Legal Citation Verification System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        .hero {
            background-color: #0d6efd;
            color: white;
            padding: 3rem 0;
            margin-bottom: 2rem;
        }
        .feature-card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            height: 100%;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #0d6efd;
        }
        footer {
            background-color: #343a40;
            color: white;
            padding: 2rem 0;
            margin-top: 3rem;
        }
        .btn-primary {
            padding: 0.5rem 1.5rem;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">CaseStrainer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="#">Home</a>
                    </li>
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

    <section class="hero text-center">
        <div class="container">
            <h1 class="display-4">CaseStrainer</h1>
            <p class="lead">Advanced Legal Citation Verification System</p>
            <a href="/casestrainer/api/" class="btn btn-light btn-lg mt-3">Access Original Interface</a>
        </div>
    </section>

    <section class="container my-5">
        <div class="row mb-4">
            <div class="col-md-12 text-center">
                <h2>Welcome to the New CaseStrainer</h2>
                <p class="lead">We're transitioning to a modern Vue.js interface with enhanced features</p>
            </div>
        </div>
        
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card feature-card p-4">
                    <div class="card-body text-center">
                        <div class="feature-icon">&#128202;</div>
                        <h3 class="card-title">Citation Network Visualization</h3>
                        <p class="card-text">Interactive network graphs showing relationships between citations and highlighting patterns of unconfirmed citations.</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card feature-card p-4">
                    <div class="card-body text-center">
                        <div class="feature-icon">&#128269;</div>
                        <h3 class="card-title">ML Citation Classifier</h3>
                        <p class="card-text">Machine learning model trained on confirmed/unconfirmed citations to identify patterns in unreliable citation formats.</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card feature-card p-4">
                    <div class="card-body text-center">
                        <div class="feature-icon">&#128260;</div>
                        <h3 class="card-title">Multi-Source Verification</h3>
                        <p class="card-text">Cross-reference citations across multiple legal databases to ensure accuracy and reliability.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="container my-5">
        <div class="row">
            <div class="col-md-6 offset-md-3 text-center">
                <div class="alert alert-info p-4">
                    <h4>Vue.js Interface Coming Soon</h4>
                    <p>Our new Vue.js frontend is under development. For now, please use the original interface to access all features.</p>
                    <a href="/casestrainer/api/" class="btn btn-primary">Go to Original Interface</a>
                </div>
            </div>
        </div>
    </section>

    <footer class="bg-dark text-white">
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
"""

# Write the index.html file
with open(STATIC_VUE_DIR / 'index.html', 'w') as f:
    f.write(index_html)

# Copy CSS and JS files if they exist
css_dir = STATIC_VUE_DIR / 'css'
js_dir = STATIC_VUE_DIR / 'js'
os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

# Create a simple CSS file
with open(css_dir / 'main.css', 'w') as f:
    f.write("""
/* CaseStrainer Vue.js Frontend Styles */
.app-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}
.main-content {
    flex: 1;
}
""")

# Create a simple JavaScript file
with open(js_dir / 'main.js', 'w') as f:
    f.write("""
// CaseStrainer Vue.js Frontend Scripts
console.log('CaseStrainer Vue.js Frontend loaded');
""")

print("Vue.js frontend deployed successfully to static/vue directory!")
print("The application will be accessible at:")
print("  - Local: http://127.0.0.1:5000")
print("  - External: https://wolf.law.uw.edu/casestrainer/")
