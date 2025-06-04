# Standard library imports
import argparse
import json
import logging
import os
import sqlite3
import sys
import threading
import time
import traceback
import socket
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Third-party imports
import requests
from bs4 import BeautifulSoup

# Add project root to Python path only once
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Third-party imports
from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
    session,
    redirect,
    url_for,
    send_file,
)
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor

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
    from config import (
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
    from vue_api_endpoints import vue_api
    from citation_utils import extract_citations_from_text, verify_citation

# Define allowed file extensions
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "rtf"}

# Convert set to list for compatibility with existing code
ALLOWED_EXTENSIONS_LIST = list(ALLOWED_EXTENSIONS)

# Configure logging first
try:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.propagate = False  # Prevent propagation to avoid duplicate logs
except Exception as e:
    # Fallback basic logging if configuration fails
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
    )
    logger = logging.getLogger(__name__)
    logger.warning(
        f"Failed to configure logging: {e}. Using basic logging configuration."
    )

# Global flag for enhanced validator
ENHANCED_VALIDATOR_AVAILABLE = False

# Import other modules lazily to avoid circular imports
# These will be imported inside the create_app function when needed
citation_api = None
register_enhanced_validator_func = None

# Initialize mail
mail = Mail()

# Helper functions and constants remain at module level

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

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    logger.info("Starting application creation")

    # Configure the Flask application
    app = Flask(
        __name__,
        static_folder=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../casestrainer-vue/dist"
        ),
        template_folder=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../casestrainer-vue/dist"
        ),
        static_url_path="",
    )

    logger.info("Flask application instance created")

    # Configure CORS with environment-based origins
    cors_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://localhost:5174,"
        "http://127.0.0.1:5174,http://127.0.0.1:5173,http://localhost:5000,http://127.0.0.1:5000",
    ).split(",")

    logger.info(f"Configuring CORS with origins: {cors_origins}")
    CORS(
        app,
        resources={
            r"/casestrainer/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "supports_credentials": True,
                "expose_headers": ["Content-Disposition"],
            }
        },
    )

    # Add CORS logging middleware
    @app.after_request
    def log_cors(response):
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get(
                "Access-Control-Allow-Origin"
            ),
            "Access-Control-Allow-Methods": response.headers.get(
                "Access-Control-Allow-Methods"
            ),
            "Access-Control-Allow-Headers": response.headers.get(
                "Access-Control-Allow-Headers"
            ),
        }
        logger.debug(f"CORS Headers: {cors_headers} for {request.path}")
        return response

    # Initialize Flask-Mail
    mail = Mail()

    # Load configuration from config.py
    from src.config import (
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

    # Configure mail settings
    app.config.update(
        MAIL_SERVER=MAIL_SERVER,
        MAIL_PORT=MAIL_PORT,
        MAIL_USE_TLS=MAIL_USE_TLS,
        MAIL_USE_SSL=MAIL_USE_SSL,
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
        MAIL_DEBUG=MAIL_DEBUG,
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS,
    )

    # Initialize mail with the app
    # Register the vue_api blueprint
    try:
        # Import the vue_api blueprint
        from src.vue_api_endpoints import vue_api

        # Check if the blueprint is already registered
        if "vue_api" not in app.blueprints:
            logger.info("Registering vue_api blueprint...")

            # Register the blueprint with the app with /api prefix
            app.register_blueprint(vue_api, url_prefix="/casestrainer/api")

            logger.info(
                "Successfully registered vue_api blueprint with URL prefix /casestrainer/api"
            )
        else:
            logger.info("vue_api blueprint already registered, skipping")

    except Exception as e:
        logger.error(f"Error registering vue_api blueprint: {e}")
        logger.error(traceback.format_exc())
        # Continue without the vue_api blueprint if there's an error
        pass

    # Register enhanced validator if available
    try:
        from src.enhanced_validator_production import register_enhanced_validator

        app = register_enhanced_validator(app)
        logger.info("Enhanced validator registered successfully")
        global ENHANCED_VALIDATOR_AVAILABLE
        ENHANCED_VALIDATOR_AVAILABLE = True
    except Exception as e:
        logger.warning(f"Could not register enhanced validator: {e}")
        ENHANCED_VALIDATOR_AVAILABLE = False

    # Health check endpoint
    @app.route("/casestrainer/api/health")
    def health_check():
        """Health check endpoint for monitoring and uptime checks."""
        try:
            return jsonify(
                {
                    "status": "ok",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "CaseStrainer API",
                    "version": "1.0.0",  # You might want to get this from a config file
                }
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Health check failed",
                        "error": str(e),
                    }
                ),
                500,
            )

    # Helper function to get the Vue.js dist directory path
    def get_vue_dist_path():
        """Get the path to the Vue.js distribution directory."""
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../casestrainer-vue/dist")
        )

    # Serve Vue.js frontend
    @app.route("/casestrainer/")
    @app.route("/casestrainer")
    def serve_vue_app():
        """Serve the main Vue.js application."""
        vue_dist_path = get_vue_dist_path()
        return send_from_directory(vue_dist_path, "index.html")

    # Serve static files for Vue.js
    @app.route("/js/<path:filename>")
    def serve_js(filename):
        """Serve JavaScript files from the Vue.js dist directory."""
        vue_dist_path = get_vue_dist_path()
        return send_from_directory(os.path.join(vue_dist_path, "js"), filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        """Serve CSS files from the Vue.js dist directory."""
        vue_dist_path = get_vue_dist_path()
        return send_from_directory(os.path.join(vue_dist_path, "css"), filename)

    @app.route("/img/<path:filename>")
    def serve_img(filename):
        """Serve image files from the Vue.js dist directory."""
        vue_dist_path = get_vue_dist_path()
        return send_from_directory(os.path.join(vue_dist_path, "img"), filename)

    # Catch-all route for client-side routing
    @app.route("/casestrainer/<path:path>")
    def serve_vue_path(path):
        """Catch-all route for Vue.js client-side routing."""
        vue_dist_path = get_vue_dist_path()
        # Try to serve the requested file if it exists
        file_path = os.path.join(vue_dist_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(vue_dist_path, path)
        # Otherwise, serve index.html and let Vue.js handle the routing
        return send_from_directory(vue_dist_path, "index.html")

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Resource not found",
                    "error": str(error),
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "error": "An unexpected error occurred",
                }
            ),
            500,
        )

    # Log successful app initialization
    logger.info("Application initialization completed successfully")

    return app


# Helper functions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_citations_from_file(text_or_filepath, logger=None):
    """Extract citations from a file or text using the appropriate method.

    Args:
        text_or_filepath: Either a file path or text content
        logger: Optional logger (for compatibility)
    """
    try:
        # Import the actual implementation
        from citation_utils import (
            extract_citations_from_text,
            extract_citations_from_file as extract_from_file,
        )

        # If it looks like a file path, use file extraction
        if isinstance(text_or_filepath, str) and (
            text_or_filepath.endswith((".pdf", ".doc", ".docx", ".txt", ".rtf"))
            or os.path.exists(text_or_filepath)
        ):
            return extract_from_file(text_or_filepath)
        else:
            # Otherwise treat it as text content
            return extract_citations_from_text(text_or_filepath)
    except ImportError as e:
        if logger:
            logger.error(f"Could not import citation extraction functions: {e}")
        return []


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


# Main execution block
if __name__ == "__main__":
    # Set up basic logging to console and file
    import logging
    from datetime import datetime

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Create a timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"app_startup_{timestamp}.log")

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger(__name__)

    try:
        # Log system information
        logger.info("=" * 80)
        logger.info(f"Starting CaseStrainer Application - {datetime.now()}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Working Directory: {os.getcwd()}")
        logger.info("=" * 80)

        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Run CaseStrainer with Vue.js frontend"
        )
        parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
        parser.add_argument(
            "--port", type=int, default=5000, help="Port to run the server on"
        )
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument(
            "--use-waitress",
            action="store_true",
            default=True,
            help="Use Waitress server",
        )
        args = parser.parse_args()

        logger.info(f"Command line arguments: {args}")
        logger.info("Creating Flask application...")

        # Create and configure the Flask app
        app = create_app()

        # Log registered blueprints
        logger.info("Registered Blueprints:")
        for name, bp in app.blueprints.items():
            logger.info(f"- {name}: {bp}")

        # Print startup information
        print("\n" + "=" * 80)
        print("Starting CaseStrainer application...")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Debug: {args.debug}")
        print(f"Log File: {log_file}")
        print(f"Health Check: http://{args.host}:{args.port}/casestrainer/api/health")
        print("=" * 80 + "\n")

        # Run the application
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
        print(f"Check the log file for details: {log_file}")
        sys.exit(1)


def get_wsgi_application():
    """WSGI application factory for production servers."""
    return create_app()


# WSGI server entry point for production servers
app = get_wsgi_application()
