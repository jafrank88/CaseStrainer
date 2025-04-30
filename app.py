#!/usr/bin/env python3
"""
CaseStrainer Web Interface

A Flask web application that provides a user interface for the CaseStrainer tool,
with support for Word documents and a Word add-in.
"""

# Standard library imports
import json
import os
import tempfile

# Third-party imports
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

# Try to import docx for Word document processing
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available, Word document support will be limited")

# Local application imports
from briefcheck import analyze_brief, extract_case_citations

app = Flask(__name__)
CORS(app)  # Enable CORS for Word add-in support

# Directory for Word add-in files
ADDIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'word_addin')
os.makedirs(ADDIN_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a brief for hallucinated case citations."""
    brief_text = ""
    
    # Check if this is a file upload or direct text input
    if 'file' in request.files and request.files['file'].filename:
        uploaded_file = request.files['file']
        
        # Save the uploaded file to a temporary location
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        uploaded_file.save(temp_file.name)
        temp_file.close()
        
        # Process based on file type
        if uploaded_file.filename.lower().endswith('.docx'):
            if DOCX_AVAILABLE:
                # Extract text from Word document
                doc = docx.Document(temp_file.name)
                brief_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            else:
                return jsonify({"error": "Word document support not available. Please install python-docx."}), 400
        elif uploaded_file.filename.lower().endswith('.txt'):
            # Read text file
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                brief_text = f.read()
        else:
            # Clean up the temporary file
            os.unlink(temp_file.name)
            return jsonify({"error": "Unsupported file format. Please upload a .docx or .txt file."}), 400
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
    else:
        # Get text from form data
        brief_text = request.form.get('brief_text', '')
        
        # If no text was provided, return an error
        if not brief_text:
            return jsonify({"error": "No text or file provided."}), 400
    
    # Get analysis parameters
    num_iterations = int(request.form.get('iterations', 3))
    similarity_threshold = float(request.form.get('threshold', 0.7))
    
    # Analyze brief
    results = analyze_brief(brief_text, num_iterations, similarity_threshold)
    
    return jsonify(results)

@app.route('/extract', methods=['POST'])
def extract():
    """Extract case citations from text."""
    # Get form data
    brief_text = request.form.get('brief_text', '')
    
    # Extract citations
    citations = extract_case_citations(brief_text)
    
    return jsonify({'citations': citations})

# API endpoints for Word add-in
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for Word add-in to analyze text."""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided."}), 400
    
    brief_text = data['text']
    num_iterations = int(data.get('iterations', 3))
    similarity_threshold = float(data.get('threshold', 0.7))
    
    # Analyze brief
    results = analyze_brief(brief_text, num_iterations, similarity_threshold)
    
    return jsonify(results)

# Serve Word add-in files
@app.route('/word-addin/<path:filename>')
def word_addin_files(filename):
    """Serve Word add-in files."""
    return send_from_directory(ADDIN_DIR, filename)

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Check for SSL certificate and key
    cert_path = os.environ.get('SSL_CERT_PATH', 'ssl/cert.pem')
    key_path = os.environ.get('SSL_KEY_PATH', 'ssl/key.pem')
    
    # Check if SSL certificate and key exist
    ssl_context = None
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = (cert_path, key_path)
        print(f"Using SSL certificate: {cert_path}")
        print(f"Using SSL key: {key_path}")
    else:
        print("Warning: SSL certificate or key not found.")
        print("For production use with Word add-in, HTTPS is required.")
        print("You can generate a self-signed certificate for development:")
        print("mkdir -p ssl")
        print("openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365")
    
    # Run the app
    app.run(
        debug=os.environ.get('DEBUG', 'True').lower() == 'true',
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        ssl_context=ssl_context
    )
