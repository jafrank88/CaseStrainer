from flask import Flask, request, render_template, jsonify, Response, send_from_directory
import os
import re
import json
import time
import uuid
import threading
import traceback
import PyPDF2
from werkzeug.utils import secure_filename
import docx
import requests
import subprocess
import sys

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v3/citation-lookup/'

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load API key from config.json if available
DEFAULT_API_KEY = None
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get('courtlistener_api_key')
        print(f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}..." if DEFAULT_API_KEY else "No CourtListener API key found in config.json")
except Exception as e:
    print(f"Error loading config.json: {e}")

# Dictionary to store analysis results
analysis_results = {}

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from different file types
from file_utils import extract_text_from_file

    """Extract text from a file based on its extension."""
    print(f"Extracting text from file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    file_extension = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    
    try:
        # Extract text based on file extension
        if file_extension == 'txt':
            # For .txt files, just read the content
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    print(f"Successfully extracted {len(text)} characters from TXT")
                    return text
            except UnicodeDecodeError:
                # Try with a different encoding if utf-8 fails
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                    print(f"Successfully extracted {len(text)} characters from TXT (latin-1 encoding)")
                    return text
        
        elif file_extension == 'pdf':
            # For .pdf files, try multiple methods
            print(f"Attempting to extract text from PDF: {file_path}")
            
            # First check if file exists and is readable
            if not os.path.exists(file_path):
                print(f"PDF file does not exist: {file_path}")
                return None
                
            file_size = os.path.getsize(file_path)
            print(f"PDF file size: {file_size} bytes")
            
            if file_size == 0:
                print(f"PDF file is empty: {file_path}")
                return None
            
            # Try pdfminer.six first (install if needed)
            try:
                print("Trying to extract text with pdfminer.six...")
                try:
                    from pdfminer.high_level import extract_text as pdfminer_extract
                    print("pdfminer.six is already installed")
                except ImportError:
                    print("Installing pdfminer.six...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfminer.six"])
                    from pdfminer.high_level import extract_text as pdfminer_extract
                
                # Extract text with pdfminer.six
                text = pdfminer_extract(file_path)
                print(f"Successfully extracted {len(text)} characters with pdfminer.six")
                
                # Save the extracted text to a file for inspection
                try:
                    with open('extracted_pdf_text.txt', 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"Extracted PDF text saved to extracted_pdf_text.txt")
                except Exception as e:
                    print(f"Error saving extracted text to file: {e}")
                
                return text
            except Exception as e:
                print(f"Error extracting text with pdfminer.six: {e}")
                traceback.print_exc()
                
                # Fall back to PyPDF2
                try:
                    print("Falling back to PyPDF2...")
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        print(f"PDF has {len(reader.pages)} pages")
                        text = ''
                        
                        # Process each page with error handling
                        for i, page in enumerate(reader.pages):
                            try:
                                print(f"Extracting text from page {i+1}...")
                                page_text = page.extract_text()
                                text += page_text + '\n'
                                print(f"Extracted {len(page_text)} characters from page {i+1}")
                            except Exception as page_error:
                                print(f"Error extracting text from page {i+1}: {page_error}")
                        
                        if text.strip():
                            print(f"Successfully extracted {len(text)} characters with PyPDF2")
                            return text
                        else:
                            print("PyPDF2 extraction returned empty text")
                            return None
                except Exception as e:
                    print(f"Error extracting text with PyPDF2: {e}")
                    traceback.print_exc()
                    return None
        
        elif file_extension in ['docx', 'doc']:
            # For .docx files, use python-docx
            try:
                doc = docx.Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                print(f"Successfully extracted {len(text)} characters from DOCX")
                return text
            except Exception as e:
                print(f"Error extracting text from DOCX: {e}")
                traceback.print_exc()
                return None
        
        else:
            print(f"Unsupported file extension: {file_extension}")
            return None
    
    except Exception as e:
        print(f"Error extracting text from file: {e}")
        traceback.print_exc()
        return None

# Function to extract citations from text
def extract_citations(text):
    """Extract legal citations from text using regex patterns."""
    print(f"Extracting citations from text of length: {len(text)}")
    
    # Normalize the text to make citation matching more reliable
    # Remove extra whitespace and normalize spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Example patterns for common citation formats
    patterns = [
        # US Reports (e.g., 347 U.S. 483)
        r'\b\d+\s+U\.?\s*S\.?\s+\d+\b',
        
        # Supreme Court Reporter (e.g., 98 S.Ct. 2733)
        r'\b\d+\s+S\.?\s*Ct\.?\s+\d+\b',
        
        # Federal Reporter (e.g., 410 F.2d 701, 723 F.3d 1067)
        r'\b\d+\s+F\.?\s*(?:2d|3d)?\s+\d+\b',
        
        # Federal Supplement (e.g., 595 F.Supp.2d 735)
        r'\b\d+\s+F\.?\s*Supp\.?\s*(?:2d|3d)?\s+\d+\b',
        
        # Westlaw citations (e.g., 2011 WL 2160468)
        r'\b\d{4}\s+WL\s+\d+\b',
        
        # Federal Rules Decisions (e.g., 29 F.R.D. 401)
        r'\b\d+\s+F\.R\.D\.\s+\d+\b',
        
        # Bankruptcy Reporter (e.g., 480 B.R. 921)
        r'\b\d+\s+B\.R\.\s+\d+\b',
        
        # Lawyers Edition (e.g., 98 L.Ed.2d 720)
        r'\b\d+\s+L\.\s*Ed\.\s*(?:2d)?\s+\d+\b',
    ]
    
    citations = []
    for pattern in patterns:
        try:
            print(f"Searching for pattern: {pattern}")
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                citation = match.group(0).strip()
                print(f"Found citation: {citation}")
                if citation not in citations:
                    citations.append(citation)
        except Exception as e:
            print(f"Error searching for pattern {pattern}: {e}")
    
    print(f"Total citations extracted: {len(citations)}")
    if citations:
        print(f"Extracted citations: {citations}")
        
        # Save the extracted citations to a file for inspection
        try:
            with open('extracted_citations.txt', 'w', encoding='utf-8') as f:
                for i, citation in enumerate(citations):
                    f.write(f"{i+1}. {citation}\n")
            print(f"Extracted citations saved to extracted_citations.txt")
        except Exception as e:
            print(f"Error saving extracted citations to file: {e}")
    
    return citations

# Function to query the CourtListener API
def query_courtlistener_api(text, api_key):
    """Query the CourtListener API to verify citations in the text."""
    print(f"Querying CourtListener API with text of length: {len(text)}")
    
    if not api_key:
        print("No API key provided")
        return {'error': 'No API key provided'}
    
    try:
        # Prepare the request
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare the data
        data = {
            'text': text
        }
        
        # Make the request
        print(f"Sending request to {COURTLISTENER_API_URL}")
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)
        
        # Check the response
        if response.status_code == 200:
            print("API request successful")
            result = response.json()
            
            # Save the API response to a file for inspection
            try:
                with open('api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print("API response saved to api_response.json")
            except Exception as e:
                print(f"Error saving API response to file: {e}")
            
            return result
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return {'error': f"API request failed with status code {response.status_code}: {response.text}"}
    
    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        traceback.print_exc()
        return {'error': f"Error querying CourtListener API: {str(e)}"}

# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())

# Function to send progress updates via SSE
def send_progress(analysis_id, data):
    print(f"Sending progress update for analysis {analysis_id}: {data}")
    if analysis_id in analysis_results:
        # Add the event to the events list
        analysis_results[analysis_id]['events'].append(data)
        
        # If this is a 'complete' event, mark the analysis as completed
        if data.get('status') == 'complete':
            analysis_results[analysis_id]['completed'] = True
            
        # Save the event data to a file for debugging
        try:
            with open(f'event_{analysis_id}_{data.get("status", "unknown")}_{len(analysis_results[analysis_id]["events"])}.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving event data to file: {e}")

# Function to run the analysis with CourtListener API
def run_analysis(analysis_id, brief_text=None, file_path=None, api_key=None):
    print(f"Starting analysis for ID: {analysis_id}")
    print(f"API key: {api_key[:5]}..." if api_key else "No API key provided")
    print(f"File path: {file_path}" if file_path else "No file path provided")
    print(f"Brief text length: {len(brief_text)}" if brief_text else "No brief text provided")
    
    try:
        # Initialize the results for this analysis
        analysis_results[analysis_id] = {
            'status': 'running',
            'events': [],
            'completed': False
        }
        
        # Get text from file if provided
        if file_path and not brief_text:
            print(f"Extracting text from file: {file_path}")
            
            # Verify file exists and is readable
            if not os.path.isfile(file_path):
                error_msg = f"File not found: {file_path}"
                print(error_msg)
                send_progress(analysis_id, {
                    'status': 'error',
                    'message': error_msg
                })
                raise Exception(error_msg)
            
            try:
                file_size = os.path.getsize(file_path)
                print(f"File size: {file_size} bytes")
                
                # Check if file is empty
                if file_size == 0:
                    error_msg = f"File is empty: {file_path}"
                    print(error_msg)
                    send_progress(analysis_id, {
                        'status': 'error',
                        'message': error_msg
                    })
                    raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Error checking file: {str(e)}"
                print(error_msg)
                send_progress(analysis_id, {
                    'status': 'error',
                    'message': error_msg
                })
                raise Exception(error_msg)
            
            # Add extraction progress event
            send_progress(analysis_id, {
                'status': 'progress',
                'current': 0,
                'total': 1,
                'message': f'Extracting text from file: {os.path.basename(file_path)}'
            })
            
            # Extract text from file
            brief_text = extract_text_from_file(file_path)
            
            if not brief_text:
                error_msg = f"Failed to extract text from file: {file_path}"
                print(error_msg)
                send_progress(analysis_id, {
                    'status': 'error',
                    'message': error_msg
                })
                raise Exception(error_msg)
                
            # Add extraction complete event
            send_progress(analysis_id, {
                'status': 'progress',
                'current': 1,
                'total': 1,
                'message': f'Successfully extracted {len(brief_text)} characters from {os.path.basename(file_path)}'
            })
            
            # Save extracted text to a file for debugging
            try:
                debug_file = f'extracted_text_{analysis_id}.txt'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(brief_text)
                print(f"Saved extracted text to {debug_file}")
            except Exception as e:
                print(f"Error saving extracted text to file: {e}")
        
        # Use default text if none provided
        if not brief_text:
            brief_text = "2016 WL 165971"
            citations = [brief_text]
            # Add default citation event
            send_progress(analysis_id, {
                'status': 'progress',
                'current': 0,
                'total': 1,
                'message': 'Using default citation for testing'
            })
        else:
            # Add citation extraction progress event
            send_progress(analysis_id, {
                'status': 'progress',
                'current': 0,
                'total': 1,
                'message': 'Extracting citations from document text...'
            })
            
            # Extract citations from the text
            citations = extract_citations(brief_text)
            
            # Send progress update with total citations and the extracted citations
            send_progress(analysis_id, {
                'status': 'started',
                'total_citations': len(citations),
                'extracted_citations': citations
            })
            
            # Add citation extraction result event
            if citations:
                # Add an event showing all extracted citations
                send_progress(analysis_id, {
                    'status': 'progress',
                    'current': 1,
                    'total': 1,
                    'message': f'Successfully extracted {len(citations)} citations from document',
                    'extracted_citations': citations
                })
            else:
                # If no citations found, treat the entire text as one citation
                citations = [brief_text[:100] + "..." if len(brief_text) > 100 else brief_text]
                send_progress(analysis_id, {
                    'status': 'progress',
                    'current': 1,
                    'total': 1,
                    'message': 'No specific citations found, treating entire text as one citation'
                })
        
        # Query the CourtListener API
        if api_key:
            # Add API query progress event
            send_progress(analysis_id, {
                'status': 'progress',
                'current': 0,
                'total': len(citations),
                'message': 'Querying CourtListener API...'
            })
            
            # Query the API with the entire text
            api_response = query_courtlistener_api(brief_text, api_key)
            
            # Add API response event
            send_progress(analysis_id, {
                'status': 'progress',
                'current': len(citations),
                'total': len(citations),
                'message': 'Received response from CourtListener API',
                'api_response': api_response
            })
            
            # Process the API response
            if 'error' in api_response:
                # Add error event
                send_progress(analysis_id, {
                    'status': 'error',
                    'message': f"Error querying CourtListener API: {api_response['error']}"
                })
            else:
                # Process each citation
                hallucinated_count = 0
                
                # Check if the API response contains citation data
                if 'citations' in api_response:
                    api_citations = api_response['citations']
                    print(f"API returned {len(api_citations)} citations")
                    
                    # Process each citation from our extraction
                    for i, citation in enumerate(citations):
                        # Check if this citation is in the API response
                        found = False
                        for api_citation in api_citations:
                            if citation.lower() in api_citation.get('citation', '').lower():
                                found = True
                                confidence = 0.9  # High confidence for exact match
                                explanation = f"Citation found in CourtListener database: {api_citation.get('name', 'Unknown case')}"
                                break
                        
                        # If not found, mark as potentially hallucinated
                        if not found:
                            hallucinated_count += 1
                            confidence = 0.8  # Moderate confidence for not found
                            explanation = "Citation not found in CourtListener database"
                        
                        # Add result event
                        send_progress(analysis_id, {
                            'status': 'result',
                            'citation_index': i,
                            'total': len(citations),
                            'result': {
                                'citation_text': citation,
                                'is_hallucinated': not found,
                                'confidence': confidence,
                                'explanation': explanation
                            }
                        })
                else:
                    print("API response does not contain citation data")
                    # Mark all citations as potentially hallucinated
                    for i, citation in enumerate(citations):
                        hallucinated_count += 1
                        send_progress(analysis_id, {
                            'status': 'result',
                            'citation_index': i,
                            'total': len(citations),
                            'result': {
                                'citation_text': citation,
                                'is_hallucinated': True,
                                'confidence': 0.7,
                                'explanation': "Citation not verified by CourtListener API"
                            }
                        })
                
                # Add complete event
                send_progress(analysis_id, {
                    'status': 'complete',
                    'total_citations': len(citations),
                    'hallucinated_citations': hallucinated_count,
                    'message': f"Analysis complete. Found {len(citations)} citations, {hallucinated_count} potentially hallucinated."
                })
        else:
            # No API key provided, mark all citations as unverified
            send_progress(analysis_id, {
                'status': 'progress',
                'current': 0,
                'total': len(citations),
                'message': 'No CourtListener API key provided, unable to verify citations'
            })
            
            # Mark all citations as potentially hallucinated
            for i, citation in enumerate(citations):
                send_progress(analysis_id, {
                    'status': 'result',
                    'citation_index': i,
                    'total': len(citations),
                    'result': {
                        'citation_text': citation,
                        'is_hallucinated': True,
                        'confidence': 0.5,
                        'explanation': "No CourtListener API key provided, unable to verify citation"
                    }
                })
            
            # Add complete event
            send_progress(analysis_id, {
                'status': 'complete',
                'total_citations': len(citations),
                'hallucinated_citations': len(citations),
                'message': f"Analysis complete without API verification. Found {len(citations)} citations."
            })
    
    except Exception as e:
        print(f"Error running analysis: {e}")
        traceback.print_exc()
        
        # Add error event
        send_progress(analysis_id, {
            'status': 'error',
            'message': f"Error running analysis: {str(e)}"
        })
        
        # Mark the analysis as completed
        analysis_results[analysis_id]['completed'] = True

# Routes
@app.route('/')
def index():
    return render_template('simple_fixed.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        print("\n\n==== ANALYZE ENDPOINT CALLED =====")
        print(f"Request method: {request.method}")
        print(f"Request headers: {request.headers}")
        print(f"Request form data: {request.form}")
        print(f"Request files: {request.files}")
        
        # Debug: Print all request data
        print("\nFull request details:")
        print(f"  Content-Type: {request.content_type}")
        print(f"  Content-Length: {request.content_length}")
        print(f"  Mimetype: {request.mimetype}")
        print(f"  Form keys: {list(request.form.keys())}")
        print(f"  Files keys: {list(request.files.keys()) if request.files else 'No files'}")
        
        # Debug: Print raw request data
        try:
            raw_data = request.get_data()
            print(f"\nRaw request data (first 500 bytes): {raw_data[:500]}")
        except Exception as e:
            print(f"Error getting raw data: {e}")
            
        # Debug: Print environment variables
        print(f"\nRequest environment:")
        for key, value in request.environ.items():
            if key.startswith('HTTP_') or key in ['REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH']:
                print(f"  {key}: {value}")
                
        try:
            # Generate a unique analysis ID
            analysis_id = generate_analysis_id()
            print(f"Generated analysis ID: {analysis_id}")
            
            # Initialize variables
            brief_text = None
            file_path = None
        
            # Get the API key if provided, otherwise use the default from config.json
            api_key = DEFAULT_API_KEY  # Use the default API key loaded from config.json
            if 'api_key' in request.form and request.form['api_key'].strip():
                api_key = request.form['api_key'].strip()
                print(f"API key provided in form: {api_key[:5]}...")
            else:
                print(f"Using default API key from config.json: {api_key[:5]}..." if api_key else "No API key provided or found in config.json")
        
            # Check if a file was uploaded
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    print(f"File uploaded: {file.filename}")
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    print(f"File saved to: {file_path}")
                    
                    # Debug: Print file size and first few bytes
                    try:
                        file_size = os.path.getsize(file_path)
                        print(f"File size: {file_size} bytes")
                        with open(file_path, 'rb') as f:
                            first_bytes = f.read(100)
                            print(f"First few bytes: {first_bytes}")
                    except Exception as e:
                        print(f"Error reading file: {e}")
        
            # Check if a file path was provided
            elif 'file_path' in request.form:
                file_path = request.form['file_path'].strip()
                print(f"File path provided: {file_path}")
                
                # Handle file:/// URLs
                if file_path.startswith('file:///'):
                    file_path = file_path[8:]  # Remove 'file:///' prefix
                
                # Check if the file exists
                if not os.path.isfile(file_path):
                    print(f"File not found: {file_path}")
                    return jsonify({
                        'status': 'error',
                        'message': f'File not found: {file_path}'
                    }), 404
                
                # Check if the file extension is allowed
                if not allowed_file(file_path):
                    print(f"File extension not allowed: {file_path}")
                    return jsonify({
                        'status': 'error',
                        'message': f'File extension not allowed: {file_path}'
                    }), 400
                
                print(f"Using file from path: {file_path}")
                
                # Debug: Print file size and first few bytes
                try:
                    file_size = os.path.getsize(file_path)
                    print(f"File size: {file_size} bytes")
                    with open(file_path, 'rb') as f:
                        first_bytes = f.read(100)
                        print(f"First few bytes: {first_bytes}")
                except Exception as e:
                    print(f"Error reading file: {e}")
        
            # Get the text input if provided
            if 'text' in request.form:
                brief_text = request.form['text']
                print(f"Text from form: {brief_text[:100]}...")
            elif 'briefText' in request.form:  # For backward compatibility
                brief_text = request.form['briefText']
                print(f"Brief text from form: {brief_text[:100]}...")
        
            # Check if we have either text or a file
            if not brief_text and not file_path:
                print("No text or file provided")
                return jsonify({
                    'status': 'error',
                    'message': 'No text or file provided'
                }), 400
            
            # Start the analysis in a background thread
            threading.Thread(target=run_analysis, args=(analysis_id, brief_text, file_path, api_key)).start()
        
            # Return the analysis ID to the client
            return jsonify({
                'status': 'success',
                'message': 'Analysis started',
                'analysis_id': analysis_id
            })
        except Exception as e:
            print(f"Error in analyze endpoint: {e}")
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }), 500
    else:
        # For GET requests, just return an empty response
        return jsonify({})

@app.route('/stream')
def stream():
    """Stream events for a specific analysis."""
    print("\n\n==== STREAM ENDPOINT CALLED =====")
    
    # Get the analysis ID from the query string
    analysis_id = request.args.get('id')
    if not analysis_id:
        return jsonify({'status': 'error', 'message': 'No analysis ID provided'}), 400
    
    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({'status': 'error', 'message': 'Analysis not found'}), 404
    
    def generate():
        # Send initial message
        yield 'data: {"message": "Connected to event stream for analysis ' + analysis_id + '"}\n\n'
        
        # Send all existing events
        for event in analysis_results[analysis_id]['events']:
            event_type = event.get('status', 'message')
            event_data = json.dumps(event)
            yield f'event: {event_type}\ndata: {event_data}\n\n'
        
        # If the analysis is not completed, keep the connection open
        if not analysis_results[analysis_id]['completed']:
            # Keep the connection open by sending a comment every 15 seconds
            for _ in range(60):  # Keep connection open for up to 15 minutes
                time.sleep(15)
                yield ': keepalive\n\n'
                
                # If the analysis has completed, break the loop
                if analysis_results[analysis_id]['completed']:
                    break
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Cache-Control', 'no-cache')
    response.headers.add('Connection', 'keep-alive')
    return response

@app.route('/analyze_status')
def analyze_status():
    """Check the status of an analysis."""
    print("\n\n==== ANALYZE_STATUS ENDPOINT CALLED =====")
    
    # Get the analysis ID from the query string
    analysis_id = request.args.get('id')
    if not analysis_id:
        return jsonify({'status': 'error', 'message': 'No analysis ID provided'}), 400
    
    # Check if the analysis exists
    if analysis_id not in analysis_results:
        return jsonify({'status': 'error', 'message': 'Analysis not found'}), 404
    
    # Return the current status and events
    response = jsonify({
        'status': analysis_results[analysis_id]['status'],
        'events': analysis_results[analysis_id]['events'],
        'completed': analysis_results[analysis_id]['completed']
    })
    
    # Add CORS headers to allow cross-origin requests
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Cache-Control', 'no-cache')
    response.headers.add('Connection', 'keep-alive')
    
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
