#!/usr/bin/env python3
"""
Example of how to integrate the citation verification URL into the CaseStrainer dropdown menu
"""
import json
from flask import Flask, render_template_string, request, jsonify
from citation_verification import CitationVerifier

app = Flask(__name__)

# HTML template with dropdown that includes URL links
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CaseStrainer Citation Verification</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 8px; font-size: 16px; }
        button { padding: 8px 15px; background-color: #4285f4; color: white; border: none; cursor: pointer; }
        .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
        .result-item { margin-bottom: 10px; }
        .result-label { font-weight: bold; display: inline-block; width: 120px; }
        .dropdown { position: relative; display: inline-block; width: 100%; }
        .dropdown-content { display: none; position: absolute; background-color: #f9f9f9; width: 100%; 
                           box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 1; max-height: 300px; overflow-y: auto; }
        .dropdown-item { padding: 12px 16px; text-decoration: none; display: block; color: black; border-bottom: 1px solid #ddd; }
        .dropdown-item:hover { background-color: #f1f1f1; }
        .dropdown-item a { color: #4285f4; text-decoration: none; margin-left: 10px; }
        .dropdown-item a:hover { text-decoration: underline; }
        .show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CaseStrainer Citation Verification</h1>
        
        <div class="form-group">
            <label for="citation">Enter a legal citation:</label>
            <div class="dropdown">
                <input type="text" id="citation" name="citation" placeholder="e.g., 196 Wash. 2d 725">
                <div id="citationDropdown" class="dropdown-content">
                    <!-- Dropdown items will be added here dynamically -->
                </div>
            </div>
        </div>
        
        <button id="verifyBtn">Verify Citation</button>
        
        <div id="result" class="result" style="display: none;">
            <h2>Verification Result</h2>
            <div class="result-item">
                <span class="result-label">Citation:</span>
                <span id="resultCitation"></span>
            </div>
            <div class="result-item">
                <span class="result-label">Found:</span>
                <span id="resultFound"></span>
            </div>
            <div class="result-item">
                <span class="result-label">Source:</span>
                <span id="resultSource"></span>
            </div>
            <div class="result-item">
                <span class="result-label">Case Name:</span>
                <span id="resultCaseName"></span>
            </div>
            <div class="result-item">
                <span class="result-label">URL:</span>
                <span id="resultUrl"></span>
            </div>
            <div id="resultDetails"></div>
        </div>
    </div>
    
    <script>
        document.getElementById('verifyBtn').addEventListener('click', function() {
            const citation = document.getElementById('citation').value;
            if (!citation) return;
            
            fetch('/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ citation: citation }),
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('resultCitation').textContent = data.citation;
                document.getElementById('resultFound').textContent = data.found;
                document.getElementById('resultSource').textContent = data.source || 'N/A';
                document.getElementById('resultCaseName').textContent = data.case_name || 'N/A';
                
                // Handle URL - create a link if available
                const urlSpan = document.getElementById('resultUrl');
                urlSpan.innerHTML = '';
                if (data.url) {
                    const link = document.createElement('a');
                    link.href = data.url;
                    link.textContent = data.url;
                    link.target = '_blank';
                    urlSpan.appendChild(link);
                } else {
                    urlSpan.textContent = 'N/A';
                }
                
                // Display details
                const detailsDiv = document.getElementById('resultDetails');
                detailsDiv.innerHTML = '<h3>Details</h3>';
                if (data.details && Object.keys(data.details).length > 0) {
                    for (const [key, value] of Object.entries(data.details)) {
                        const item = document.createElement('div');
                        item.className = 'result-item';
                        item.innerHTML = `<span class="result-label">${key}:</span> <span>${value}</span>`;
                        detailsDiv.appendChild(item);
                    }
                } else {
                    detailsDiv.innerHTML += '<p>No additional details available.</p>';
                }
                
                document.getElementById('result').style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while verifying the citation.');
            });
        });
        
        // Example dropdown functionality
        const sampleCitations = [
            { citation: "196 Wash. 2d 725", case_name: "Associated Press v. Wash. State Legislature", url: "https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/" },
            { citation: "190 Wash. 2d 1", case_name: "WPEA v. Washington State Center for Childhood Deafness", url: "https://www.courtlistener.com/opinion/4505648/wpea-v-washington-state-center-for-childhood-deafness/" },
            { citation: "183 Wash. 2d 490", case_name: "State v. Arlene's Flowers", url: "https://www.courtlistener.com/opinion/4267878/state-v-arlenes-flowers/" },
            { citation: "410 U.S. 113", case_name: "Roe v. Wade", url: "https://www.courtlistener.com/opinion/108713/roe-v-wade/" }
        ];
        
        document.getElementById('citation').addEventListener('focus', function() {
            const dropdown = document.getElementById('citationDropdown');
            dropdown.innerHTML = '';
            
            sampleCitations.forEach(item => {
                const div = document.createElement('div');
                div.className = 'dropdown-item';
                div.textContent = `${item.citation} - ${item.case_name}`;
                
                // Add the URL link
                if (item.url) {
                    const link = document.createElement('a');
                    link.href = item.url;
                    link.textContent = "View Case";
                    link.target = "_blank";
                    div.appendChild(link);
                }
                
                div.addEventListener('click', function() {
                    document.getElementById('citation').value = item.citation;
                    dropdown.classList.remove('show');
                });
                
                dropdown.appendChild(div);
            });
            
            dropdown.classList.add('show');
        });
        
        // Close dropdown when clicking outside
        window.addEventListener('click', function(event) {
            if (!event.target.matches('#citation')) {
                document.getElementById('citationDropdown').classList.remove('show');
            }
        });
    </script>
</body>
</html>
"""

# Load API keys from config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        courtlistener_api_key = config.get("courtlistener_api_key")
        langsearch_api_key = config.get("langsearch_api_key")
except Exception as e:
    print(f"Error loading config.json: {e}")
    courtlistener_api_key = None
    langsearch_api_key = None

# Create the citation verifier
verifier = CitationVerifier(
    api_key=courtlistener_api_key, langsearch_api_key=langsearch_api_key
)


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    citation = data.get("citation", "")

    if not citation:
        return jsonify({"error": "No citation provided"}), 400

    result = verifier.verify_citation(citation)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
