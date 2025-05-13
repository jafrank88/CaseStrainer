# Import necessary modules
from flask import Flask, send_from_directory, request, jsonify, render_template, redirect, url_for, session
import os
import sys
import json
import sqlite3
import logging
import socket
import re
import requests
import traceback
import uuid
import tempfile
from flask_session import Session
from bs4 import BeautifulSoup
import urllib.parse
from werkzeug.utils import secure_filename

# Import the API endpoints
from citation_api import citation_api

# Import the Enhanced Validator blueprint
from enhanced_validator_production import enhanced_validator_bp, register_enhanced_validator

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import HyperscanTokenizer
    EYECITE_AVAILABLE = True
    logging.info("Eyecite library loaded successfully for citation extraction")
except ImportError:
    EYECITE_AVAILABLE = False
    logging.warning("Eyecite not installed. Using regex patterns for citation extraction.")

# Create the Flask application
app = Flask(__name__, 
    static_folder=os.path.join(os.path.dirname(__file__), 'static'), 
    static_url_path='/static',
    template_folder=os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')))  # Use absolute path to root templates directory

# Add detailed logging for template loading
@app.before_request
def log_request_info():
    app.logger.info('Request path: %s', request.path)
    app.logger.info('Template folder: %s', app.template_folder)
    app.logger.info('Template folder exists: %s', os.path.exists(app.template_folder))
    if os.path.exists(app.template_folder):
        app.logger.info('Template folder contents: %s', os.listdir(app.template_folder))
        app.logger.info('Looking for template: enhanced_validator.html')
        template_path = os.path.join(app.template_folder, 'enhanced_validator.html')
        app.logger.info('Full template path: %s', template_path)
        app.logger.info('Template file exists: %s', os.path.exists(template_path))

# Configure environment-specific settings
if os.environ.get('FLASK_ENV') == 'production':
    app.config['BASE_URL'] = 'https://wolf.law.uw.edu/casestrainer'
    app.config['API_BASE_URL'] = 'https://wolf.law.uw.edu/casestrainer/api'
else:
    app.config['BASE_URL'] = 'http://localhost:5000'
    app.config['API_BASE_URL'] = 'http://localhost:5000/api'

# Configure secret key for sessions
app.secret_key = os.environ.get('SECRET_KEY', 'casestrainer-secret-key')

# Configure server-side session storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(tempfile.gettempdir(), 'casestrainer_sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize the Flask-Session extension
Session(app)
app.logger.info(f"Configured server-side session storage at {app.config['SESSION_FILE_DIR']}")

# Create the session directory if it doesn't exist
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.INFO)
app.logger.info("Starting CaseStrainer application with Vue.js frontend")

# Register the citation API blueprint
app.register_blueprint(citation_api, url_prefix='/api')
app.logger.info("Citation API registered with prefix /api")

# Register the Enhanced Validator blueprint
register_enhanced_validator(app)
app.logger.info("Enhanced Validator blueprint registered with the application")

# Create a placeholder for the DATABASE_FILE constant
DATABASE_FILE = 'citations.db'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v3/opinions/'

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load API keys from config.json if available
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

def verify_citation(citation):
    """Verify a citation using CourtListener API."""
    try:
        # First try CourtListener API
        import requests
        from urllib.parse import quote
        
        # Encode the citation for the URL
        encoded_citation = quote(citation)
        url = f"{COURTLISTENER_API_URL}?cite={encoded_citation}"
        
        headers = {
            'Authorization': f'Token {DEFAULT_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['count'] > 0:
                return {
                    'citation': citation,
                    'verified': True,
                    'source': 'CourtListener',
                    'details': data['results'][0]
                }
        
        # If not found in CourtListener, try other sources
        # For now, we'll just return unverified
        return {
            'citation': citation,
            'verified': False,
            'source': None,
            'details': None
        }
    except Exception as e:
        print(f"Error verifying citation: {e}")
        return {
            'citation': citation,
            'verified': False,
            'source': None,
            'details': None,
            'error': str(e)
        }

# We'll import the original app_final functionality AFTER defining our Vue.js routes
# This ensures our routes take precedence

# Add Vue.js routes to the Flask application
# Serve the Vue.js static files (keep the /vue/ path for backward compatibility)
@app.route('/vue/<path:path>')
@app.route('/casestrainer/vue/<path:path>')
def serve_vue_static_compat(path):
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
    return send_from_directory(vue_dist_dir, path)

# Serve static assets from the Vue.js build at the root
@app.route('/js/<path:path>')
@app.route('/casestrainer/js/<path:path>')
def serve_vue_js(path):
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue', 'js')
    return send_from_directory(vue_dist_dir, path)

@app.route('/css/<path:path>')
@app.route('/casestrainer/css/<path:path>')
def serve_vue_css(path):
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue', 'css')
    return send_from_directory(vue_dist_dir, path)

@app.route('/img/<path:path>')
@app.route('/casestrainer/img/<path:path>')
def serve_vue_img(path):
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue', 'img')
    return send_from_directory(vue_dist_dir, path)

@app.route('/fonts/<path:path>')
@app.route('/casestrainer/fonts/<path:path>')
def serve_vue_fonts(path):
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue', 'fonts')
    return send_from_directory(vue_dist_dir, path)

# Serve the Enhanced Validator template at the root URL
@app.route('/')
def redirect_to_enhanced_validator():
    from flask import redirect
    return redirect('/enhanced-validator')

@app.route('/casestrainer/')
def serve_vue_index():
    return render_template('enhanced_validator.html')

# Backward compatibility routes
@app.route('/vue/')
@app.route('/casestrainer/vue/')
def serve_vue_index_compat():
    return serve_vue_index()

@app.route('/vue')
@app.route('/casestrainer/vue')
def redirect_to_vue():
    return serve_vue_index()

# Redirect /original to /api for the original interface
@app.route('/original')
@app.route('/casestrainer/original')
def redirect_to_api():
    return redirect('/api/')

@app.route('/original/')
@app.route('/casestrainer/original/')
def redirect_to_api_slash():
    return redirect('/api/')

# Special route to handle Vue.js hash-based routing
@app.route('/vue-enhanced-validator')
@app.route('/casestrainer/vue-enhanced-validator')
def redirect_from_vue_to_enhanced_validator():
    return redirect('/')

# Serve the Enhanced Validator link page
@app.route('/enhanced-validator-link')
@app.route('/casestrainer/enhanced-validator-link')
def serve_enhanced_validator_link():
    return send_from_directory('static', 'enhanced_validator_link.html')

# Serve JSON files directly
@app.route('/citation_verification_results.json')
@app.route('/casestrainer/citation_verification_results.json')
def serve_citation_verification_results():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'citation_verification_results.json')

@app.route('/database_verification_results.json')
@app.route('/casestrainer/database_verification_results.json')
def serve_database_verification_results():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'database_verification_results.json')

# We'll use Flask sessions to store user-specific citation data instead of a global variable
# This ensures each user only sees their own data

# Function to initialize session with sample citation data if empty
def initialize_session_data():
    """Initialize session with sample citation data if it's empty."""
    from flask import session
    if 'user_citations' not in session or not session['user_citations']:
        app.logger.info("Initializing session with sample citation data")
        session['user_citations'] = [
            {
                'citation': '347 U.S. 483',
                'found': True,
                'found_case_name': 'Brown v. Board of Education',
                'confidence': 0.95,
                'source': 'Multi-source Verification',
                'url': 'https://scholar.google.com/scholar_case?case=12120372216939101759',
                'explanation': 'The landmark case Brown v. Board of Education (347 U.S. 483) established that separate educational facilities are inherently unequal.'
            },
            {
                'citation': '410 U.S. 113',
                'found': True,
                'found_case_name': 'Roe v. Wade',
                'confidence': 0.92,
                'source': 'CourtListener',
                'cl_id': '12345',
                'url': 'https://www.courtlistener.com/opinion/12345',
                'explanation': "The Court's decision in Roe v. Wade (410 U.S. 113) recognized a woman's right to choose."
            },
            {
                'citation': '5 U.S. 137',
                'found': True,
                'found_case_name': 'Marbury v. Madison',
                'confidence': 0.88,
                'source': 'Multi-source Verification',
                'url': 'https://caselaw.findlaw.com/us-supreme-court/5/137.html',
                'explanation': 'Marbury v. Madison (5 U.S. 137) established the principle of judicial review.'
            },
            {
                'citation': '123 U.S. 456',
                'found': False,
                'found_case_name': 'Smith v. Jones',
                'confidence': 0.0,
                'source': 'Not found',
                'explanation': 'Citation not found in any source.'
            }
        ]

# API endpoints for the third and fourth tabs
@app.route('/api/confirmed_with_multitool_data')
@app.route('/api/confirmed-with-multitool-data')
@app.route('/casestrainer/api/confirmed_with_multitool_data')
def confirmed_with_multitool_data():
    """API endpoint for citations confirmed with multi-tool verification."""
    try:
        # Initialize session data if empty
        initialize_session_data()
        
        # Use the user's session data
        from flask import session
        user_citations = session.get('user_citations', [])
        app.logger.info(f"Confirmed with multitool data request received. Citations available: {len(user_citations)}")
        
        # Filter for citations that were found but not from CourtListener
        multitool_citations = [{
            'citation_text': c['citation'],
            'case_name': c.get('found_case_name', 'Unknown'),
            'confidence': c.get('confidence', 0.8),
            'source': c.get('source', 'Multi-source Verification'),
            'url': c.get('url', ''),
            'explanation': c.get('explanation', f"Verified by {c.get('source', 'Multi-source Verification')}"),
            'document': ''
        } for c in user_citations if c.get('found', False) and c.get('source') != 'CourtListener']
        
        app.logger.info(f"Found {len(multitool_citations)} multitool citations")
        
        # Return the multitool citations (even if empty)
        return jsonify({
            'status': 'success',
            'citations': multitool_citations
        })
    except Exception as e:
        app.logger.error(f"Error in confirmed_with_multitool_data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Use HyperscanTokenizer for citation extraction if available
if EYECITE_AVAILABLE:
    tokenizer = HyperscanTokenizer()
    app.logger.info("Using HyperscanTokenizer for citation extraction")
else:
    app.logger.warning("HyperscanTokenizer not available. Using default tokenizer.")

# API endpoint to fetch content from a URL
@app.route('/api/fetch_url', methods=['POST', 'OPTIONS'])
@app.route('/casestrainer/api/fetch_url', methods=['POST', 'OPTIONS'])
def fetch_url():
    """API endpoint to fetch content from a URL and extract text for citation analysis."""
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
        app.logger.info(f"Fetching content from URL: {url}")
        
        # Clear previous citation data in session
        from flask import session
        session.pop('user_citations', None)
        app.logger.info("Cleared previous citation data in user session")
        
        # Initialize session data
        initialize_session_data()
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
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
        
        # Handle PDF files directly
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            app.logger.info("Detected PDF file, using direct PDF extraction")
            
            # Save PDF to temporary file
            import tempfile
            import PyPDF2
            import io
            
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                # Download the PDF in chunks to avoid memory issues
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            app.logger.info(f"PDF saved to temporary file: {temp_file_path}")
            
            try:
                # Extract text from PDF
                text = ""
                with open(temp_file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)
                    app.logger.info(f"PDF has {num_pages} pages")
                    
                    # Limit to first 20 pages for large PDFs
                    max_pages = min(num_pages, 20)
                    app.logger.info(f"Processing first {max_pages} pages")
                    
                    for page_num in range(max_pages):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                
                # Clean up the text (remove excessive whitespace)
                text = re.sub(r'\s+', ' ', text).strip()
                app.logger.info(f"Extracted {len(text)} characters from PDF")
                
                # If eyecite is available, use it to extract citations directly
                if EYECITE_AVAILABLE and len(text) > 0:
                    app.logger.info("Using eyecite to extract citations from PDF")
                    try:
                        # Extract citations using eyecite
                        citations = get_citations(text)
                        app.logger.info(f"Found {len(citations)} citations with eyecite")
                        
                        # Resolve citations
                        resolved_citations = resolve_citations(citations)
                        
                        # Store citations in session
                        eyecite_citations = []
                        for citation in citations:
                            citation_info = {
                                'citation': str(citation),
                                'found': True,
                                'found_case_name': getattr(citation, 'plaintiff', '') + ' v. ' + getattr(citation, 'defendant', '') if hasattr(citation, 'plaintiff') and hasattr(citation, 'defendant') else 'Unknown',
                                'reporter': getattr(citation, 'reporter', ''),
                                'volume': getattr(citation, 'volume', ''),
                                'page': getattr(citation, 'page', ''),
                                'year': getattr(citation, 'year', ''),
                                'court': getattr(citation, 'court', ''),
                                'source': 'Eyecite'
                            }
                            eyecite_citations.append(citation_info)
                        
                        # Store citations in session
                        session['user_citations'] = eyecite_citations
                        app.logger.info(f"Stored {len(eyecite_citations)} citations in session")
                    except Exception as e:
                        app.logger.error(f"Error extracting citations with eyecite: {e}")
                        # Continue with standard text extraction
                
                # Clean up the temporary file
                import os
                os.unlink(temp_file_path)
            except Exception as e:
                app.logger.error(f"Error extracting text from PDF: {e}")
                # Clean up the temporary file
                import os
                os.unlink(temp_file_path)
                raise
        else:
            # Handle HTML and other text-based content
            app.logger.info("Processing as HTML/text content")
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up the text (remove excessive whitespace)
            text = re.sub(r'\s+', ' ', text).strip()
        
        app.logger.info(f"Successfully extracted {len(text)} characters from URL")
        
        # Check if eyecite was used to process citations
        eyecite_processed = False
        citations_count = 0
        if EYECITE_AVAILABLE and 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            eyecite_processed = True
            # Get citation count from session
            user_citations = session.get('user_citations', [])
            citations_count = len(user_citations)
            app.logger.info(f"Eyecite processed {citations_count} citations from PDF")
            app.logger.info(f"Session citations: {user_citations}")
        
        return jsonify({
            'status': 'success',
            'text': text,
            'url': url,
            'eyecite_processed': eyecite_processed,
            'citations_count': citations_count
        })
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching URL: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Error fetching URL: {str(e)}"
        }), 500
    except Exception as e:
        app.logger.error(f"Error in fetch_url: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Add a direct URL analyze endpoint
@app.route('/api/direct_url_analyze', methods=['POST', 'OPTIONS'])
@app.route('/casestrainer/api/direct_url_analyze', methods=['POST', 'OPTIONS'])
def direct_url_analyze():
    """Endpoint to directly analyze a URL for citations without storing in session.
    Can be called directly via the API or forwarded from enhanced_analyze."""
    # Log request details for debugging
    app.logger.info("Direct URL analysis request received")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Request content type: {request.content_type}")
    app.logger.info(f"Forwarded data: {forwarded_data}")
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        # Generate a unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        app.logger.info(f"Generated analysis ID: {analysis_id}")
        
        # Get URL from either forwarded data or request
        if forwarded_data and 'url' in forwarded_data:
            url = forwarded_data['url']
            app.logger.info(f"URL provided from forwarded data: {url}")
        else:
            # Parse the JSON data from the request
            try:
                data = request.get_json(force=True)
                if not data or 'url' not in data:
                    error_msg = "Missing URL in request data"
                    app.logger.error(error_msg)
                    return jsonify({
                        'status': 'error',
                        'message': error_msg
                    }), 400
                
                url = data['url']
                app.logger.info(f"URL provided from request: {url}")
            except Exception as json_error:
                error_msg = f"Error parsing JSON data: {str(json_error)}"
                app.logger.error(error_msg)
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), 400
        
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
        
        try:
            # Fetch the URL content
            app.logger.info(f"Fetching content from URL: {url}")
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check content type to handle different file types
            content_type = response.headers.get('Content-Type', '').lower()
            app.logger.info(f"Content type: {content_type}")
            
            # Create uploads directory if it doesn't exist
            os.makedirs('uploads', exist_ok=True)
            
            # Initialize document_text
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
                from enhanced_validator_production import extract_text_from_file
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
                document_text = re.sub(r'\s+', ' ', document_text).strip()
            
            app.logger.info(f"Successfully extracted {len(document_text)} characters from URL")
            
            # Extract citations from text
            citations = []
            extracted_citations = extract_citations_from_text(document_text)
            app.logger.info(f"Extracted {len(extracted_citations)} citations from URL content")
            
            # Validate each citation
            for citation_text in extracted_citations:
                validation_result = verify_citation(citation_text)
                
                # Format the result
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
            
            # Format citations for the response
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
            
            # Return the results directly without storing in session
            response_data = {
                'status': 'success',
                'analysis_id': analysis_id,
                'citations': formatted_citations,
                'citations_count': len(citations),
                'url': url
            }
            
            app.logger.info(f"Direct URL analysis completed for ID: {analysis_id}")
            return jsonify(response_data)
            
        except Exception as url_error:
            error_msg = f"Error fetching URL content: {str(url_error)}"
            app.logger.error(error_msg)
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
            
    except Exception as e:
        error_msg = f"Error analyzing URL: {str(e)}"
        app.logger.error(error_msg)
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': error_msg
        }), 500

# Skip importing from app_final.py since it has a syntax error
try:
    # Try to import specific functions from enhanced_validator_production instead
    from enhanced_validator_production import is_landmark_case, validate_citation
    print("Imported functionality from enhanced_validator_production")
except Exception as e:
    print(f"Warning: Error importing from enhanced_validator_production: {e}")
    
    # Define fallback functions
    def is_landmark_case(citation_text):
        """Check if a citation refers to a landmark case."""
        return False
    
    def validate_citation(citation_text):
        """Validate a citation using multiple methods."""
        return {
            'verified': False,
            'case_name': None,
            'validation_method': None
        }
    
    print("Using fallback functionality")

def get_ip_address():
    """Get the server's IP address for logging purposes"""
    try:
        # Get the server's IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        app.logger.error(f"Error getting IP address: {e}")
        return "unknown"

# Global state to track processing progress
processing_state = {
    'total_citations': 0,
    'processed_citations': 0,
    'is_complete': False
}

@app.route('/api/processing_progress', methods=['GET'])
def processing_progress():
    """Get the current progress of citation processing."""
    return jsonify({
        'status': 'success',
        'total_citations': processing_state['total_citations'],
        'processed_citations': processing_state['processed_citations'],
        'is_complete': processing_state['is_complete']
    })

@app.route('/api/validate_citations', methods=['POST'])
def validate_citations():
    """Validate citations from text or file input."""
    try:
        # Reset processing state
        processing_state['total_citations'] = 0
        processing_state['processed_citations'] = 0
        processing_state['is_complete'] = False
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            
            if file:
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                # Extract citations from file
                citations = extract_citations_from_file(filepath)
        else:
            # Handle text input
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({'error': 'No text provided'}), 400
            
            # Extract citations from text
            citations = extract_citations_from_text(data['text'])
        
        # Set total citations count
        processing_state['total_citations'] = len(citations)
        
        # Process citations
        verified_citations = []
        unverified_citations = []
        
        for i, citation in enumerate(citations):
            # Update progress
            processing_state['processed_citations'] = i + 1
            
            # Verify citation
            result = verify_citation(citation)
            if result['verified']:
                verified_citations.append(result)
            else:
                unverified_citations.append(result)
        
        # Mark processing as complete
        processing_state['is_complete'] = True
        
        return jsonify({
            'total_citations': len(citations),
            'verified_citations': len(verified_citations),
            'unverified_citations': len(unverified_citations),
            'citations': {
                'verified': verified_citations,
                'unverified': unverified_citations
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_citations_from_file(filepath):
    """Extract citations from a file."""
    try:
        # Read file content based on file type
        if filepath.endswith('.pdf'):
            # Use PyPDF2 for PDF files
            import PyPDF2
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
        elif filepath.endswith(('.doc', '.docx')):
            # Use python-docx for Word files
            import docx
            doc = docx.Document(filepath)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            # Assume text file
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        
        return extract_citations_from_text(text)
    except Exception as e:
        print(f"Error extracting citations from file: {e}")
        return []

def extract_citations_from_text(text):
    """Extract citations from text using eyecite."""
    try:
        from eyecite import get_citations
        citations = get_citations(text)
        return [citation.matched_text() for citation in citations]
    except Exception as e:
        print(f"Error extracting citations from text: {e}")
        return []

if __name__ == '__main__':
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run CaseStrainer with Vue.js frontend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--use-cheroot', action='store_true', help='Use Cheroot WSGI server (production mode)')
    parser.add_argument('--env', choices=['development', 'production'], default='development', help='Environment to run in')
    args = parser.parse_args()
    
    # Set environment
    os.environ['FLASK_ENV'] = args.env
    
    # Check if we should run with Cheroot (production) or Flask's dev server
    use_cheroot = args.use_cheroot or os.environ.get('USE_CHEROOT', 'True').lower() in ('true', '1', 't')
    
    # Log server information
    server_ip = get_ip_address()
    app.logger.info(f"Server IP address: {server_ip}")
    app.logger.info(f"Starting CaseStrainer with Vue.js frontend on {args.host}:{args.port}")
    app.logger.info(f"Using Cheroot: {use_cheroot}")
    app.logger.info(f"Environment: {args.env}")
    app.logger.info(f"Base URL: {app.config['BASE_URL']}")
    app.logger.info(f"API Base URL: {app.config['API_BASE_URL']}")
    
    if use_cheroot:
        try:
            from cheroot.wsgi import Server as WSGIServer
            app.logger.info("Starting with Cheroot WSGI server (production mode)")
            
            # Configure Cheroot server with appropriate settings for production
            server = WSGIServer((args.host, args.port), app)
            server.max_request_header_size = 0  # No limit
            server.max_request_body_size = 0  # No limit
            server.request_queue_size = 50  # Increased from default
            server.nodelay = True  # Disable Nagle's algorithm for better performance
            
            try:
                app.logger.info(f"Server started on http://{args.host}:{args.port}")
                app.logger.info(f"External access URL: https://wolf.law.uw.edu/casestrainer/")
                server.start()
            except KeyboardInterrupt:
                server.stop()
                app.logger.info("Server stopped due to keyboard interrupt.")
            except Exception as e:
                app.logger.error(f"Error starting Cheroot server: {e}")
                sys.exit(1)
        except ImportError:
            app.logger.warning("Cheroot not installed. Installing now...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cheroot"])
                app.logger.info("Cheroot installed. Please restart the application.")
                sys.exit(0)
            except Exception as e:
                app.logger.error(f"Failed to install Cheroot: {e}")
                app.logger.warning("Falling back to Flask development server")
                app.run(debug=args.debug, host=args.host, port=args.port)
    else:
        app.logger.info("Starting with Flask development server")
        app.run(debug=args.debug, host=args.host, port=args.port)
