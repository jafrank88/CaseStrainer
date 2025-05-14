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
from src.enhanced_validator_production import enhanced_validator_bp as enhanced_validator_production_bp, register_enhanced_validator
from src.citation_api import citation_api

# Helper functions and constants remain at module level
DATABASE_FILE = 'citations.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v4/opinions/'

# Load config from config.json with better error handling
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get('COURTLISTENER_API_KEY', '')
        if not DEFAULT_API_KEY:
            DEFAULT_API_KEY = config.get('courtlistener_api_key', '')  # Try alternate key name
        SECRET_KEY = config.get('SECRET_KEY', '')
        print(f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}...")
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded CourtListener API key from config.json: {DEFAULT_API_KEY[:5]}...")
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading config.json: {str(e)}. Using environment variables.")
    DEFAULT_API_KEY = os.environ.get('COURTLISTENER_API_KEY', '')
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    
# Fallback to config.json in current directory if API key is still empty
if not DEFAULT_API_KEY:
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            DEFAULT_API_KEY = config.get('COURTLISTENER_API_KEY', '')
            if not DEFAULT_API_KEY:
                DEFAULT_API_KEY = config.get('courtlistener_api_key', '')  # Try alternate key name
            print(f"Loaded CourtListener API key from current directory config.json: {DEFAULT_API_KEY[:5]}...")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config.json from current directory: {str(e)}")

# Verify API key is valid
if not DEFAULT_API_KEY:
    print("WARNING: No CourtListener API key found. Citation verification will not work properly.")
elif len(DEFAULT_API_KEY) < 10:
    print(f"WARNING: CourtListener API key appears invalid: {DEFAULT_API_KEY}")
else:
    print(f"CourtListener API key loaded successfully: {DEFAULT_API_KEY[:5]}...")

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

# Thread-local storage for API keys
thread_local = threading.local()

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, 
                static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
                template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    logger.info("CORS configured with Flask-CORS")

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

    # Set SECRET_KEY from environment variable first, then try config.json
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                app.config['SECRET_KEY'] = config.get('SECRET_KEY', '')
                if not app.config['SECRET_KEY']:
                    raise ValueError("SECRET_KEY not found in config.json")
                logger.info(f"Loaded SECRET_KEY from config.json: {app.config['SECRET_KEY'][:5]}...")
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error loading config.json: {e}")
            app.config['SECRET_KEY'] = 'dev-secret-key-please-change-in-production'
            logger.info(f"Using default SECRET_KEY: {app.config['SECRET_KEY'][:5]}...")
    else:
        logger.info(f"Using SECRET_KEY from environment: {app.config['SECRET_KEY'][:5]}...")

    # Session configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    if not os.path.exists(app.config['SESSION_FILE_DIR']):
        os.makedirs(app.config['SESSION_FILE_DIR'])
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Initialize Flask-Session BEFORE any routes
    Session(app)
    logger.info("Flask-Session initialized with filesystem storage")

    # URL prefix configuration
    app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/casestrainer')
    logger.info(f"Using APPLICATION_ROOT: {app.config['APPLICATION_ROOT']}")

    # Configure for reverse proxy
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_proto=1,
        x_host=1,
        x_prefix=1,
        x_for=1,
        x_port=1
    )
    logger.info("ProxyFix middleware configured")

    # Create thread pool for handling concurrent requests
    thread_pool = ThreadPoolExecutor(max_workers=10)

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

    @app.before_request
    def before_request():
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            session.permanent = True
            logger.info(f"Created new session for user: {session['user_id']}")

    # Serve Vue.js static files
    @app.route('/')
    def redirect_to_enhanced_validator():
        return redirect('/casestrainer/')

    @app.route('/casestrainer/')
    def serve_vue_index():
        vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
        logger.info(f"Serving Vue index from: {vue_dist_dir}")
        response = send_from_directory(vue_dist_dir, 'index.html')
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/casestrainer/<path:path>')
    def serve_vue_assets(path):
        vue_dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'vue')
        response = send_from_directory(vue_dist_dir, path)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

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
        """API endpoint for validating citations."""
        try:
            # Get the request data
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({'error': 'No text provided'}), 400

            # Extract citations from the text (now returns list of dicts)
            extracted_citations = extract_citations_from_text(data['text'])

            # Verify each citation using the citation_text field
            results = []
            for citation in extracted_citations:
                verification = verify_citation(citation['citation_text'])
                # Combine extraction metadata and verification result
                results.append({
                    'extraction': citation,
                    'verification': verification
                })

            return jsonify({
                'citations': results,
                'total': len(results)
            })
        except Exception as e:
            logger.error(f"Error in validate_citations: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500

    @app.after_request
    def after_request(response):
        """Clean up after each request."""
        # Clean up thread-local storage
        if hasattr(thread_local, 'data'):
            del thread_local.data
        return response

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        logger.error(f"Server error: {str(error)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

    return app

# Create the Flask app instance
app = create_app()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_citation(citation):
    """Verify a citation using the robust CitationVerifier logic with improved error handling."""
    try:
        # Import with better error handling
        try:
            from src.citation_verification import CitationVerifier
            logger.info(f"Successfully imported CitationVerifier from src.citation_verification")
        except ImportError as import_err:
            # Try relative import if the first one fails
            try:
                from citation_verification import CitationVerifier
                logger.info(f"Successfully imported CitationVerifier from citation_verification (relative import)")
            except ImportError:
                logger.error(f"Failed to import CitationVerifier: {str(import_err)}")
                raise
        
        # Get API key from thread_local or use default
        api_key = getattr(thread_local, 'api_key', DEFAULT_API_KEY)
        
        # Log API key information (first 5 chars only for security)
        if api_key:
            logger.info(f"Using API key for verification: {api_key[:5]}... (length: {len(api_key)})")
        else:
            logger.warning("No API key available for citation verification")
            print("WARNING: No API key available for citation verification")
        
        # Create verifier and verify citation
        verifier = CitationVerifier(api_key=api_key)
        logger.info(f"Verifying citation: {citation}")
        result = verifier.verify_citation(citation)
        logger.info(f"Verification result: {result}")
        
        # Return formatted result
        return {
            'citation': citation,
            'verified': result.get('found', False),
            'source': result.get('source'),
            'case_name': result.get('case_name'),
            'details': result.get('details'),
            'url': result.get('url'),
            'error': result.get('error')
        }
    except Exception as e:
        logger.error(f"Error verifying citation: {e}")
        traceback.print_exc()  # Print full stack trace for debugging
        return {
            'citation': citation,
            'verified': False,
            'source': 'CourtListener',
            'case_name': None,
            'details': None,
            'error': str(e)
        }

def extract_citations_from_file(filepath):
    """Extract citations from a file and return full metadata."""
    try:
        # Read file content based on file type
        if filepath.endswith('.pdf'):
            import PyPDF2
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
        elif filepath.endswith(('.doc', '.docx')):
            import docx
            doc = docx.Document(filepath)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        return extract_citations_from_text(text)
    except Exception as e:
        print(f"Error extracting citations from file: {e}")
        return []

def extract_citations_from_text(text):
    """Extract citations from text using eyecite and return full metadata."""
    try:
        from eyecite import get_citations
        from eyecite.tokenizers import AhocorasickTokenizer
        
        # Use AhocorasickTokenizer
        tokenizer = None
        try:
            tokenizer = AhocorasickTokenizer()
        except Exception:
            tokenizer = None
        
        citations = get_citations(text, tokenizer=tokenizer) if tokenizer else get_citations(text)
        
        citation_dicts = []
        for citation in citations:
            citation_dicts.append({
                'citation_text': citation.matched_text(),
                'corrected_citation': citation.corrected_citation() if hasattr(citation, 'corrected_citation') else None,
                'citation_type': type(citation).__name__,
                'metadata': {
                    'reporter': getattr(citation, 'reporter', None),
                    'volume': getattr(citation, 'volume', None),
                    'page': getattr(citation, 'page', None),
                    'year': getattr(citation, 'year', None),
                    'court': getattr(citation, 'court', None)
                }
            })
        return citation_dicts
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
