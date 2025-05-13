import os
import re
import uuid
import json
import time
import logging
import requests
import traceback
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from bs4 import BeautifulSoup
from flask_session import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_final_vue.log'),
        logging.StreamHandler()
    ]
)

# Create a logger for this module
logger = logging.getLogger('app_final_vue')

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'casestrainer_sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'casestrainer-secret-key')

# Ensure session directory exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
logger.info(f"Configured server-side session storage at {app.config['SESSION_FILE_DIR']}")

# Initialize server-side session
Session(app)

logger.info("Starting CaseStrainer application with Vue.js frontend")

# Register the citation API blueprint
from citation_api import citation_api_blueprint
app.register_blueprint(citation_api_blueprint, url_prefix='/api')
logger.info("Citation API registered with prefix /api")

# Register the enhanced validator blueprint
try:
    from enhanced_validator import enhanced_validator_blueprint
    app.register_blueprint(enhanced_validator_blueprint)
    logger.info("Enhanced Validator blueprint registered with the application")
except ImportError:
    logger.warning("Enhanced Validator blueprint not found, skipping registration")

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.resolve import resolve_citations
    EYECITE_AVAILABLE = True
    logger.info("Eyecite library loaded successfully for citation extraction")
except ImportError:
    EYECITE_AVAILABLE = False
    logger.warning("Eyecite library not available, falling back to standard extraction")

# Function to get or create a session ID
def get_or_create_session_id():
    """Get or create a unique session ID for the current user."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

# Function to initialize session data with sample citation data
def initialize_session_data():
    """Initialize the session data with sample citation data if it doesn't exist."""
    if 'user_citations' not in session:
        session['user_citations'] = []

# Function to extract text from a file
def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.pdf':
        # Extract text from PDF
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    elif ext in ['.txt', '.md', '.rst']:
        # Read text file directly
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext in ['.docx', '.doc']:
        # Extract text from Word document
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from Word document: {e}")
            return ""
    else:
        # For other file types, try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file as text: {e}")
            return ""

# CORS preflight response builder
def _build_cors_preflight_response():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# API endpoint for enhanced analyze
@app.route('/api/analyze', methods=['POST', 'OPTIONS'])
@app.route('/casestrainer/api/analyze', methods=['POST', 'OPTIONS'])
def enhanced_analyze():
    # Handle file upload, text input, or URL input
    # The function returns a JSON response with the analysis results
    
    # Log request details for debugging
    logger.info("Enhanced analyze request received")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request data: {request.data}")
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    # Get or create a session ID
    session_id = get_or_create_session_id()
    logger.info(f"Session ID: {session_id}")
    
    try:
        # Generate a unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        logger.info(f"Generated analysis ID: {analysis_id}")
        
        # Clear previous citation data in session
        session.pop('user_citations', None)
        logger.info("Cleared previous citation data in user session")
        
        # Initialize session data with sample citation data
        initialize_session_data()
        
        # Initialize document_text
        document_text = None
        file = None
        
        # First, check if this is a URL input request
        # Handle both application/json content type and raw JSON data
        if request.content_type and 'application/json' in request.content_type or request.data and request.data.strip().startswith(b'{'):
            try:
                # Try to get JSON data, force=True to handle cases where Content-Type is set but not recognized as is_json
                try:
                    data = request.get_json(force=True)
                except:
                    # If that fails, try to parse the raw data
                    data = json.loads(request.data)
                
                logger.info(f"JSON data received: {data}")
                if data and 'url' in data:
                    url = data['url']
                    logger.info(f"URL detected in JSON: {url}")
                    
                    # Forward the data to the direct URL analysis function
                    return direct_url_analyze(forwarded_data=data)
            except Exception as json_error:
                logger.error(f"Error parsing JSON: {str(json_error)}")
                # Continue with other input methods
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                logger.info(f"File uploaded: {file.filename}")
                
                # Save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', f"{analysis_id}_{filename}")
                os.makedirs('uploads', exist_ok=True)
                file.save(file_path)
                logger.info(f"File saved to {file_path}")
                
                # Extract text from file
                document_text = extract_text_from_file(file_path)
                logger.info(f"Extracted {len(document_text)} characters from file")
            else:
                error_msg = "No file selected"
                logger.error(error_msg)
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), 400
        
        # Handle text input
        elif 'text' in request.form:
            document_text = request.form['text']
            logger.info(f"Text input received: {len(document_text)} characters")
        
        # If no file or text provided, return an error
        if not document_text:
            error_msg = "No file or text provided"
            logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        
        # Extract citations from the document text
        citations = []
        
        # Use eyecite if available
        if EYECITE_AVAILABLE:
            try:
                # Extract citations using eyecite
                eyecite_citations = get_citations(document_text)
                logger.info(f"Found {len(eyecite_citations)} citations with eyecite")
                
                # Resolve citations
                resolved_citations = resolve_citations(eyecite_citations)
                
                # Convert to our format
                for citation in eyecite_citations:
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
                    citations.append(citation_info)
            except Exception as e:
                logger.error(f"Error extracting citations with eyecite: {e}")
                # Continue with standard extraction
        
        # If no citations found with eyecite, use standard extraction
        if not citations:
            # Simple regex pattern for citation extraction
            citation_pattern = r'\d+\s+[A-Za-z\.]+\s+\d+\s+\(\d{4}\)'
            found_citations = re.findall(citation_pattern, document_text)
            
            # Add found citations to the list
            for citation in found_citations:
                citation_info = {
                    'citation': citation,
                    'found': True,
                    'found_case_name': 'Unknown',
                    'source': 'Regex'
                }
                citations.append(citation_info)
            
            logger.info(f"Found {len(citations)} citations with regex")
        
        # Store citations in session
        session['user_citations'] = citations
        logger.info(f"Stored {len(citations)} citations in session")
        
        # Return the analysis results
        return jsonify({
            'status': 'success',
            'analysis_id': analysis_id,
            'citations_count': len(citations),
            'citations': citations
        })
    
    except Exception as e:
        logger.error(f"Error in enhanced_analyze: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to directly analyze a URL for citations
@app.route('/api/direct_url_analyze', methods=['POST', 'OPTIONS'])
def direct_url_analyze(forwarded_data=None):
    """Endpoint to directly analyze a URL for citations without storing in session.
    Can be called directly via the API or forwarded from enhanced_analyze."""
    # Log request details for debugging
    logger.info("Direct URL analysis request received")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Forwarded data: {forwarded_data}")
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        # Generate a unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        logger.info(f"Generated analysis ID: {analysis_id}")
        
        # Get URL from either forwarded data or request
        if forwarded_data and 'url' in forwarded_data:
            url = forwarded_data['url']
            logger.info(f"URL provided from forwarded data: {url}")
        else:
            # Parse the JSON data from the request
            try:
                data = request.get_json(force=True)
                if not data or 'url' not in data:
                    error_msg = "Missing URL in request data"
                    logger.error(error_msg)
                    return jsonify({
                        'status': 'error',
                        'message': error_msg
                    }), 400
                
                url = data['url']
                logger.info(f"URL provided from request: {url}")
            except Exception as json_error:
                error_msg = f"Error parsing JSON data: {str(json_error)}"
                logger.error(error_msg)
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
        
        # Fetch the URL content
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        # Check content type to handle different file types
        content_type = response.headers.get('Content-Type', '').lower()
        logger.info(f"Content type: {content_type}")
        
        # Extract text based on content type
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            # Handle PDF files
            logger.info("Detected PDF file, using direct PDF extraction")
            
            # Save PDF to temporary file
            import tempfile
            import PyPDF2
            
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                # Download the PDF in chunks to avoid memory issues
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            logger.info(f"PDF saved to temporary file: {temp_file_path}")
            
            try:
                # Extract text from PDF
                text = ""
                with open(temp_file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)
                    logger.info(f"PDF has {num_pages} pages")
                    
                    # Limit to first 20 pages for large PDFs
                    max_pages = min(num_pages, 20)
                    logger.info(f"Processing first {max_pages} pages")
                    
                    for page_num in range(max_pages):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                
                # Clean up the temporary file
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error extracting text from PDF: {e}")
                # Clean up the temporary file
                os.unlink(temp_file_path)
                raise
        else:
            # Handle HTML and other text-based content
            logger.info("Processing as HTML/text content")
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
        
        # Clean up the text (remove excessive whitespace)
        text = re.sub(r'\s+', ' ', text).strip()
        logger.info(f"Successfully extracted {len(text)} characters from URL")
        
        # Return the URL analysis results
        return jsonify({
            'status': 'success',
            'analysis_id': analysis_id,
            'url': url,
            'citations_count': 0,
            'citations': []  # In a real implementation, we would extract citations from the text
        })
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Error fetching URL: {str(e)}"
        }), 500
    except Exception as e:
        logger.error(f"Error in direct_url_analyze: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Serve the Vue.js frontend
@app.route('/')
@app.route('/index')
def index():
    """Serve the Vue.js frontend."""
    return send_from_directory('static/vue', 'index.html')

# Serve static files for the Vue.js frontend
@app.route('/<path:path>')
def static_files(path):
    """Serve static files for the Vue.js frontend."""
    return send_from_directory('static/vue', path)

# Redirect to the original interface
@app.route('/api/')
@app.route('/api/index')
def original_interface():
    """Redirect to the original interface."""
    return redirect('/casestrainer/')

# Create a PrefixMiddleware to handle the /casestrainer/ prefix
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return [b'Not Found']

# Apply the PrefixMiddleware if running in production
if os.environ.get('FLASK_ENV') == 'production':
    print("Initializing PrefixMiddleware with prefix: /casestrainer")
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/casestrainer')
    logger.info("PrefixMiddleware applied with prefix '/casestrainer'")

# Run the application
if __name__ == '__main__':
    # Check if index.html exists in the static/vue directory
    vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
    index_html_path = os.path.join(vue_dist_dir, 'index.html')
    
    if os.path.exists(index_html_path):
        print(f"Found existing index.html at {index_html_path}")
    else:
        # Create the directory if it doesn't exist
        os.makedirs(vue_dist_dir, exist_ok=True)
        
        # Create a placeholder index.html file
        with open(index_html_path, 'w') as f:
            f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CaseStrainer - Modern Legal Citation Verification</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .feature-icon {
            font-size: 2.5rem;
            color: #0d6efd;
            margin-bottom: 1rem;
        }
        .feature-card {
            transition: transform 0.3s;
            height: 100%;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .navbar-brand {
            font-weight: bold;
        }
        .hero-section {
            background-color: #f8f9fa;
            padding: 4rem 0;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/casestrainer/">CaseStrainer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/casestrainer/">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/casestrainer/api/">Original Interface</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <section class="hero-section">
        <div class="container text-center">
            <h1 class="display-4">CaseStrainer</h1>
            <p class="lead">Modern Legal Citation Verification</p>
            <div class="mt-4">
                <a href="/casestrainer/api/" class="btn btn-primary btn-lg">Launch Application</a>
            </div>
        </div>
    </section>

    <section class="container mb-5">
        <div class="row">
            <div class="col-md-4 mb-4">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">📊</div>
                        <h3>Citation Network Visualization</h3>
                        <p>Visualize relationships between citations and identify patterns of unconfirmed citations.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">🤖</div>
                        <h3>ML Classifier</h3>
                        <p>Machine learning model trained on our database of confirmed and unconfirmed citations.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">🔍</div>
                        <h3>Multi-Source Verification</h3>
                        <p>Verify citations against multiple authoritative sources for comprehensive validation.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <footer class="bg-light py-4">
        <div class="container text-center">
            <p>© 2025 CaseStrainer - University of Washington School of Law</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
            ''')
        print(f"Created placeholder index.html at {index_html_path}")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
