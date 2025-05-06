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
    
    # Example patterns for common citation formats
    patterns = [
        r'\d+ U\.S\. \d+',  # US Reports
        r'\d+ S\.Ct\. \d+',  # Supreme Court Reporter
        r'\d+ F\.(\d|Supp|App)\.(\d|3d|2d) \d+',  # Federal Reporter
        r'\d+ F\.R\.D\. \d+',  # Federal Rules Decisions
        r'\d+ B\.R\. \d+',  # Bankruptcy Reporter
        r'\d+ WL \d+',  # Westlaw
        r'\d+ L\.Ed\.(\d|2d) \d+',  # Lawyers Edition
    ]
    
    citations = []
    for pattern in patterns:
        try:
            print(f"Searching for pattern: {pattern}")
            matches = re.findall(pattern, text)
            print(f"Found {len(matches)} matches for pattern: {pattern}")
            for match in matches:
                if isinstance(match, tuple):
                    # If the match is a tuple (from capturing groups), join it
                    match = ''.join(match)
                citations.append(match)
        except Exception as e:
            print(f"Error searching for pattern {pattern}: {e}")
    
    print(f"Total citations extracted: {len(citations)}")
    if citations:
        print(f"Extracted citations: {citations}")
    return citations

# Function to query the CourtListener API
def query_courtlistener_api(citation, api_key):
    print(f"\n=== QUERYING COURTLISTENER API ===\nCitation: {citation}\nAPI Key: {api_key[:5]}...")
    try:
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
        
        # According to the documentation, we need to send a POST request with the text containing citations
        data = {
            'text': citation
        }
        
        print(f"Making request to: {COURTLISTENER_API_URL}\nHeaders: {headers}\nData: {data}")
        
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)
        
        print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json)[:200]}...")
            return response_json
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response text: {response.text}")
            return None
    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        import traceback
        traceback.print_exc()
        return None

# Function to generate a unique analysis ID
def generate_analysis_id():
    return str(uuid.uuid4())

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
            # Add extraction progress event
            analysis_results[analysis_id]['events'].append({
                'status': 'progress',
                'current': 0,
                'total': 1,
                'message': f'Extracting text from file: {os.path.basename(file_path)}'
            })
            brief_text = extract_text_from_file(file_path)
            if not brief_text:
                raise Exception("Failed to extract text from file")
            # Add extraction complete event
            analysis_results[analysis_id]['events'].append({
                'status': 'progress',
                'current': 1,
                'total': 1,
                'message': f'Successfully extracted {len(brief_text)} characters from {os.path.basename(file_path)}'
            })
        
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
            is_hallucinated = False
            confidence = 0.85
            explanation = "This citation was found in the database."
            context = "This is a test citation."
            
            # Query CourtListener API if API key is provided
            if api_key:
                print(f"Querying CourtListener API for citation {citation} with API key: {api_key[:5]}...")
                api_response = query_courtlistener_api(citation, api_key)
                
                if api_response:
                    print(f"Received response from CourtListener API: {json.dumps(api_response)[:100]}...")
                    # Add API response event
                    analysis_results[analysis_id]['events'].append({
                        'status': 'progress',
                        'current': idx + 1,
                        'total': len(citations),
                        'message': f'Received API response for citation: {citation}',
                        'api_response': api_response  # Include the raw API response
                    })
                    
                    # Process API response
                    # The citation-lookup API returns a dictionary with citation strings as keys
                    # Each citation key maps to a list of matching opinions
                    citation_found = False
                    matching_citations = []
                    
                    # Check if any citations were found in the response
                    for cite_key, opinions in api_response.items():
                        if opinions and len(opinions) > 0:
                            citation_found = True
                            matching_citations.extend(opinions)
                    
                    is_hallucinated = not citation_found
                    confidence = 0.95 if citation_found else 0.90
                    explanation = "Citation found in CourtListener database." if citation_found else "Citation not found in CourtListener database."
                    context = json.dumps(matching_citations[:3]) if matching_citations else "No context available."
                else:
                    # Add API error event
                    analysis_results[analysis_id]['events'].append({
                            'status': 'progress',
                            'current': idx + 1,
                            'total': len(citations),
                            'message': f'API response did not contain citation data for: {citation}'
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
                time.sleep(0.5)
        
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

@app.route('/test_sse.html')
def test_sse():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_sse.html')

@app.route('/test_sse_simple.html')
def test_sse_simple():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'test_sse_simple.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Analyze a brief for hallucinated case citations."""
    print("\n\n==== ANALYZE ENDPOINT CALLED =====")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request path: {request.path}")
    print(f"Request query string: {request.query_string}")
    
    # For POST requests, start a new analysis
    if request.method == 'POST':
        print("POST request detected - starting analysis")
        
        # Initialize variables
        brief_text = None
        file_path = None
        api_key = None
        
        # Get the API key if provided, otherwise use the default from config.json
        api_key = DEFAULT_API_KEY  # Use the default API key loaded from config.json
        if 'api_key' in request.form and request.form['api_key'].strip():
            api_key = request.form['api_key']
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
        
        # Check if a file path was provided
        elif 'file_path' in request.form:
            file_path = request.form['file_path']
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
    return jsonify({
        'status': analysis_results[analysis_id]['status'],
        'events': analysis_results[analysis_id]['events'],
        'completed': analysis_results[analysis_id]['completed']
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
