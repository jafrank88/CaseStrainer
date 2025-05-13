import os
import json
import time
import uuid
import threading
import requests
import tempfile
import re
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory, Response, session
from flask_cors import CORS
from PyPDF2 import PdfReader
import docx

# Create Flask app
app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())  # Set a secret key for sessions
CORS(app)  # Enable CORS for Word add-in support

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v3/citation-lookup/'

# Load configuration from config.json if available
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
DEFAULT_API_KEY = None

try:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            DEFAULT_API_KEY = config.get('courtlistener_api_key')
            print(f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}..." if DEFAULT_API_KEY else "No API key found in config.json")
except Exception as e:
    print(f"Error loading config.json: {e}")
    DEFAULT_API_KEY = None

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global storage for analysis results
analysis_results = {}

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from different file types
def extract_text_from_file(file_path):
    print(f"\n=== EXTRACTING TEXT FROM FILE ===\nFile path: {file_path}")
    try:
        if not os.path.exists(file_path):
            print(f"Error: File does not exist: {file_path}")
            return ""
            
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        print(f"File extension: {ext}")
        
        if ext == '.pdf':
            # Extract text from PDF
            print("Extracting text from PDF file...")
            try:
                with open(file_path, 'rb') as file:
                    reader = PdfReader(file)
                    print(f"PDF has {len(reader.pages)} pages")
                    text = ''
                    for i, page in enumerate(reader.pages):
                        print(f"Extracting text from page {i+1}/{len(reader.pages)}")
                        page_text = page.extract_text()
                        text += page_text + '\n'
                    print(f"Successfully extracted {len(text)} characters from PDF")
                    
                    # Save the extracted text to a file for inspection
                    try:
                        with open('extracted_pdf_text.txt', 'w', encoding='utf-8') as f:
                            f.write(text)
                        print(f"Extracted PDF text saved to extracted_pdf_text.txt")
                    except Exception as e:
                        print(f"Error saving extracted text to file: {e}")
                    
                    return text
            except Exception as e:
                print(f"Error extracting text from PDF: {e}")
                import traceback
                traceback.print_exc()
                return ""
        elif ext == '.docx':
            # Extract text from DOCX
            print("Extracting text from DOCX file...")
            try:
                doc = docx.Document(file_path)
                text = '\n'.join([para.text for para in doc.paragraphs])
                print(f"Successfully extracted {len(text)} characters from DOCX")
                return text
            except Exception as e:
                print(f"Error extracting text from DOCX: {e}")
                import traceback
                traceback.print_exc()
                return ""
        elif ext == '.txt':
            # Extract text from TXT
            print("Extracting text from TXT file...")
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    print(f"Successfully extracted {len(text)} characters from TXT")
                    return text
            except UnicodeDecodeError:
                # Try with a different encoding if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        text = file.read()
                        print(f"Successfully extracted {len(text)} characters from TXT using latin-1 encoding")
                        return text
                except Exception as e:
                    print(f"Error extracting text from TXT with latin-1 encoding: {e}")
                    return ""
            except Exception as e:
                print(f"Error extracting text from TXT: {e}")
                import traceback
                traceback.print_exc()
                return ""
        else:
            print(f"Unsupported file extension: {ext}")
            return ""
    except Exception as e:
        print(f"Error extracting text from file: {e}")
        import traceback
        traceback.print_exc()
        return ""

# Function to extract citations from text
def extract_citations(text):
    print(f"Extracting citations from text of length: {len(text)}")
    # This is a simple implementation - in a real application, you would use a more sophisticated approach
    # For example, using regex patterns or a legal citation extraction library
    
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
def query_courtlistener_api(citation, api_key):
    print(f"\n=== QUERYING COURTLISTENER API ===\nCitation text length: {len(citation)}\nAPI Key: {api_key[:5]}...")
    try:
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
        
        # According to the documentation, we need to send a POST request with the text containing citations
        data = {
            'text': citation
        }
        
        print(f"Making request to: {COURTLISTENER_API_URL}")
        print(f"Headers: {headers}")
        print(f"Data length: {len(citation)} characters")
        print(f"First 100 chars of text: {citation[:100]}...")
        
        # Make the API request
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                print(f"Response is valid JSON")
                print(f"Response keys: {list(response_json.keys()) if isinstance(response_json, dict) else 'Not a dictionary'}")
                print(f"Response content: {json.dumps(response_json)[:500]}...")
                
                # Log the full response to a file for inspection
                with open('api_response.json', 'w') as f:
                    json.dump(response_json, f, indent=2)
                print(f"Full response saved to api_response.json")
                
                return response_json
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                print(f"Response text: {response.text[:500]}...")
                return None
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            return None
    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        import traceback
        traceback.print_exc()
        return None

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
            analysis_results[analysis_id]['events'].append({
                'status': 'progress',
                'current': 0,
                'total': 1,
                'message': 'Using default citation for testing'
            })
        else:
            # Add citation extraction progress event
            analysis_results[analysis_id]['events'].append({
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
                # First, add a summary event
                analysis_results[analysis_id]['events'].append({
                    'status': 'progress',
                    'current': 1,
                    'total': 1,
                    'message': f'Successfully extracted {len(citations)} citations from document'
                })
                
                # Then, add an event showing all extracted citations
                analysis_results[analysis_id]['events'].append({
                    'status': 'progress',
                    'current': 1,
                    'total': 1,
                    'message': 'Extracted citations:',
                    'extracted_citations': citations
                })
            else:
                # If no citations found, treat the entire text as one citation
                citations = [brief_text[:100] + "..." if len(brief_text) > 100 else brief_text]
                analysis_results[analysis_id]['events'].append({
                    'status': 'progress',
                    'current': 1,
                    'total': 1,
                    'message': 'No specific citations found, treating entire text as one citation'
                })
        
        # Add initial event
        analysis_results[analysis_id]['events'].append({
            'status': 'started',
            'total_citations': len(citations)
        })
        
        # Query the CourtListener API with the full document text
        api_response = None
        citation_results = {}
        
        if api_key and brief_text:
            # Add progress event for API query
            analysis_results[analysis_id]['events'].append({
                'status': 'progress',
                'current': 0,
                'total': len(citations),
                'message': f'Sending document text to CourtListener API for citation analysis...'
            })
            
            # Query the API with the full document text
            print(f"Querying CourtListener API with full document text using API key: {api_key[:5]}...")
            api_response = query_courtlistener_api(brief_text, api_key)
            
            if api_response:
                print(f"Received response from CourtListener API: {json.dumps(api_response)[:100]}...")
                # Add API response event
                analysis_results[analysis_id]['events'].append({
                    'status': 'progress',
                    'current': 0,
                    'total': len(citations),
                    'message': f'Received API response with citation data',
                    'api_response': api_response  # Include the raw API response
                })
                
                # Store the citation results for later processing
                citation_results = api_response
            else:
                # Add API error event
                analysis_results[analysis_id]['events'].append({
                    'status': 'progress',
                    'current': 0,
                    'total': len(citations),
                    'message': f'Error receiving API response'
                })
        
        # Process each citation
        hallucinated_count = 0
        
        for idx, citation in enumerate(citations):
            # Add progress event
            analysis_results[analysis_id]['events'].append({
                'status': 'progress',
                'current': idx + 1,
                'total': len(citations),
                'message': f'Checking citation {idx + 1} of {len(citations)}: {citation}'
            })
            
            # Default values
            is_hallucinated = True  # Default to hallucinated unless found in API response
            confidence = 0.85
            explanation = "This citation was not found in the database."
            context = "No context available."
            
            # Check if this citation was found in the API response
            if citation_results:
                # Normalize the citation for comparison
                normalized_citation = citation.strip().lower()
                
                # Check if this citation appears in the API response
                citation_found = False
                matching_opinions = []
                
                # Look through all citation keys in the response
                for cite_key, opinions in citation_results.items():
                    # Simple string matching - could be improved with more sophisticated matching
                    if normalized_citation in cite_key.lower() or cite_key.lower() in normalized_citation:
                        if opinions and len(opinions) > 0:
                            citation_found = True
                            matching_opinions.extend(opinions)
                
                if citation_found:
                    is_hallucinated = False
                    confidence = 0.95
                    explanation = "Citation found in CourtListener database."
                    context = json.dumps(matching_opinions[:3]) if matching_opinions else "No context available."
                    
                    # Add detailed result event
                    analysis_results[analysis_id]['events'].append({
                        'status': 'progress',
                        'current': idx + 1,
                        'total': len(citations),
                        'message': f'Citation verified: {citation}',
                        'matching_opinions': matching_opinions[:3] if matching_opinions else []
                    })
                else:
                    # Add not found event
                    analysis_results[analysis_id]['events'].append({
                        'status': 'progress',
                        'current': idx + 1,
                        'total': len(citations),
                        'message': f'Citation not found in database: {citation}'
                    })
            
            # Add result event
            result = {
                'citation_text': citation,
                'is_hallucinated': is_hallucinated,
                'confidence': confidence,
                'context': context,
                'explanation': explanation
            }
            
            analysis_results[analysis_id]['events'].append({
                'status': 'result',
                'citation_index': idx,
                'result': result,
                'total': len(citations)
            })
            
            # Count hallucinated citations
            if is_hallucinated:
                hallucinated_count += 1
            
            # Add a small delay between citations to avoid rate limiting
            if idx < len(citations) - 1 and api_key:
                time.sleep(1.0)  # 1 second delay to handle 60 citations per minute
        
        # Add completion event
        analysis_results[analysis_id]['events'].append({
            'status': 'complete',
            'total_citations': len(citations),
            'hallucinated_citations': hallucinated_count
        })
        
        # Mark as completed
        analysis_results[analysis_id]['status'] = 'complete'
        analysis_results[analysis_id]['completed'] = True
        
        print(f"Analysis completed for ID: {analysis_id}, found {hallucinated_count} hallucinated citations out of {len(citations)}")
        
        # Clean up old analyses after some time
        threading.Timer(300, lambda: analysis_results.pop(analysis_id, None)).start()
        
    except Exception as e:
        print(f"Error in analysis {analysis_id}: {str(e)}")
        # If there's an error, mark the analysis as failed
        if analysis_id in analysis_results:
            analysis_results[analysis_id]['status'] = 'error'
            analysis_results[analysis_id]['error'] = str(e)
            analysis_results[analysis_id]['completed'] = True
            
            # Add error event
            analysis_results[analysis_id]['events'].append({
                'status': 'error',
                'message': f"Error during analysis: {str(e)}"
            })
    
    # This function is now complete with proper error handling

@app.route('/')
def index():
    return render_template('index_fixed.html')

@app.route('/fixed')
def fixed():
    return render_template('fixed_form.html')

@app.route('/test_sse.html')
def test_sse():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_sse.html')

@app.route('/test_sse_simple.html')
def test_sse_simple():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_sse_simple.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        print("==== ANALYZE ENDPOINT CALLED =====")
        print(f"Request method: {request.method}")
        print(f"Request headers: {request.headers}")
        
        # Generate a unique analysis ID
        analysis_id = generate_analysis_id()
        print(f"Generated analysis ID: {analysis_id}")
        
        # Initialize variables
        brief_text = None
        file_path = None
        
        # Get the API key if provided, otherwise use the default from config.json
        api_key = DEFAULT_API_KEY  # Use the default API key loaded from config.json
        if 'api_key' in request.form and request.form['api_key'].strip():
            api_key = request.form['api_key']
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
        
        # Generate a unique ID for this analysis
        analysis_id = generate_analysis_id()
        print(f"Generated analysis ID: {analysis_id}")
        
        # Start the analysis in a background thread
        threading.Thread(target=run_analysis, args=(analysis_id, brief_text, file_path, api_key)).start()
        
        # Return the analysis ID to the client
        return jsonify({
            'status': 'success',
            'message': 'Analysis started',
            'analysis_id': analysis_id
        })
    else:
        # For GET requests, just return an empty response
        return jsonify({})

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
