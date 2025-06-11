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
    )
    from src.vue_api_endpoints import vue_api
    from src.citation_utils import extract_citations_from_text, verify_citation
except ImportError:
    # Fallback for direct execution
    from config import configure_logging

# Define allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "rtf"}
ALLOWED_EXTENSIONS_LIST = list(ALLOWED_EXTENSIONS)

# Global flag for enhanced validator
ENHANCED_VALIDATOR_AVAILABLE = False

# Import other modules lazily to avoid circular imports
citation_api = None
register_enhanced_validator_func = None

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

# Configure logging
def setup_logging():
    """Configure logging for the application."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path(project_root) / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create a timestamp for the log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"app_{timestamp}.log"
        
        # Configure logging
        configure_logging()
        logger = logging.getLogger(__name__)
        logger.propagate = False  # Prevent propagation to avoid duplicate logs
        
        # Add file handler if not already added
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            logger.addHandler(file_handler)
        
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

# Initialize logger
logger = setup_logging()

def create_app():
    """Create and configure the Flask application."""
    logger.info("Starting application creation")

    # Configure the Flask application
    app = Flask(
        __name__,
        static_folder=str(Path(project_root) / "casestrainer-vue-new" / "dist"),
        template_folder=str(Path(project_root) / "casestrainer-vue-new" / "dist"),
        static_url_path="",
    )

    # Set environment based on FLASK_ENV
    app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
    app.config['DEBUG'] = app.config['ENV'] == 'development'
    
    # Register blueprints with consistent prefixes
    app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
    
    logger.info("Registered API blueprint")
    logger.info(f"Application initialized in {app.config['ENV']} mode")

    # Configure CORS
    is_production = app.config['ENV'] == 'production'
    default_origins = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://wolf.law.uw.edu"
    ]
    
    cors_origins = (
        ["https://wolf.law.uw.edu"] if is_production
        else os.getenv("CORS_ORIGINS", ",".join(default_origins)).split(",")
    )
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    
    logger.info(f"Configuring CORS with origins: {cors_origins}")
    
    CORS(
        app,
        resources={r"/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "X-Requested-With", 
                "x-requested-with",
                "Origin", 
                "Accept"
            ],
            "supports_credentials": True,
            "expose_headers": ["Content-Disposition", "Content-Type"],
            "max_age": 86400
        }},
        supports_credentials=True,
        automatic_options=True
    )

    # Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Handle CORS headers
        if 'Origin' in request.headers:
            origin = request.headers['Origin']
            if origin in cors_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response

    # Add health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        try:
            return jsonify({
                'status': 'ok',
                'environment': app.config['ENV'],
                'version': '1.0.0',
                'service': 'CaseStrainer API',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'service': 'CaseStrainer API',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500

    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return jsonify({
            "status": "error",
            "message": "Not found",
            "error": str(error)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error": "An unexpected error occurred"
        }), 500

    # Add static file routes
    @app.route("/")
    def root_redirect():
        """Redirect root to the Vue app."""
        return redirect("/casestrainer/")

    @app.route("/casestrainer/")
    @app.route("/casestrainer")
    def serve_vue_app():
        """Serve the Vue.js application."""
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        """Serve JavaScript files."""
        return send_from_directory(Path(app.static_folder) / "js", filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        """Serve CSS files."""
        return send_from_directory(Path(app.static_folder) / "css", filename)

    @app.route("/img/<path:filename>")
    def serve_img(filename):
        """Serve image files."""
        return send_from_directory(Path(app.static_folder) / "img", filename)

    @app.route("/casestrainer/<path:path>")
    def serve_vue_path(path):
        """Serve Vue.js application paths."""
        try:
            return send_from_directory(app.static_folder, path)
        except Exception as e:
            logger.error(f"Error serving path {path}: {e}")
            return send_from_directory(app.static_folder, "index.html")

    logger.info("Application initialization completed successfully")
    return app

# Create the Flask application
app = create_app()

# WSGI application for production servers
def get_wsgi_application():
    """WSGI server entry point for production servers."""
    return app

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
                serve(app, host=args.host, port=args.port, threads=10)
            except ImportError:
                logger.warning("Waitress not installed. Using Flask dev server.")
                app.run(host=args.host, port=args.port, debug=args.debug)
        else:
            logger.info("Starting with Flask development server")
            app.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.critical("Fatal error in main:", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
