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
import argparse
import time
from pathlib import Path

# Third-party imports
from flask import Flask, jsonify, render_template, request, send_from_directory, session
from flask_cors import CORS
import uuid
import threading
import queue
import re

# Load configuration
def load_config():
    """Load configuration from config.json and set up environment variables."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        # Set up environment variables from config
        if 'courtlistener_api_key' in config:
            os.environ['COURTLISTENER_API_KEY'] = config['courtlistener_api_key']
        if 'langsearch_api_key' in config:
            os.environ['LANGSEARCH_API_KEY'] = config['langsearch_api_key']
        if 'openai_api_key' in config:
            os.environ['OPENAI_API_KEY'] = config['openai_api_key']
            
        return config
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        return {}

# Load configuration
config = load_config()

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

# Try to import API integrations
try:
    from langsearch_integration import setup_langsearch_api, LANGSEARCH_AVAILABLE
except ImportError:
    LANGSEARCH_AVAILABLE = False
    print("Warning: langsearch_integration module not available. LangSearch API will not be used.")

try:
    from courtlistener_integration import setup_courtlistener_api, set_use_local_pdf_search, COURTLISTENER_AVAILABLE
except ImportError:
    COURTLISTENER_AVAILABLE = False
    print("Warning: courtlistener_integration module not available. CourtListener API will not be used.")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())  # Set a secret key for sessions
CORS(app)  # Enable CORS for Word add-in support

# Directory for Word add-in files
ADDIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'word_addin')
os.makedirs(ADDIN_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

# Global queue for storing analysis results
analysis_queues = {}

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a brief for hallucinated case citations."""
    brief_text = ""
    temp_file = None
    
    # Generate a unique session ID for this analysis request
    session_id = str(uuid.uuid4())
    
    # Create a queue for this session
    analysis_queues[session_id] = queue.Queue()
    
    try:
        # Check if this is a file upload or direct text input
        print("Analyzing request...")
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        print(f"Request files: {list(request.files.keys()) if request.files else 'None'}")
        print(f"Request form: {list(request.form.keys()) if request.form else 'None'}")
        
        if 'file' in request.files and request.files['file'].filename:
            uploaded_file = request.files['file']
            print(f"File upload detected: {uploaded_file.filename}")
            file_extension = os.path.splitext(uploaded_file.filename.lower())[1]
            print(f"File extension: {file_extension}")
            
            # Validate file extension
            valid_extensions = ['.docx', '.pdf', '.txt']
            if file_extension not in valid_extensions:
                print(f"Invalid file extension: {file_extension}")
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
                        print(f"Error processing DOCX file: {str(e)}")
                        return jsonify({
                            "error": f"Failed to process Word document: {str(e)}"
                        }), 400
                        
                elif file_extension == '.pdf':
                    if not PDF_AVAILABLE:
                        print("PDF support not available. PyPDF2 package is missing.")
                        return jsonify({
                            "error": "PDF support not available. Please install PyPDF2 package."
                        }), 400
                    
                    try:
                        # Extract text from PDF document
                        print(f"Processing PDF file: {temp_file.name}")
                        text = ""
                        with open(temp_file.name, 'rb') as f:
                            try:
                                pdf_reader = PyPDF2.PdfReader(f)
                                print(f"PDF has {len(pdf_reader.pages)} pages")
                                for page_num in range(len(pdf_reader.pages)):
                                    page = pdf_reader.pages[page_num]
                                    page_text = page.extract_text()
                                    text += page_text + "\n"
                                    print(f"Extracted {len(page_text)} characters from page {page_num+1}")
                            except Exception as pdf_error:
                                print(f"Error reading PDF: {str(pdf_error)}")
                                raise pdf_error
                        brief_text = text
                        print(f"Total extracted text length: {len(brief_text)} characters")
                    except Exception as e:
                        print(f"Error processing PDF file: {str(e)}")
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
            
            # Check if local PDF search is enabled
            use_local_pdf_search = request.form.get('use_local_pdf_search', 'false').lower() == 'true'
            set_use_local_pdf_search(use_local_pdf_search)
        except ValueError as e:
            return jsonify({
                "error": f"Invalid parameter value: {str(e)}"
            }), 400
        
        # Analyze brief
        try:
            # Use Server-Sent Events to stream results as they become available
            def generate():
                # Set a keep-alive interval
                keep_alive_interval = 15  # seconds
                last_message_time = 0
                
                # First, extract citations
                try:
                    # Send an initial keep-alive message
                    yield f"data: {json.dumps({'status': 'connecting', 'message': 'Connection established'})}\n\n"
                    
                    citations = extract_case_citations(brief_text)
                    
                    if not citations:
                        yield f"data: {json.dumps({'status': 'complete', 'total_citations': 0, 'hallucinated_citations': 0, 'results': []})}\n\n"
                        return
                    
                    # Deduplicate citations
                    seen_citations = set()
                    unique_citations = []
                    
                    def normalize_citation(citation):
                        """Normalize citation for deduplication"""
                        # Convert to lowercase and strip whitespace
                        norm = citation.strip().lower()
                        
                        # Remove all spaces
                        no_spaces = re.sub(r'\s+', '', norm)
                        
                        # For WestLaw citations (e.g., 2018 WL 3037217)
                        wl_match = re.search(r'(\d{4})(?:\s*W\.?\s*L\.?\s*)(\d+)', norm)
                        if wl_match:
                            year, number = wl_match.groups()
                            return f"{year}wl{number}"
                        
                        # For standard case citations, remove punctuation
                        return re.sub(r'[^\w\d]', '', norm)
                    
                    for citation in citations:
                        normalized_citation = normalize_citation(citation)
                        if normalized_citation not in seen_citations:
                            seen_citations.add(normalized_citation)
                            unique_citations.append(citation)
                    
                    # Send initial data with total citations
                    total_unique = len(unique_citations)
                    yield f"data: {json.dumps({'status': 'started', 'total_citations': total_unique, 'message': f'Found {total_unique} unique citations in the document'})}\n\n"
                    last_message_time = time.time()
                    
                    # Start a background thread to process citations
                    def process_citations():
                        results = []
                        hallucinated_count = 0
                        
                        try:
                            for i, citation in enumerate(unique_citations, 1):
                                # Put progress update in the queue
                                analysis_queues[session_id].put({
                                    'status': 'progress', 
                                    'current': i, 
                                    'total': total_unique, 
                                    'message': f'Checking citation {i}/{total_unique}: {citation}'
                                })
                                
                                try:
                                    # Check the citation
                                    from briefcheck import check_citation
                                    result = check_citation(citation, num_iterations, similarity_threshold)
                                    
                                    # Update hallucinated count
                                    if result.get('is_hallucinated', False):
                                        hallucinated_count += 1
                                    
                                    # Add result to results list
                                    results.append(result)
                                    
                                    # Put the individual result in the queue
                                    analysis_queues[session_id].put({
                                        'status': 'result', 
                                        'citation_index': i-1, 
                                        'citation': citation, 
                                        'result': result,
                                        'total': total_unique,
                                        'hallucinated_count': hallucinated_count
                                    })
                                    
                                except Exception as e:
                                    # Put error for this citation in the queue
                                    error_result = {
                                        "citation": citation,
                                        "is_hallucinated": False,
                                        "confidence": 0.0,
                                        "method": "check_failed",
                                        "error": str(e),
                                        "similarity_score": None,
                                        "summaries": [],
                                        "exists": True,
                                        "case_data": False,
                                        "case_summary": f"Error checking citation: {str(e)}"
                                    }
                                    results.append(error_result)
                                    analysis_queues[session_id].put({
                                        'status': 'error', 
                                        'citation_index': i-1, 
                                        'citation': citation, 
                                        'error': str(e), 
                                        'result': error_result,
                                        'total': total_unique,
                                        'hallucinated_count': hallucinated_count
                                    })
                            
                            # Put final complete message in the queue
                            final_result = {
                                "status": "complete",
                                "total_citations": total_unique,
                                "hallucinated_citations": hallucinated_count,
                                "results": results
                            }
                            analysis_queues[session_id].put(final_result)
                            
                        except Exception as e:
                            # Put error message in the queue
                            analysis_queues[session_id].put({'status': 'error', 'error': str(e)})
                    
                    # Start the background thread
                    thread = threading.Thread(target=process_citations)
                    thread.daemon = True
                    thread.start()
                    
                    # Process each citation and send results as they become available
                    results = []
                    hallucinated_count = 0
                    
                    # Keep-alive timer
                    last_message_time = 0
                    
                    # Stream results from the queue
                    while True:
                        try:
                            # Check if we need to send a keep-alive message
                            current_time = time.time()
                            if current_time - last_message_time > keep_alive_interval:
                                yield f"data: {json.dumps({'status': 'keep-alive', 'timestamp': current_time})}\n\n"
                                last_message_time = current_time
                            
                            # Try to get a message from the queue with a timeout
                            try:
                                message = analysis_queues[session_id].get(timeout=1)
                            except queue.Empty:
                                # No message available, continue and check for keep-alive
                                continue
                            
                            # Update the last message time
                            last_message_time = time.time()
                            
                            # Process the message
                            if message['status'] == 'complete':
                                # Final message, send it and break the loop
                                yield f"data: {json.dumps(message)}\n\n"
                                break
                            elif message['status'] == 'error':
                                # Error message, send it and break the loop
                                yield f"data: {json.dumps(message)}\n\n"
                                break
                            else:
                                # Regular message, send it
                                yield f"data: {json.dumps(message)}\n\n"
                                
                                # Update our local tracking variables
                                if message['status'] == 'result':
                                    if message['result'].get('is_hallucinated', False):
                                        hallucinated_count = message.get('hallucinated_count', hallucinated_count + 1)
                        except GeneratorExit:
                            # Client disconnected
                            print(f"Client disconnected for session {session_id}")
                            if session_id in analysis_queues:
                                del analysis_queues[session_id]
                            return
                        except Exception as e:
                            # Send error message
                            yield f"data: {json.dumps({'status': 'error', 'error': f'Stream error: {str(e)}'})}\n\n"
                            break
                    
                    # Clean up
                    if session_id in analysis_queues:
                        del analysis_queues[session_id]
                    
                except Exception as e:
                    # Send error message
                    yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
                    
                    # Clean up
                    if session_id in analysis_queues:
                        del analysis_queues[session_id]
            
            # Return the streaming response
            response = app.response_class(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',  # Disable buffering for Nginx
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',  # Allow cross-origin requests
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Transfer-Encoding': 'chunked'  # Use chunked encoding for better streaming
                }
            )
            print("Sending SSE response with headers:", response.headers)
            return response
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
            
            # Check if local PDF search is enabled
            use_local_pdf_search = data.get('use_local_pdf_search', False)
            set_use_local_pdf_search(use_local_pdf_search)
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
        # Get server configuration
        server_config = config.get('server', {})
        host = server_config.get('host', 'localhost')
        port = server_config.get('port', 5000)
        use_ssl = server_config.get('use_ssl', False)
        
        # Set up SSL context if needed
        ssl_context = None
        if use_ssl:
            ssl_context = 'adhoc'  # Use adhoc for development, replace with proper certs in production
        
        print(f"Starting server on {host}:{port} (SSL: {use_ssl})")
        app.run(
            host=host,
            port=port,
            ssl_context=ssl_context,
            debug=True
        )
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        sys.exit(1)
