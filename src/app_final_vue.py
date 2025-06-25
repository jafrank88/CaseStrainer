# Standard library imports
import argparse
import logging
import os
import sys
import threading
import traceback
import socket
from datetime import datetime, timezone
from pathlib import Path

# Add project root to Python path only once
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging first, before any other imports
def setup_logging():
    """Configure logging for the application using centralized configuration."""
    try:
        # Import and use the centralized logging configuration
        from src.config import configure_logging
        configure_logging()
        
        # Get logger for this module
        logger = logging.getLogger(__name__)
        
        logger.info("=== Logging Configuration ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        return logger
        
    except Exception as e:
        # Fallback basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to configure logging: {e}. Using basic logging configuration.")
        return logger

# Initialize logger before any other imports
logger = setup_logging()

# Third-party imports
from flask import Flask, request, jsonify, send_from_directory, redirect, Blueprint, current_app, make_response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException, InternalServerError
from flask_mail import Mail

# Local application imports
try:
    from src.config import (
        configure_logging,
        MAIL_SERVER,
        MAIL_PORT,
        MAIL_USE_TLS,
        MAIL_USE_SSL,
        MAIL_USERNAME,
        MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER,
        MAIL_DEBUG,
        UPLOAD_FOLDER,
        ALLOWED_EXTENSIONS,
        MAX_CONTENT_LENGTH,
    )
    logger.info("Successfully imported config module")
except ImportError as e:
    logger.error(f"Failed to import config module: {e}")
    # Fallback for direct execution
    from config import configure_logging

# Import vue_api after logging is configured
try:
    from src.vue_api_endpoints import vue_api
    logger.info("Successfully imported vue_api blueprint")
except ImportError as e:
    logger.error(f"Failed to import vue_api blueprint: {e}")
    raise

try:
    from src.citation_utils import extract_all_citations, verify_citation
    logger.info("Successfully imported citation utilities")
except ImportError as e:
    logger.error(f"Failed to import citation utilities: {e}")
    raise

# Global flag for enhanced validator - now always true since it's integrated into vue_api
ENHANCED_VALIDATOR_AVAILABLE = True

# Import other modules lazily to avoid circular imports
citation_api = None

# Initialize mail
mail = Mail()

# Global state to track processing progress
processing_state = {
    "total_citations": 0,
    "processed_citations": 0,
    "is_complete": False,
}

# Dictionary to store analysis results
analysis_results = {}

# Thread-local storage for API keys
thread_local = threading.local()

# Singleton instance of the Flask application
_app_instance = None

print("Python executable:", sys.executable)

def setup_secure_upload_directory():
    """
    Set up secure upload directory with proper permissions and security measures.
    """
    try:
        # Create upload directory if it doesn't exist
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, mode=0o755, exist_ok=True)
            logger.info(f"Created upload directory: {UPLOAD_FOLDER}")
        
        # Create subdirectories for better organization
        subdirs = ['temp', 'processed', 'rejected']
        for subdir in subdirs:
            subdir_path = os.path.join(UPLOAD_FOLDER, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path, mode=0o755, exist_ok=True)
                logger.info(f"Created upload subdirectory: {subdir_path}")
        
        # Create .htaccess file to prevent direct access (if using Apache)
        htaccess_path = os.path.join(UPLOAD_FOLDER, '.htaccess')
        if not os.path.exists(htaccess_path):
            with open(htaccess_path, 'w') as f:
                f.write("Order deny,allow\n")
                f.write("Deny from all\n")
            logger.info(f"Created .htaccess file: {htaccess_path}")
        
        # Create index.html to prevent directory listing
        index_path = os.path.join(UPLOAD_FOLDER, 'index.html')
        if not os.path.exists(index_path):
            with open(index_path, 'w') as f:
                f.write("<!DOCTYPE html>\n<html><head><title>403 Forbidden</title></head>")
                f.write("<body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>")
            logger.info(f"Created index.html file: {index_path}")
        
        # Test write permissions
        test_file = os.path.join(UPLOAD_FOLDER, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('Test write permission')
            os.remove(test_file)
            logger.info("Upload directory write permissions verified")
        except Exception as e:
            logger.error(f"Upload directory write permission test failed: {e}")
            raise
        
        logger.info(f"Upload directory setup completed: {UPLOAD_FOLDER}")
        logger.info(f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}")
        logger.info(f"Max file size: {MAX_CONTENT_LENGTH // (1024*1024)}MB")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup upload directory: {e}")
        return False

def create_app():
    """Create and configure the Flask application."""
    global _app_instance
    
    # Return existing instance if it exists
    if _app_instance is not None:
        logger.info("Returning existing Flask application instance")
        return _app_instance
        
    logger.info("Starting application creation")

    # Configure the Flask application
    app = Flask(
        __name__,
        static_folder=str(Path(project_root) / "casestrainer-vue-new" / "dist"),
        template_folder=str(Path(project_root) / "casestrainer-vue-new" / "dist"),
        static_url_path="/casestrainer"
    )

    # Set environment based on FLASK_ENV
    app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
    app.config['DEBUG'] = app.config['ENV'] == 'development'
    
    # Register blueprints with consistent prefixes
    app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
    
    # Configure CORS
    cors_origins = os.getenv('CORS_ORIGINS', 'https://wolf.law.uw.edu,http://localhost:5000,http://localhost:8080').split(',')
    CORS(app, 
         resources={r"/*": {"origins": cors_origins}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         expose_headers=["Content-Disposition", "Content-Type"])

    # Set up secure upload directory
    if not setup_secure_upload_directory():
        logger.error("Failed to setup secure upload directory")
        raise RuntimeError("Upload directory setup failed")

    # Initialize the global database manager
    db_manager = get_database_manager()
    logger.info("DatabaseManager initialized and ready.")

    # Add robust SPA fallback for Vue.js frontend with enhanced security
    @app.route('/casestrainer/', defaults={'path': ''})
    @app.route('/casestrainer/<path:path>')
    def serve_vue_app(path):
        vue_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'casestrainer-vue-new', 'dist'))
        
        # Security: Prevent directory traversal attacks
        if '..' in path or path.startswith('/'):
            logger.warning(f"Potential directory traversal attempt: {path}")
            return make_response("Forbidden", 403)
        
        # Security: Validate file path
        try:
            file_path = os.path.join(vue_dist_dir, path)
            # Ensure the resolved path is within the vue_dist_dir
            if not os.path.abspath(file_path).startswith(vue_dist_dir):
                logger.warning(f"Path traversal attempt blocked: {path}")
                return make_response("Forbidden", 403)
        except Exception as e:
            logger.error(f"Error resolving file path: {e}")
            return make_response("Bad Request", 400)
        
        # Serve static files with proper headers
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            response = send_from_directory(vue_dist_dir, path)
            
            # Set appropriate caching headers based on file type
            if path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot')):
                # Static assets: cache for 1 year
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            elif path.endswith('.html'):
                # HTML files: no cache to ensure fresh content
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            else:
                # Other files: cache for 1 hour
                response.headers['Cache-Control'] = 'public, max-age=3600'
            
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Set proper MIME types for common file extensions
            mime_types = {
                '.js': 'application/javascript',
                '.css': 'text/css',
                '.html': 'text/html',
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.woff': 'font/woff',
                '.woff2': 'font/woff2',
                '.ttf': 'font/ttf',
                '.eot': 'application/vnd.ms-fontobject'
            }
            
            file_ext = os.path.splitext(path)[1].lower()
            if file_ext in mime_types:
                response.headers['Content-Type'] = mime_types[file_ext]
            
            return response
        else:
            # Serve index.html for unknown routes (SPA fallback)
            response = send_from_directory(vue_dist_dir, 'index.html')
            
            # Security headers for HTML responses
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            
            # No cache for HTML files
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response

    # Add a database health/stats endpoint
    @app.route('/casestrainer/api/db_stats', methods=['GET'])
    def db_stats():
        stats = db_manager.get_database_stats()
        return jsonify(stats)

    # Print all registered routes for debugging
    for rule in app.url_map.iter_rules():
        print(f"Registered route: {rule}")

    # Add a direct /test route for debugging
    @app.route('/test')
    def test():
        return 'test route is working!'

    # Store the instance
    _app_instance = app
    logger.info("Application initialization completed successfully")
    return app

# WSGI application for production servers
def get_wsgi_application():
    """WSGI server entry point for production servers."""
    return create_app()

# Main execution block
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run CaseStrainer with Vue.js frontend")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5000")), help="Port to run the server on")
    parser.add_argument("--debug", action="store_true", default=os.getenv("FLASK_DEBUG", "").lower() == "true", help="Enable debug mode")
    parser.add_argument("--use-waitress", action="store_true", default=True, help="Use Waitress server")
    args = parser.parse_args()

    # Log startup information
    logger.info("=" * 80)
    logger.info(f"Starting CaseStrainer Application - {datetime.now()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Debug: {args.debug}")
    logger.info(f"Using Waitress: {args.use_waitress}")
    logger.info("=" * 80)

    try:
        if args.use_waitress:
            try:
                from waitress import serve
                logger.info("Starting with Waitress WSGI server")
                serve(create_app(), host=args.host, port=args.port, threads=10)
            except ImportError:
                logger.warning("Waitress not installed. Using Flask dev server.")
                create_app().run(host=args.host, port=args.port, debug=args.debug)
        else:
            logger.info("Starting with Flask development server")
            create_app().run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.critical("Fatal error in main:", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
