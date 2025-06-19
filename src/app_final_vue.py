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
    """Configure logging for the application."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path(project_root) / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create a timestamp for the log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"app_{timestamp}.log"
        
        # Configure basic logging first
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file, encoding="utf-8")
            ]
        )
        
        # Get logger for this module
        logger = logging.getLogger(__name__)
        logger.propagate = False  # Prevent propagation to avoid duplicate logs
        
        logger.info("=== Logging Configuration ===")
        logger.info(f"Log file: {log_file}")
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

# Define allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "rtf"}
ALLOWED_EXTENSIONS_LIST = list(ALLOWED_EXTENSIONS)

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

    # Add robust SPA fallback for Vue.js frontend
    @app.route('/casestrainer/', defaults={'path': ''})
    @app.route('/casestrainer/<path:path>')
    def serve_vue_app(path):
        vue_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'casestrainer-vue-new', 'dist'))
        file_path = os.path.join(vue_dist_dir, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(vue_dist_dir, path)
        else:
            # Serve index.html for unknown routes (SPA fallback)
            return send_from_directory(vue_dist_dir, 'index.html')

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
