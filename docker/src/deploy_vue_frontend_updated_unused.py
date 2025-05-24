"""
Deploy Vue.js Frontend for CaseStrainer with Tabbed Interface

This script creates the Vue.js frontend in the static/vue directory
with the tabbed interface for file upload, text paste, and citation viewing.
"""

import os
import shutil
import json
from pathlib import Path
import sys

# Define paths
BASE_DIR = Path(__file__).resolve().parent
VUE_SRC_DIR = BASE_DIR / "casestrainer-vue" / "src"
STATIC_VUE_DIR = BASE_DIR / "static" / "vue"

# Create static/vue directory if it doesn't exist
os.makedirs(STATIC_VUE_DIR, exist_ok=True)

# Create directories for CSS and JS
css_dir = STATIC_VUE_DIR / "css"
js_dir = STATIC_VUE_DIR / "js"
os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

# Create a simplified index.html file with proper paths and Bootstrap 5
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer - Legal Citation Verification System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css" rel="stylesheet">
    <link href="/css/main.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        .navbar {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .card-header {
            background-color: rgba(13, 110, 253, 0.1);
            border-bottom: none;
            font-weight: 600;
        }
        .tab-content {
            padding: 20px 0;
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
                        <a class="nav-link" href="#unconfirmed">Unconfirmed Citations</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#multitool">Multitool Verified</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/api/">Original Interface</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="jumbotron bg-light p-4 mb-4 rounded">
            <h1 class="display-5">CaseStrainer</h1>
            <p class="lead">
                Advanced Legal Citation Verification System
            </p>
            <hr class="my-4">
        </div>
        
        <!-- Tabbed Interface -->
        <div class="card">
            <div class="card-header">
                <ul class="nav nav-tabs card-header-tabs" id="citation-tabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="upload-tab" data-bs-toggle="tab" data-bs-target="#upload" type="button" role="tab" aria-controls="upload" aria-selected="true">
                            Upload File
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="paste-tab" data-bs-toggle="tab" data-bs-target="#paste" type="button" role="tab" aria-controls="paste" aria-selected="false">
                            Paste Text
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="multitool-tab" data-bs-toggle="tab" data-bs-target="#multitool" type="button" role="tab" aria-controls="multitool" aria-selected="false">
                            Verified with Multi-tool
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="unconfirmed-tab" data-bs-toggle="tab" data-bs-target="#unconfirmed" type="button" role="tab" aria-controls="unconfirmed" aria-selected="false">
                            Unconfirmed Citations
                        </button>
                    </li>
                </ul>
            </div>
            <div class="card-body">
                <div class="tab-content" id="citation-tabs-content">
                    <!-- Upload File Tab -->
                    <div class="tab-pane fade show active" id="upload" role="tabpanel" aria-labelledby="upload-tab">
                        <div class="card">
                            <div class="card-header">
                                <h5>Upload a Document</h5>
                            </div>
                            <div class="card-body">
                                <form action="/api/analyze" method="post" enctype="multipart/form-data">
                                    <div class="mb-3">
                                        <label for="fileUpload" class="form-label">Select a file to analyze for citations</label>
                                        <input class="form-control" type="file" id="fileUpload" name="file" accept=".pdf,.docx,.txt,.rtf,.doc,.html,.htm">
                                        <div class="form-text">Supported formats: PDF, DOCX, TXT, RTF, DOC, HTML</div>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Analyze Citations</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Paste Text Tab -->
                    <div class="tab-pane fade" id="paste" role="tabpanel" aria-labelledby="paste-tab">
                        <div class="card">
                            <div class="card-header">
                                <h5>Paste Text</h5>
                            </div>
                            <div class="card-body">
                                <form action="/api/analyze" method="post">
                                    <div class="mb-3">
                                        <label for="textInput" class="form-label">Paste text containing legal citations</label>
                                        <textarea class="form-control" id="textInput" name="text" rows="10" placeholder="Paste text from a legal document containing citations..."></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Analyze Citations</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Multitool Tab -->
                    <div class="tab-pane fade" id="multitool" role="tabpanel" aria-labelledby="multitool-tab">
                        <div class="card">
                            <div class="card-header bg-info text-white">
                                <h5>Citations Confirmed with Multi-tool</h5>
                                <p class="mb-0">These citations were verified using multiple sources but not found in CourtListener</p>
                            </div>
                            <div class="card-body">
                                <div class="text-center py-4">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p class="mt-2">Loading citations...</p>
                                </div>
                                <div class="mt-3 d-none">
                                    <div class="table-responsive">
                                        <table class="table table-striped table-hover">
                                            <thead>
                                                <tr>
                                                    <th>Citation</th>
                                                    <th>Case Name</th>
                                                    <th>Source</th>
                                                    <th>Confidence</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody id="multitool-citations">
                                                <!-- Citations will be loaded here via JavaScript -->
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Unconfirmed Tab -->
                    <div class="tab-pane fade" id="unconfirmed" role="tabpanel" aria-labelledby="unconfirmed-tab">
                        <div class="card">
                            <div class="card-header bg-danger text-white">
                                <h5>Unconfirmed Citations</h5>
                                <p class="mb-0">These citations could not be verified in any of our sources</p>
                            </div>
                            <div class="card-body">
                                <div class="text-center py-4">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p class="mt-2">Loading citations...</p>
                                </div>
                                <div class="mt-3 d-none">
                                    <div class="table-responsive">
                                        <table class="table table-striped table-hover">
                                            <thead>
                                                <tr>
                                                    <th>Citation</th>
                                                    <th>Possible Case Name</th>
                                                    <th>Confidence</th>
                                                    <th>Explanation</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody id="unconfirmed-citations">
                                                <!-- Citations will be loaded here via JavaScript -->
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white mt-5">
        <div class="container py-4">
            <div class="row">
                <div class="col-md-6">
                    <h5>CaseStrainer</h5>
                    <p>Legal Citation Verification System</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p>University of Washington School of Law</p>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/js/main.js"></script>
</body>
</html>
"""

# Write the index.html file
with open(STATIC_VUE_DIR / "index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# Create a simple CSS file
with open(css_dir / "main.css", "w", encoding="utf-8") as f:
    f.write(
        """
/* CaseStrainer Vue.js Frontend Styles */
.app-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}
.main-content {
    flex: 1;
}
.progress {
    height: 20px;
}
.nav-tabs .nav-link {
    color: #495057;
}
.nav-tabs .nav-link.active {
    color: #0d6efd;
    font-weight: 600;
}
"""
    )

# Create JavaScript to handle tab navigation and API calls
with open(js_dir / "main.js", "w", encoding="utf-8") as f:
    f.write(
        """
// CaseStrainer Vue.js Frontend Scripts
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    const triggerTabList = document.querySelectorAll('#citation-tabs button');
    triggerTabList.forEach(triggerEl => {
        triggerEl.addEventListener('click', event => {
            event.preventDefault();
            const tabTarget = document.querySelector(triggerEl.dataset.bsTarget);
            if (tabTarget) {
                // Remove active class from all tabs
                triggerTabList.forEach(t => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                // Add active class to clicked tab
                triggerEl.classList.add('active');
                triggerEl.setAttribute('aria-selected', 'true');
                
                // Hide all tab panes
                const tabPanes = document.querySelectorAll('.tab-pane');
                tabPanes.forEach(p => {
                    p.classList.remove('show', 'active');
                });
                
                // Show the target tab pane
                tabTarget.classList.add('show', 'active');
                
                // Load data for the active tab if needed
                if (triggerEl.id === 'multitool-tab') {
                    loadMultitoolCitations();
                } else if (triggerEl.id === 'unconfirmed-tab') {
                    loadUnconfirmedCitations();
                }
            }
        });
    });
    
    // Check if there's a hash in the URL to activate a specific tab
    const hash = window.location.hash.substring(1);
    if (hash) {
        const tab = document.querySelector(`#${hash}-tab`);
        if (tab) {
            tab.click();
        }
    }
    
    // Load multitool citations
    function loadMultitoolCitations() {
        fetch('/api/confirmed-with-multitool-data')
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('multitool-citations');
                const loadingIndicator = tableBody.closest('.card-body').querySelector('.text-center');
                const tableContainer = tableBody.closest('.table-responsive').parentNode;
                
                // Clear existing rows
                tableBody.innerHTML = '';
                
                if (data.citations && data.citations.length > 0) {
                    // Add new rows
                    data.citations.forEach(citation => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${citation.citation_text}</td>
                            <td>${citation.case_name || 'Unknown'}</td>
                            <td>${citation.source}</td>
                            <td>
                                <div class="progress">
                                    <div class="progress-bar ${getConfidenceClass(citation.confidence)}" 
                                         role="progressbar" 
                                         style="width: ${citation.confidence * 100}%" 
                                         aria-valuenow="${citation.confidence * 100}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                        ${Math.round(citation.confidence * 100)}%
                                    </div>
                                </div>
                            </td>
                            <td>
                                ${citation.url ? `<a href="${citation.url}" target="_blank" class="btn btn-sm btn-outline-primary">View Source</a>` : ''}
                                ${citation.context ? `<button class="btn btn-sm btn-outline-info ms-1" onclick="showContext('${citation.citation_text}', '${citation.context.replace(/'/g, "\\'")}')">View Context</button>` : ''}
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                    
                    // Hide loading indicator and show table
                    loadingIndicator.classList.add('d-none');
                    tableContainer.classList.remove('d-none');
                } else {
                    // Show no data message
                    loadingIndicator.innerHTML = '<p class="text-muted">No citations found.</p>';
                }
            })
            .catch(error => {
                console.error('Error loading multitool citations:', error);
                const tableBody = document.getElementById('multitool-citations');
                const loadingIndicator = tableBody.closest('.card-body').querySelector('.text-center');
                loadingIndicator.innerHTML = '<p class="text-danger">Error loading citations. Please try again.</p>';
            });
    }
    
    // Load unconfirmed citations
    function loadUnconfirmedCitations() {
        fetch('/api/unconfirmed-citations-data')
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('unconfirmed-citations');
                const loadingIndicator = tableBody.closest('.card-body').querySelector('.text-center');
                const tableContainer = tableBody.closest('.table-responsive').parentNode;
                
                // Clear existing rows
                tableBody.innerHTML = '';
                
                if (data.citations && data.citations.length > 0) {
                    // Add new rows
                    data.citations.forEach(citation => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${citation.citation_text}</td>
                            <td>${citation.case_name || 'Unknown'}</td>
                            <td>
                                <div class="progress">
                                    <div class="progress-bar bg-danger" 
                                         role="progressbar" 
                                         style="width: ${citation.confidence * 100}%" 
                                         aria-valuenow="${citation.confidence * 100}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                        ${Math.round(citation.confidence * 100)}%
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="text-truncate d-inline-block" style="max-width: 200px;">
                                    ${citation.explanation || 'No explanation available'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" onclick="reprocessCitation('${citation.citation_text}')">
                                    Reprocess
                                </button>
                                ${citation.context ? `<button class="btn btn-sm btn-outline-info ms-1" onclick="showContext('${citation.citation_text}', '${citation.context.replace(/'/g, "\\'")}')">Context</button>` : ''}
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                    
                    // Hide loading indicator and show table
                    loadingIndicator.classList.add('d-none');
                    tableContainer.classList.remove('d-none');
                } else {
                    // Show no data message
                    loadingIndicator.innerHTML = '<p class="text-muted">No unconfirmed citations found.</p>';
                }
            })
            .catch(error => {
                console.error('Error loading unconfirmed citations:', error);
                const tableBody = document.getElementById('unconfirmed-citations');
                const loadingIndicator = tableBody.closest('.card-body').querySelector('.text-center');
                loadingIndicator.innerHTML = '<p class="text-danger">Error loading citations. Please try again.</p>';
            });
    }
    
    // Helper function to get confidence class
    function getConfidenceClass(confidence) {
        if (confidence >= 0.8) {
            return 'bg-success';
        } else if (confidence >= 0.6) {
            return 'bg-info';
        } else if (confidence >= 0.4) {
            return 'bg-warning';
        } else {
            return 'bg-danger';
        }
    }
    
    // Expose functions to window
    window.showContext = function(citation, context) {
        alert(`Context for ${citation}:\\n\\n${context}`);
    };
    
    window.reprocessCitation = function(citation) {
        if (confirm(`Reprocess citation: ${citation}?`)) {
            fetch('/api/reprocess-citations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    citations: [citation]
                }),
            })
            .then(response => response.json())
            .then(data => {
                alert('Citation reprocessed. Please refresh the page to see updated results.');
            })
            .catch(error => {
                console.error('Error reprocessing citation:', error);
                alert('Error reprocessing citation. Please try again.');
            });
        }
    };
});
"""
    )

print(
    "Vue.js frontend with tabbed interface deployed successfully to static/vue directory!"
)
print("The application will be accessible at:")
print("  - Local: http://0.0.0.0:5000")
print("  - External: https://wolf.law.uw.edu/casestrainer/")
print("\nTo start the application, run:")
print("  D:\\Python\\python.exe app_final_vue.py --host=0.0.0.0 --port=5000")

# Ask if the user wants to restart the application
restart = input("\nDo you want to restart the application to apply changes? (y/n): ")
if restart.lower() == "y":
    print("\nRestarting the application...")
    try:
        # Find the Python process running app_final_vue.py
        import subprocess

        result = subprocess.run(
            ["tasklist", "/fi", "imagename eq python.exe", "/fo", "csv"],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().split("\n")

        # Skip the header line
        for line in lines[1:]:
            parts = line.strip('"').split('","')
            if len(parts) >= 2:
                pid = parts[1]
                # Check if this process is running app_final_vue.py
                result = subprocess.run(
                    [
                        "wmic",
                        "process",
                        "where",
                        f"ProcessId={pid}",
                        "get",
                        "CommandLine",
                    ],
                    capture_output=True,
                    text=True,
                )
                if "app_final_vue.py" in result.stdout:
                    print(f"Stopping process {pid}...")
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)

        # Start the application again
        print("Starting the application...")
        subprocess.Popen(
            [
                "D:\\Python\\python.exe",
                "app_final_vue.py",
                "--host=0.0.0.0",
                "--port=5000",
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        print("Application restarted successfully!")
    except Exception as e:
        print(f"Error restarting application: {e}")
        print("Please restart the application manually with:")
        print("  D:\\Python\\python.exe app_final_vue.py --host=0.0.0.0 --port=5000")
