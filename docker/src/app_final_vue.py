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
from werkzeug.middleware.proxy_fix import ProxyFix
from concurrent.futures import ThreadPoolExecutor
import threading
from flask_cors import CORS
from datetime import timedelta
from enhanced_validator_production import enhanced_validator_bp as enhanced_validator_production_bp, register_enhanced_validator
from citation_api import citation_api

# Helper functions and constants remain at module level
DATABASE_FILE = 'citations.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v4/opinions/'

# Load API key from config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get('COURTLISTENER_API_KEY', '')
except (FileNotFoundError, json.JSONDecodeError):
    DEFAULT_API_KEY = os.environ.get('COURTLISTENER_API_KEY', '')

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state to track processing progress
processing_state = {
    'total_citations': 0,
    'processed_citations': 0,
    'is_complete': False
}

# Dictionary to store analysis results
analysis_results = {}

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, 
                static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
                template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/casestrainer.log'),
            logging.StreamHandler()
        ]
    )
    logger.info(f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}...")

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-please-change-in-production')
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'doc', 'docx', 'rtf', 'odt', 'html', 'htm'}
    
    # Set application root from environment variable
    app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/casestrainer')

    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # Configure for reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)

    # Initialize Flask-Session
    Session(app)

    # Create thread pool for handling concurrent requests
    thread_pool = ThreadPoolExecutor(max_workers=10)

    # Thread-local storage for user-specific data
    thread_local = threading.local()

    # Import eyecite for citation extraction
    try:
        from eyecite import get_citations
        from eyecite.tokenizers import AhocorasickTokenizer
        try:
            tokenizer = AhocorasickTokenizer()
            EYECITE_AVAILABLE = True
            logger.info("Eyecite library and AhocorasickTokenizer loaded successfully for citation extraction")
        except ImportError as e:
            EYECITE_AVAILABLE = False
            tokenizer = None
            logger.warning(f"Eyecite not installed: {str(e)}. Using regex patterns for citation extraction.")
    except ImportError as e:
        EYECITE_AVAILABLE = False
        tokenizer = None
        logger.warning(f"Eyecite not installed: {str(e)}. Using regex patterns for citation extraction.")

    # Register the citation API blueprint with proper prefix
    app.register_blueprint(citation_api, url_prefix='/api')
    logger.info("Citation API registered with prefix /api")

    # Register the Enhanced Validator blueprint
    register_enhanced_validator(app)
    logger.info("Enhanced Validator blueprint registered with the application")

    # Configure logging for the app
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)

    # Serve Vue.js static files
    @app.route('/')
    def redirect_to_enhanced_validator():
        return redirect('/casestrainer/')

    @app.route('/casestrainer/')
    def serve_vue_index():
        vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
        return send_from_directory(vue_dist_dir, 'index.html')

    @app.route('/casestrainer/<path:path>')
    def serve_vue_static(path):
        vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
        return send_from_directory(vue_dist_dir, path)

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

    @app.route('/original')
    @app.route('/casestrainer/original')
    def redirect_to_api():
        return redirect('/api/')

    @app.route('/original/')
    @app.route('/casestrainer/original/')
    def redirect_to_api_slash():
        return redirect('/api/')

    @app.route('/vue-enhanced-validator')
    @app.route('/casestrainer/vue-enhanced-validator')
    def redirect_from_vue_to_enhanced_validator():
        return redirect('/')

    @app.route('/enhanced-validator-link')
    @app.route('/casestrainer/enhanced-validator-link')
    def serve_enhanced_validator_link():
        return send_from_directory('static', 'enhanced_validator_link.html')

    @app.route('/citation_verification_results.json')
    @app.route('/casestrainer/citation_verification_results.json')
    def serve_citation_verification_results():
        return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'citation_verification_results.json')

    @app.route('/database_verification_results.json')
    @app.route('/casestrainer/database_verification_results.json')
    def serve_database_verification_results():
        return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'database_verification_results.json')

    @app.route('/api/confirmed_with_multitool_data')
    @app.route('/api/confirmed-with-multitool-data')
    @app.route('/casestrainer/api/confirmed_with_multitool_data')
    def confirmed_with_multitool_data():
        """API endpoint for citations confirmed with multi-tool verification."""
        try:
            # Get citations from database
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM citations WHERE verified = 1')
            citations = cursor.fetchall()
            conn.close()

            # Format citations for response
            formatted_citations = []
            for citation in citations:
                formatted_citations.append({
                    'citation': citation[1],
                    'found': True,
                    'found_case_name': citation[2],
                    'confidence': citation[3],
                    'source': citation[4],
                    'url': citation[5],
                    'explanation': citation[6]
                })

            return jsonify({
                'citations': formatted_citations,
                'total': len(formatted_citations)
            })
        except Exception as e:
            logger.error(f"Error in confirmed_with_multitool_data: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/processing_progress', methods=['GET'])
    def processing_progress():
        """Get the current processing progress."""
        return jsonify(processing_state)

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
                    upload_folder = os.path.join(app.root_path, 'uploads')
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
            logger.error(f"Error in validate_citations: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500

    # Add middleware to handle user sessions
    @app.before_request
    def before_request():
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        thread_local.user_id = session['user_id']

    # Add cleanup middleware
    @app.after_request
    def after_request(response):
        # Clean up thread-local storage
        if hasattr(thread_local, 'user_id'):
            del thread_local.user_id
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_citation(citation):
    """Verify a citation using CourtListener API or direct validation for U.S. Code."""
    try:
        # Get API key from thread-local storage or config
        api_key = getattr(thread_local, 'api_key', DEFAULT_API_KEY)
        logger.info(f"[verify_citation] Using API key: {api_key[:6]}... (length: {len(api_key)})")
        
        # Check if this is a U.S. Code citation
        usc_pattern = r'(\d+)\s+U\.\s*S\.\s*C\.\s*§\s*(\d+)'
        usc_match = re.match(usc_pattern, citation, re.IGNORECASE)
        
        if usc_match:
            title = usc_match.group(1)
            section = usc_match.group(2)
            logger.info(f"Found U.S. Code citation: Title {title}, Section {section}")
            return {
                'citation': citation,
                'verified': True,
                'source': 'U.S. Code',
                'case_name': f"U.S. Code Title {title}, Section {section}",
                'details': {
                    'title': title,
                    'section': section,
                    'url': f"https://www.law.cornell.edu/uscode/text/{title}/{section}"
                }
            }
        
        # For case citations, use CourtListener API
        from urllib.parse import quote
        
        # Encode the citation for the URL
        encoded_citation = quote(citation)
        url = f"https://www.courtlistener.com/api/rest/v4/opinions/?cite={encoded_citation}"
        logger.info(f"[verify_citation] Requesting URL: {url}")
        
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"[verify_citation] Headers: {headers}")
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"[verify_citation] Response status: {response.status_code}")
        logger.info(f"[verify_citation] Response body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"CourtListener API response: {data}")
            
            if data.get('count', 0) > 0:
                result = data['results'][0]
                logger.info(f"Citation verified: {citation}")
                return {
                    'citation': citation,
                    'verified': True,
                    'source': 'CourtListener',
                    'case_name': result.get('case_name', 'Unknown Case'),
                    'details': {
                        'court': result.get('court', 'Unknown Court'),
                        'date_filed': result.get('date_filed', 'Unknown Date'),
                        'docket_number': result.get('docket_number', 'Unknown Docket'),
                        'url': f"https://www.courtlistener.com{result.get('absolute_url', '')}"
                    }
                }
        
        # If not found in CourtListener, try other sources
        logger.info(f"Citation not found in CourtListener: {citation}")
        return {
            'citation': citation,
            'verified': False,
            'source': 'CourtListener',
            'case_name': None,
            'details': None,
            'error': 'Citation not found in CourtListener database'
        }
    except Exception as e:
        logger.error(f"Error verifying citation: {e}")
        return {
            'citation': citation,
            'verified': False,
            'source': 'CourtListener',
            'case_name': None,
            'details': None,
            'error': str(e)
        }

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
        
        # Use AhocorasickTokenizer
        if EYECITE_AVAILABLE and tokenizer:
            logger.info("Using AhocorasickTokenizer for citation extraction")
            try:
                citations = get_citations(text, tokenizer=tokenizer)
                if citations is None:
                    raise ValueError("AhocorasickTokenizer returned None")
            except Exception as e:
                logger.warning(f"Error using AhocorasickTokenizer: {e}. Falling back to regex patterns.")
                citations = None
        else:
            logger.info("Using regex patterns for citation extraction")
            citations = None
        
        # Clean and normalize citations
        cleaned_citations = []
        
        # First try eyecite if available
        if citations:
            logger.info(f"Processing {len(citations)} citations from eyecite")
            for citation in citations:
                # Get the matched text
                citation_text = citation.matched_text()
                
                # Skip U.S. Code citations
                if re.search(r'\d+\s+U\.\s*S\.\s*C\.\s*§', citation_text, re.IGNORECASE):
                    logger.info(f"Skipping U.S. Code citation: {citation_text}")
                    continue
                
                # Clean up the citation
                citation_text = re.sub(r'\s+', ' ', citation_text)  # Normalize whitespace
                citation_text = re.sub(r'([0-9])\s+([A-Z])', r'\1 \2', citation_text)  # Fix spacing in citations
                citation_text = re.sub(r'([A-Z])\.\s+([A-Z])', r'\1. \2', citation_text)  # Fix spacing in abbreviations
                
                # Add to list if not empty
                if citation_text.strip():
                    cleaned_citations.append(citation_text)
                    logger.info(f"Extracted citation with eyecite: {citation_text}")
        
        # If no citations found with eyecite, try regex patterns
        if not cleaned_citations:
            logger.info("No citations found with eyecite, trying regex patterns")
            
            # Pattern for U.S. Supreme Court citations with complex case names and multiple page numbers
            scotus_patterns = [
                # Pattern for full citations with case names and multiple page numbers
                r'(?:[A-Z][A-Za-z0-9\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z0-9\s\.,&\'\"\(\)]+,\s+)?(\d+\s+U\.\s*S\.\s*\d+(?:,\s*\d+)*)',
                
                # Pattern for citations with multiple page numbers but no case name
                r'(\d+\s+U\.\s*S\.\s*\d+(?:,\s*\d+)*)',
                
                # Pattern for simple citations
                r'(\d+\s+U\.\s*S\.\s*\d+)'
            ]
            
            # Find all matches
            for pattern in scotus_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    citation = match.group().strip()
                    # Clean up the citation
                    citation = re.sub(r'\s+', ' ', citation)  # Normalize whitespace
                    citation = re.sub(r'([0-9])\s+([A-Z])', r'\1 \2', citation)  # Fix spacing
                    citation = re.sub(r'([A-Z])\.\s+([A-Z])', r'\1. \2', citation)  # Fix abbreviations
                    
                    if citation not in cleaned_citations:
                        cleaned_citations.append(citation)
                        logger.info(f"Extracted citation with regex: {citation}")
        
        logger.info(f"Extracted {len(cleaned_citations)} citations from text")
        return cleaned_citations
    except Exception as e:
        logger.error(f"Error extracting citations from text: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return []

def initialize_session_data():
    """Initialize session with sample citation data if it's empty."""
    from flask import session
    if 'user_citations' not in session or not session['user_citations']:
        logger.info("Initializing session with sample citation data")
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
        logger.error(f"Error getting IP address: {e}")
        return "unknown"

if __name__ == '__main__':
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run CaseStrainer with Vue.js frontend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--use-waitress', action='store_true', help='Use Waitress WSGI server (production mode)')
    parser.add_argument('--env', choices=['development', 'production'], default='development', help='Environment to run in')
    parser.add_argument('--threads', type=int, default=10, help='Number of threads for the server')
    args = parser.parse_args()
    
    # Set environment
    os.environ['FLASK_ENV'] = args.env
    
    # Check if we should run with Waitress (production) or Flask's dev server
    use_waitress = args.use_waitress or os.environ.get('USE_WAITRESS', 'True').lower() in ('true', '1', 't')
    
    logger.info(f"Using Waitress: {use_waitress}")
    
    # Create the Flask app
    app = create_app()

    if use_waitress:
        try:
            from waitress import serve
            logger.info("Starting with Waitress WSGI server (production mode)")
            
            # Now 'app' is defined and can be used
            serve(app, host=args.host, port=args.port, threads=args.threads)
        except ImportError:
            logger.warning("Waitress not installed. Installing now...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "waitress"])
                logger.info("Waitress installed. Please restart the application.")
            except Exception as e:
                logger.error(f"Failed to install Waitress: {e}")
    else:
        logger.info("Starting with Flask development server")
        app.run(debug=args.debug, host=args.host, port=args.port)
