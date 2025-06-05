#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for creating a direct URL endpoint in CaseStrainer
This script adds a direct URL endpoint to the CaseStrainer application
"""

import os
import sys
import logging
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_url_endpoint")


def create_direct_url_endpoint():
    """Create a direct URL endpoint for CaseStrainer."""
    logger.info("Creating direct URL endpoint for CaseStrainer")

    # Path to the app_final_vue.py file
    app_path = os.path.join(os.getcwd(), "app_final_vue.py")

    if not os.path.exists(app_path):
        logger.error(f"app_final_vue.py not found at {app_path}")
        return False

    # Read the current content of the file
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if the direct URL endpoint already exists
    if "def direct_url_analyze():" in content:
        logger.info("Direct URL endpoint already exists")
        return True

    # Find a good insertion point after the fetch_url function
    insertion_point = content.find('print("Vue.js routes added to Flask application")')

    if insertion_point == -1:
        logger.error("Could not find insertion point")
        return False

    # Create the direct URL endpoint function
    direct_url_endpoint = """
# Add a direct URL analyze endpoint
@app.route('/api/direct_url_analyze', methods=['POST', 'OPTIONS'])
@app.route('/casestrainer/api/direct_url_analyze', methods=['POST', 'OPTIONS'])
def direct_url_analyze():
    \"\"\"API endpoint to directly analyze a URL for citations.\"\"\"
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    try:
        # Get URL from request
        data = request.get_json()
        if not data or 'url' not in data:
            app.logger.error("No URL provided in request")
            return jsonify({
                'status': 'error',
                'message': 'No URL provided'
            }), 400
        
        url = data['url']
        app.logger.info(f"Analyzing URL: {url}")
        
        # Generate a unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        
        # Clear previous citation data in session
        session.pop('user_citations', None)
        app.logger.info("Cleared previous citation data in user session")
        
        # Initialize session data with sample citation data
        initialize_session_data()
        
        # Fetch URL content
        try:
            # Set headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Fetch the URL content
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            # Check content type to handle different file types
            content_type = response.headers.get('Content-Type', '').lower()
            app.logger.info(f"Content type: {content_type}")
            
            # Create uploads directory if it doesn't exist
            os.makedirs('uploads', exist_ok=True)
            
            # Variable to store extracted text
            document_text = None
            
            # Handle PDF files
            if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                app.logger.info("Detected PDF file, extracting text")
                
                # Save PDF to temporary file
                pdf_path = os.path.join('uploads', f"{analysis_id}_url.pdf")
                
                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                app.logger.info(f"PDF saved to: {pdf_path}")
                
                # Extract text from PDF
                document_text = extract_text_from_file(pdf_path)
                app.logger.info(f"Extracted {len(document_text)} characters from PDF")
            else:
                # Handle HTML and other text-based content
                app.logger.info("Processing as HTML/text content")
                
                # Parse the HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text content
                document_text = soup.get_text(separator=' ', strip=True)
                
                # Clean up the text (remove excessive whitespace)
                document_text = re.sub(r'\\s+', ' ', document_text).strip()
            
            app.logger.info(f"Successfully extracted {len(document_text)} characters from URL")
            
            # Extract citations from text
            citations = []
            extracted_citations = extract_citations(document_text)
            app.logger.info(f"Extracted {len(extracted_citations)} citations from URL content")
            
            # Validate each citation
            for citation_text in extracted_citations:
                validation_result = validate_citation(citation_text)
                
                # Format the result to match the expected format by the Vue.js frontend
                citations.append({
                    'citation': citation_text,
                    'found': validation_result['verified'],
                    'url': None,  # Not provided by Enhanced Validator
                    'found_case_name': validation_result['case_name'],
                    'name_match': True if validation_result['verified'] else False,
                    'confidence': 1.0 if validation_result['verified'] else 0.0,
                    'explanation': f"Validated by {validation_result['validation_method']}" if validation_result['verified'] else "Citation not found",
                    'source': validation_result['validation_method'] if validation_result['verified'] else None
                })
            
            app.logger.info(f"Validated {len(citations)} citations")
            
            # Format the citations for the response
            formatted_citations = [
                {
                    'citation': citation['citation'],
                    'found': citation['found'],
                    'url': citation.get('url'),
                    'found_case_name': citation['found_case_name'],
                    'name_match': citation.get('name_match', True) if citation['found'] else False,
                    'confidence': citation.get('confidence', 1.0) if citation['found'] else 0.0,
                    'explanation': citation.get('explanation', f"Validated by {citation['source']}") if citation['found'] else "Citation not found",
                    'source': citation['source']
                } for citation in citations
            ]
            
            # Store citations in session
            session['user_citations'] = formatted_citations
            app.logger.info(f"Stored {len(formatted_citations)} citations in user session")
            
            # Return the results
            return jsonify({
                'status': 'success',
                'analysis_id': analysis_id,
                'citations': formatted_citations,
                'citations_count': len(citations),
                'url': url
            })
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error fetching URL: {e}")
            return jsonify({
                'status': 'error',
                'message': f"Error fetching URL: {str(e)}"
            }), 500
    
    except Exception as e:
        error_msg = f"Error analyzing URL: {str(e)}"
        app.logger.error(error_msg)
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500
"""

    # Insert the direct URL endpoint function
    new_content = (
        content[:insertion_point]
        + direct_url_endpoint
        + "\n\n"
        + content[insertion_point:]
    )

    # Write the updated content back to the file
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info("Direct URL endpoint added successfully")
    return True


def create_test_client():
    """Create a test client for the direct URL endpoint."""
    logger.info("Creating test client for direct URL endpoint")

    # Create a simple HTML file to test the direct URL endpoint
    test_html_path = os.path.join(os.getcwd(), "test_direct_url.html")

    test_html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer Direct URL Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { max-width: 800px; margin-top: 50px; }
        #results { margin-top: 20px; }
        pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CaseStrainer Direct URL Test</h1>
        <p>This page tests the direct URL processing functionality of the CaseStrainer application.</p>
        
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">Test Direct URL Processing</h5>
            </div>
            <div class="card-body">
                <form id="urlForm">
                    <div class="mb-3">
                        <label for="urlInput" class="form-label">Enter URL with legal citations:</label>
                        <input type="url" class="form-control" id="urlInput" 
                               value="https://www.law.cornell.edu/supremecourt/text/347/483" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Process URL</button>
                </form>
            </div>
        </div>
        
        <div id="results" style="display: none;">
            <h3>Results</h3>
            <div class="mb-3">
                <h5>Request:</h5>
                <pre id="requestData"></pre>
            </div>
            <div class="mb-3">
                <h5>Response:</h5>
                <pre id="responseData"></pre>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const urlForm = document.getElementById('urlForm');
            const resultsDiv = document.getElementById('results');
            const requestDataPre = document.getElementById('requestData');
            const responseDataPre = document.getElementById('responseData');
            
            urlForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const url = document.getElementById('urlInput').value.trim();
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                // Clear previous results
                requestDataPre.textContent = '';
                responseDataPre.textContent = '';
                resultsDiv.style.display = 'none';
                
                // Disable submit button
                const submitButton = this.querySelector('button[type="submit"]');
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Direct URL processing
                const payload = {
                    url: url
                };
                
                requestDataPre.textContent = 'Direct URL processing\\n' + JSON.stringify(payload, null, 2);
                
                fetch('/api/direct_url_analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    // Display results
                    responseDataPre.textContent = JSON.stringify(data, null, 2);
                    resultsDiv.style.display = 'block';
                    
                    // Reset button
                    submitButton.disabled = false;
                    submitButton.textContent = 'Process URL';
                })
                .catch(error => {
                    responseDataPre.textContent = 'Error: ' + error.message;
                    resultsDiv.style.display = 'block';
                    
                    // Reset button
                    submitButton.disabled = false;
                    submitButton.textContent = 'Process URL';
                });
            });
        });
    </script>
</body>
</html>"""

    with open(test_html_path, "w", encoding="utf-8") as f:
        f.write(test_html_content)

    logger.info(f"Test client created at {test_html_path}")
    return True


def test_direct_url_endpoint():
    """Test the direct URL endpoint."""
    logger.info("Testing direct URL endpoint")

    # Test URL with legal citations
    url = "https://www.law.cornell.edu/supremecourt/text/347/483"
    logger.info(f"Testing direct URL endpoint with URL: {url}")

    # CaseStrainer API endpoint
    api_url = "http://localhost:5000/api/direct_url_analyze"

    # Prepare the JSON payload
    payload = {"url": url}

    headers = {"Content-Type": "application/json"}

    # Make the request to the CaseStrainer API
    logger.info(f"Sending request to: {api_url}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        # Log the raw response for debugging
        logger.info(f"Raw response: {response.text}")

        # Check response status
        logger.info(f"Response status code: {response.status_code}")

        try:
            result = response.json()
            logger.info(f"Response JSON: {json.dumps(result, indent=2)}")
            return True
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return False


if __name__ == "__main__":
    # Create the direct URL endpoint
    if create_direct_url_endpoint():
        logger.info("Direct URL endpoint created successfully")

        # Create the test client
        if create_test_client():
            logger.info("Test client created successfully")

            # Prompt the user to restart the application
            print("\nPlease restart the CaseStrainer application to apply the changes.")
            print("After restarting, you can test the direct URL endpoint by:")
            print(
                "1. Running 'python test_url_endpoint.py test' to test the endpoint directly"
            )
            print("2. Opening test_direct_url.html in a browser to test through the UI")

            # Check if the user wants to test the endpoint directly
            if len(sys.argv) > 1 and sys.argv[1] == "test":
                logger.info("Testing direct URL endpoint")
                if test_direct_url_endpoint():
                    logger.info("Direct URL endpoint test successful")
                else:
                    logger.error("Direct URL endpoint test failed")
        else:
            logger.error("Failed to create test client")
    else:
        logger.error("Failed to create direct URL endpoint")
