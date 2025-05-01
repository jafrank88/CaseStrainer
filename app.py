#!/usr/bin/env python3
"""
CaseStrainer Web Interface

A Flask web application that provides a user interface for the CaseStrainer tool,
with support for Word documents and a Word add-in.
"""

# Standard library imports
import json
import os
import sys
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

# Try to import PyPDF2 for PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not available, PDF support will be limited")

# Local application imports
from briefcheck import analyze_brief, extract_case_citations

# Try to import OpenAI and CourtListener integrations
try:
    from openai_integration import setup_openai_api, OPENAI_AVAILABLE
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai_integration module not available. OpenAI API will not be used.")

try:
    from courtlistener_integration import setup_courtlistener_api, COURTLISTENER_AVAILABLE
except ImportError:
    COURTLISTENER_AVAILABLE = False
    print("Warning: courtlistener_integration module not available. CourtListener API will not be used.")

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
    temp_file = None
    
    try:
        # Check if this is a file upload or direct text input
        if 'file' in request.files and request.files['file'].filename:
            uploaded_file = request.files['file']
            file_extension = os.path.splitext(uploaded_file.filename.lower())[1]
            
            # Validate file extension
            valid_extensions = ['.docx', '.pdf', '.txt']
            if file_extension not in valid_extensions:
                return jsonify({
                    "error": f"Unsupported file format: {file_extension}. Please upload a .docx, .pdf, or .txt file."
                }), 400
            
            try:
                # Save the uploaded file to a temporary location
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                uploaded_file.save(temp_file.name)
                temp_file.close()
                
                # Process based on file type
                if file_extension == '.docx':
                    if not DOCX_AVAILABLE:
                        return jsonify({
                            "error": "Word document support not available. Please install python-docx package."
                        }), 400
                    
                    try:
                        # Extract text from Word document
                        doc = docx.Document(temp_file.name)
                        brief_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    except Exception as e:
                        return jsonify({
                            "error": f"Failed to process Word document: {str(e)}"
                        }), 400
                        
                elif file_extension == '.pdf':
                    if not PDF_AVAILABLE:
                        return jsonify({
                            "error": "PDF support not available. Please install PyPDF2 package."
                        }), 400
                    
                    try:
                        # Extract text from PDF document
                        text = ""
                        with open(temp_file.name, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                text += page.extract_text() + "\n"
                        brief_text = text
                    except Exception as e:
                        return jsonify({
                            "error": f"Failed to process PDF document: {str(e)}"
                        }), 400
                        
                elif file_extension == '.txt':
                    try:
                        # Read text file
                        with open(temp_file.name, 'r', encoding='utf-8') as f:
                            brief_text = f.read()
                    except UnicodeDecodeError:
                        # Try with different encodings if UTF-8 fails
                        try:
                            with open(temp_file.name, 'r', encoding='latin-1') as f:
                                brief_text = f.read()
                        except Exception as e:
                            return jsonify({
                                "error": f"Failed to read text file: {str(e)}"
                            }), 400
                    except Exception as e:
                        return jsonify({
                            "error": f"Failed to read text file: {str(e)}"
                        }), 400
            finally:
                # Clean up the temporary file
                if temp_file and os.path.exists(temp_file.name):
                    try:
                        os.unlink(temp_file.name)
                    except Exception as e:
                        print(f"Warning: Failed to delete temporary file: {str(e)}")
        else:
            # Get text from form data
            brief_text = request.form.get('brief_text', '')
            
            # If no text was provided, return an error
            if not brief_text:
                return jsonify({"error": "No text or file provided."}), 400
        
        # Validate and get analysis parameters
        try:
            num_iterations = int(request.form.get('iterations', 3))
            if num_iterations < 1 or num_iterations > 10:
                return jsonify({
                    "error": "Number of iterations must be between 1 and 10."
                }), 400
                
            similarity_threshold = float(request.form.get('threshold', 0.7))
            if similarity_threshold < 0.1 or similarity_threshold > 1.0:
                return jsonify({
                    "error": "Similarity threshold must be between 0.1 and 1.0."
                }), 400
        except ValueError as e:
            return jsonify({
                "error": f"Invalid parameter value: {str(e)}"
            }), 400
        
        # Analyze brief
        try:
            results = analyze_brief(brief_text, num_iterations, similarity_threshold)
            return jsonify(results)
        except Exception as e:
            return jsonify({
                "error": f"Analysis failed: {str(e)}"
            }), 500
            
    except Exception as e:
        # Catch-all for any unexpected errors
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

@app.route('/extract', methods=['POST'])
def extract():
    """Extract case citations from text."""
    try:
        # Get form data
        brief_text = request.form.get('brief_text', '')
        
        if not brief_text:
            return jsonify({
                "error": "No text provided for citation extraction."
            }), 400
        
        # Extract citations
        try:
            citations = extract_case_citations(brief_text)
            return jsonify({'citations': citations})
        except Exception as e:
            return jsonify({
                "error": f"Citation extraction failed: {str(e)}"
            }), 500
            
    except Exception as e:
        # Catch-all for any unexpected errors
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

# API endpoints for Word add-in
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for Word add-in to analyze text."""
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON format."
            }), 400
            
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                "error": "No text provided in request body."
            }), 400
        
        brief_text = data['text']
        if not brief_text.strip():
            return jsonify({
                "error": "Text content is empty."
            }), 400
        
        # Validate and get analysis parameters
        try:
            num_iterations = int(data.get('iterations', 3))
            if num_iterations < 1 or num_iterations > 10:
                return jsonify({
                    "error": "Number of iterations must be between 1 and 10."
                }), 400
                
            similarity_threshold = float(data.get('threshold', 0.7))
            if similarity_threshold < 0.1 or similarity_threshold > 1.0:
                return jsonify({
                    "error": "Similarity threshold must be between 0.1 and 1.0."
                }), 400
        except ValueError as e:
            return jsonify({
                "error": f"Invalid parameter value: {str(e)}"
            }), 400
        
        # Analyze brief
        try:
            results = analyze_brief(brief_text, num_iterations, similarity_threshold)
            return jsonify(results)
        except Exception as e:
            return jsonify({
                "error": f"Analysis failed: {str(e)}"
            }), 500
            
    except Exception as e:
        # Catch-all for any unexpected errors
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500

# Serve Word add-in files
@app.route('/word-addin/<path:filename>')
def word_addin_files(filename):
    """Serve Word add-in files."""
    try:
        # Validate filename to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({
                "error": "Invalid filename."
            }), 400
            
        # Check if file exists
        file_path = os.path.join(ADDIN_DIR, filename)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({
                "error": f"File not found: {filename}"
            }), 404
            
        return send_from_directory(ADDIN_DIR, filename)
    except Exception as e:
        return jsonify({
            "error": f"Failed to serve file: {str(e)}"
        }), 500

if __name__ == '__main__':
    try:
        # Ensure templates directory exists
        os.makedirs('templates', exist_ok=True)
        
        # Initialize API integrations
        if 'OPENAI_AVAILABLE' in globals() and OPENAI_AVAILABLE:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                print("Initializing OpenAI API...")
                setup_openai_api(openai_key)
            else:
                print("Warning: OPENAI_API_KEY environment variable not set. OpenAI API will not be used.")
        
        if 'COURTLISTENER_AVAILABLE' in globals() and COURTLISTENER_AVAILABLE:
            courtlistener_key = os.environ.get('COURTLISTENER_API_KEY')
            if courtlistener_key:
                print("Initializing CourtListener API...")
                setup_courtlistener_api(courtlistener_key)
            else:
                print("Warning: COURTLISTENER_API_KEY environment variable not set. CourtListener API will be used in limited mode.")
        
        # Check for SSL certificate and key
        cert_path = os.environ.get('SSL_CERT_PATH', 'ssl/cert.pem')
        key_path = os.environ.get('SSL_KEY_PATH', 'ssl/key.pem')
        
        # Check if SSL certificate and key exist
        ssl_context = None
        if os.path.exists(cert_path) and os.path.exists(key_path):
            try:
                # Verify the certificate and key are valid
                ssl_context = (cert_path, key_path)
                print(f"Using SSL certificate: {cert_path}")
                print(f"Using SSL key: {key_path}")
            except Exception as e:
                print(f"Error loading SSL certificate or key: {str(e)}")
                print("Running without SSL...")
        else:
            print("Warning: SSL certificate or key not found.")
            print("For production use with Word add-in, HTTPS is required.")
            print("You can generate a self-signed certificate for development:")
            print("mkdir -p ssl")
            print("openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365")
        
        # Parse environment variables with error handling
        try:
            debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
            host = os.environ.get('HOST', '0.0.0.0')
            
            try:
                port = int(os.environ.get('PORT', 5000))
                if port < 0 or port > 65535:
                    print(f"Warning: Invalid port number {port}, using default port 5000")
                    port = 5000
            except ValueError:
                print(f"Warning: Invalid PORT environment variable, using default port 5000")
                port = 5000
                
        except Exception as e:
            print(f"Error parsing environment variables: {str(e)}")
            print("Using default configuration...")
            debug_mode = True
            host = '0.0.0.0'
            port = 5000
        
        # Run the app
        app.run(
            debug=debug_mode,
            host=host,
            port=port,
            ssl_context=None  # Disable SSL for testing
        )
    except Exception as e:
        print(f"Failed to start the application: {str(e)}")
        sys.exit(1)
