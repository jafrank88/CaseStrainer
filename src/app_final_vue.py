"""
Enhanced CaseStrainer Flask Application
Improved version with better error handling, performance, and maintainability
"""

import argparse
import atexit
import logging
import os
import sys
import threading
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask

# Ensure project root is in path
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.case_name_extraction_core import extract_case_name_triple, get_canonical_case_name_with_date

# Enhanced citation verification function

def verify_citation_with_extraction(citation_text: str, document_text: str = "", api_key: str = None) -> dict:
    """
    Enhanced citation verification that includes both extraction and database verification.
    This should be called in your main verification workflow.
    """
    import logging
    logger = logging.getLogger("citation_verification")
    result = {
        "citation": citation_text,
        "canonical_citation": citation_text,
        "primary_citation": citation_text,
        "extracted_case_name": "N/A",
        "extracted_date": "",
        "case_name": "N/A",
        "canonical_name": "N/A",
        "canonical_date": "",
        "verified": "false",
        "confidence": 0.0,
        "source": "Unknown",
        "url": None,
        "error": None,
        "explanation": None
    }
    try:
        if document_text and document_text.strip():
            logger.info(f"Extracting case info from document for citation: {citation_text}")
            extraction_result = extract_case_name_triple(
                text=document_text,
                citation=citation_text,
                api_key=api_key,
                context_window=200
            )
            if extraction_result:
                result["extracted_case_name"] = extraction_result.get("extracted_name", "N/A")
                result["extracted_date"] = extraction_result.get("extracted_date", "")
                result["case_name"] = extraction_result.get("case_name", "N/A")
                result["canonical_name"] = extraction_result.get("canonical_name", "N/A")
                result["canonical_date"] = extraction_result.get("canonical_date", "")
                if result["canonical_name"] != "N/A" and result["canonical_name"]:
                    result["verified"] = "true"
                    result["confidence"] = extraction_result.get("case_name_confidence", 0.9)
                    result["source"] = "CourtListener"
                logger.info(f"Extraction complete - extracted: {result['extracted_case_name']}, canonical: {result['canonical_name']}")
            else:
                logger.warning(f"No extraction results for citation: {citation_text}")
        if result["verified"] == "false":
            logger.info(f"Attempting direct API lookup for citation: {citation_text}")
            canonical_result = get_canonical_case_name_with_date(citation_text, api_key)
            if canonical_result:
                result["canonical_name"] = canonical_result.get("case_name", "N/A")
                result["canonical_date"] = canonical_result.get("date", "")
                result["case_name"] = result["canonical_name"]
                result["verified"] = "true"
                result["confidence"] = 0.8
                result["source"] = "CourtListener"
                logger.info(f"Direct lookup successful - canonical: {result['canonical_name']}")
        if result["verified"] == "false":
            pass
    except Exception as e:
        logger.error(f"Error in citation verification: {e}")
        result["error"] = str(e)
        result["explanation"] = f"Verification failed: {e}"
    if result["verified"] == "false" and not result["error"]:
        result["error"] = "Citation could not be verified by any source"
        result["explanation"] = "Citation format may be valid but not found in searched databases"
    return result


class ApplicationError(Exception):
    """Custom exception for application-level errors"""
    pass


class LoggingManager:
    """Centralized logging management"""
    
    @staticmethod
    def setup_logging() -> logging.Logger:
        """Configure logging with fallback strategy"""
        try:
            from src.config import configure_logging
            configure_logging()
            logger = logging.getLogger(__name__)
            logger.info("=== Logging Configuration ===")
            logger.info(f"Python version: {sys.version}")
            logger.info(f"Working directory: {os.getcwd()}")
            return logger
        except Exception as e:
            return LoggingManager._setup_fallback_logging(e)
    
    @staticmethod
    def _setup_fallback_logging(error: Exception) -> logging.Logger:
        """Setup basic logging when centralized config fails"""
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(logs_dir / "app.log")
            ]
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to configure centralized logging: {error}. Using fallback.")
        return logger


class ConfigManager:
    """Configuration management with validation"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration with proper error handling"""
        try:
            from src.config import (
                MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL,
                MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, MAIL_DEBUG,
                UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
            )
            
            self._config = {
                'mail': {
                    'server': MAIL_SERVER,
                    'port': MAIL_PORT,
                    'use_tls': MAIL_USE_TLS,
                    'use_ssl': MAIL_USE_SSL,
                    'username': MAIL_USERNAME,
                    'password': MAIL_PASSWORD,
                    'default_sender': MAIL_DEFAULT_SENDER,
                    'debug': MAIL_DEBUG
                },
                'upload': {
                    'folder': UPLOAD_FOLDER,
                    'allowed_extensions': ALLOWED_EXTENSIONS,
                    'max_content_length': MAX_CONTENT_LENGTH
                }
            }
            self.logger.info("Configuration loaded successfully")
            
        except ImportError as e:
            self.logger.error(f"Failed to import config module: {e}")
            raise ApplicationError(f"Configuration loading failed: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default


class SecurityManager:
    """Handle security-related operations"""
    
    @staticmethod
    def setup_secure_upload_directory(upload_folder: str, logger: logging.Logger) -> bool:
        """Set up secure upload directory with comprehensive security measures"""
        try:
            upload_path = Path(upload_folder)
            
            # Create main directory
            upload_path.mkdir(mode=0o755, exist_ok=True)
            logger.info(f"Upload directory ready: {upload_path}")
            
            # Create organized subdirectories
            subdirs = ['temp', 'processed', 'rejected', 'quarantine']
            for subdir in subdirs:
                subdir_path = upload_path / subdir
                subdir_path.mkdir(mode=0o755, exist_ok=True)
                logger.debug(f"Created subdirectory: {subdir_path}")
            
            # Security files
            SecurityManager._create_security_files(upload_path, logger)
            
            # Test permissions
            SecurityManager._test_directory_permissions(upload_path, logger)
            
            logger.info(f"Secure upload directory setup completed: {upload_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup upload directory: {e}")
            return False
    
    @staticmethod
    def _create_security_files(upload_path: Path, logger: logging.Logger):
        """Create security files to prevent unauthorized access"""
        security_files = {
            '.htaccess': "Order deny,allow\nDeny from all\n",
            'index.html': (
                "<!DOCTYPE html>\n"
                "<html><head><title>403 Forbidden</title></head>\n"
                "<body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>"
            ),
            'web.config': (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<configuration><system.webServer><defaultDocument enabled="false" />'
                '<directoryBrowse enabled="false" /></system.webServer></configuration>'
            )
        }
        
        for filename, content in security_files.items():
            file_path = upload_path / filename
            if not file_path.exists():
                file_path.write_text(content)
                logger.debug(f"Created security file: {file_path}")
    
    @staticmethod
    def _test_directory_permissions(upload_path: Path, logger: logging.Logger):
        """Test write permissions"""
        test_file = upload_path / 'test_write.tmp'
        try:
            test_file.write_text('Permission test')
            test_file.unlink()
            logger.debug("Directory write permissions verified")
        except Exception as e:
            logger.error(f"Directory permission test failed: {e}")
            raise
    
    @staticmethod
    def validate_file_path(path: str, base_dir: str, logger: logging.Logger) -> bool:
        """Validate file path to prevent directory traversal"""
        if '..' in path or path.startswith('/'):
            logger.warning(f"Potential directory traversal attempt: {path}")
            return False
        
        try:
            file_path = os.path.abspath(os.path.join(base_dir, path))
            return file_path.startswith(base_dir)
        except Exception as e:
            logger.error(f"Error validating file path: {e}")
            return False


class ResponseManager:
    """Handle response processing and logging"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._response_count = 0
        self._lock = threading.Lock()
    
    def log_response(self, response, request):
        """Log responses with rate limiting and filtering"""
        with self._lock:
            self._response_count += 1
        
        try:
            # Only log JSON responses and errors
            if (response.content_type == 'application/json' or 
                response.status_code >= 400):
                
                response_data = response.get_data(as_text=True)
                truncated_data = (response_data[:200] + "..." 
                                if len(response_data) > 200 else response_data)
                
                # Use appropriate log level based on status
                if response.status_code >= 500:
                    level = logging.ERROR
                elif response.status_code >= 400:
                    level = logging.WARNING
                else:
                    level = logging.INFO
                
                self.logger.log(
                    level,
                    f"[RESPONSE #{self._response_count}] {request.method} "
                    f"{request.endpoint} -> {response.status_code} "
                    f"({len(response_data)} chars)"
                )
                
                if len(response_data) > 200 and level >= logging.WARNING:
                    self.logger.log(level, f"Body (truncated): {truncated_data}")
        
        except Exception as e:
            self.logger.error(f"Error in response logging: {e}")
        
        return response


class ApplicationFactory:
    """Factory for creating Flask application instances"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.logger = LoggingManager.setup_logging()
        self.config_manager = ConfigManager(self.logger)
        self.response_manager = ResponseManager(self.logger)
        self._setup_signal_handlers()
    
    @classmethod
    def get_instance(cls):
        """Thread-safe singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def create_app(self) -> 'Flask':
        """Create and configure Flask application"""
        if hasattr(self, '_app') and self._app is not None:
            self.logger.info("Returning existing Flask application instance")
            return self._app
        
        self.logger.info("Creating new Flask application instance")
        
        try:
            app = self._configure_flask_app()
            self._register_blueprints(app)
            self._configure_cors(app)
            self._setup_upload_security(app)
            self._register_routes(app)
            self._register_error_handlers(app)
            self._register_middleware(app)
            
            self._app = app
            self.logger.info("Flask application created successfully")
            return app
            
        except Exception as e:
            self.logger.critical(f"Failed to create Flask application: {e}")
            raise ApplicationError(f"Application creation failed: {e}")
    
    def _configure_flask_app(self) -> 'Flask':
        """Configure basic Flask application"""
        from flask import Flask
        
        app = Flask(
            __name__,
            static_folder=str(project_root / "static"),
            template_folder=str(project_root / "static"),
            static_url_path="/casestrainer"
        )
        
        # Environment configuration
        app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
        app.config['DEBUG'] = app.config['ENV'] == 'development'
        app.config['TESTING'] = False
        
        # Security configuration
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
        app.config['MAX_CONTENT_LENGTH'] = self.config_manager.get('upload.max_content_length')
        
        return app
    
    def _register_blueprints(self, app):
        """Register application blueprints"""
        try:
            from src.vue_api_endpoints import vue_api
            app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
            self.logger.info("Registered vue_api blueprint")
        except ImportError as e:
            self.logger.error(f"Failed to import vue_api blueprint: {e}")
            raise ApplicationError("Critical blueprint missing: vue_api")
        
        try:
            from src.citation_api import citation_api
            if citation_api:
                app.register_blueprint(citation_api, url_prefix='/casestrainer/api')
                self.logger.info("Registered enhanced citation_api blueprint")
        except ImportError as e:
            self.logger.warning(f"Optional citation_api blueprint not available: {e}")
        
        # Initialize enhanced citation processor
        try:
            from src.citation_processor import CaseStrainerCitationProcessor
            self.citation_processor = CaseStrainerCitationProcessor()
            self.logger.info("Enhanced citation processor initialized")
        except ImportError as e:
            self.logger.warning(f"Enhanced citation processor not available: {e}")
            self.citation_processor = None
        
        # Initialize progress manager for real-time progress tracking
        try:
            from src.progress_manager import SSEProgressManager, ChunkedCitationProcessor, create_progress_routes
            self.progress_manager = SSEProgressManager()
            self.chunked_processor = ChunkedCitationProcessor(self.progress_manager)
            
            # Register progress-enabled routes
            create_progress_routes(app, self.progress_manager, self.chunked_processor)
            self.logger.info("Progress manager and chunked processor initialized")
        except ImportError as e:
            self.logger.warning(f"Progress manager not available: {e}")
            self.progress_manager = None
            self.chunked_processor = None
    
    def _configure_cors(self, app):
        """Configure CORS with security considerations"""
        from flask_cors import CORS
        
        cors_origins = os.getenv(
            'CORS_ORIGINS', 
            'https://wolf.law.uw.edu,http://localhost:5000,http://localhost:8080'
        ).split(',')
        
        CORS(app,
             resources={r"/*": {"origins": cors_origins}},
             supports_credentials=True,
             allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
             expose_headers=["Content-Disposition", "Content-Type"],
             max_age=3600)  # Cache preflight requests
        
        self.logger.info(f"CORS configured for origins: {cors_origins}")
    
    def _setup_upload_security(self, app):
        """Setup secure upload directory"""
        upload_folder = self.config_manager.get('upload.folder')
        if not SecurityManager.setup_secure_upload_directory(upload_folder, self.logger):
            raise ApplicationError("Failed to setup secure upload directory")
    
    def _register_routes(self, app):
        """Register application routes"""
        from flask import send_from_directory, make_response, request
        
        @app.route('/casestrainer/', defaults={'path': ''})
        @app.route('/casestrainer/<path:path>')
        def serve_vue_app(path):
            return self._serve_static_file(path)
        
        @app.route('/casestrainer/api/health', methods=['GET'])
        def health_check():
            """Enhanced health check endpoint"""
            from flask import jsonify
            try:
                # Basic health checks
                db_manager = self._get_database_manager()
                db_healthy = bool(db_manager)
                
                health_data = {
                    'status': 'healthy' if db_healthy else 'degraded',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '2.0',
                    'components': {
                        'database': 'healthy' if db_healthy else 'unhealthy',
                        'upload_directory': 'healthy'
                    }
                }
                
                status_code = 200 if db_healthy else 503
                return jsonify(health_data), status_code
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 503
        
        @app.route('/casestrainer/api/db_stats', methods=['GET'])
        def db_stats():
            """Database statistics endpoint"""
            from flask import jsonify
            try:
                db_manager = self._get_database_manager()
                stats = db_manager.get_database_stats()
                return jsonify(stats)
            except Exception as e:
                self.logger.error(f"Database stats error: {e}")
                return jsonify({'error': 'Database stats unavailable'}), 503
        
        @app.route('/casestrainer/api/analyze_enhanced', methods=['POST'])
        def enhanced_analyze():
            """Enhanced analyze endpoint with better citation extraction and verification"""
            from flask import request, jsonify
            import logging
            logger = logging.getLogger("citation_verification")
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                input_type = data.get('type', 'text')
                if input_type == 'text':
                    text = data.get('text', '')
                    citations_list = data.get('citations', [])
                    api_key = data.get('api_key', None)
                    if not text:
                        return jsonify({'error': 'No text provided'}), 400
                    if not citations_list:
                        return jsonify({'error': 'No citations provided'}), 400
                    # Use the enhanced verification workflow
                    results = []
                    for citation_text in citations_list:
                        result = verify_citation_with_extraction(
                            citation_text=citation_text,
                            document_text=text,
                            api_key=api_key
                        )
                        results.append(result)
                    return jsonify({'citations': results, 'success': True})
                else:
                    return jsonify({'error': 'File upload processing not implemented in this endpoint'}), 501
            except Exception as e:
                logger.error(f"Error in enhanced analyze endpoint: {e}")
                return jsonify({'error': 'Analysis failed', 'details': str(e)}), 500
        
        # Debug route (only in development)
        if app.config['DEBUG']:
            @app.route('/test')
            def test():
                return 'Test route is working!'
        
        self.logger.info("Application routes registered")
    
    def _serve_static_file(self, path: str):
        """Serve static files with enhanced security and caching"""
        from flask import send_from_directory, make_response
        
        vue_dist_dir = str(project_root / "static")
        
        # Security validation
        if not SecurityManager.validate_file_path(path, vue_dist_dir, self.logger):
            return make_response("Forbidden", 403)
        
        # Serve existing files
        file_path = os.path.join(vue_dist_dir, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            response = send_from_directory(vue_dist_dir, path)
            self._set_cache_headers(response, path)
            self._set_security_headers(response)
            self._set_mime_type(response, path)
            return response
        else:
            # SPA fallback
            response = send_from_directory(vue_dist_dir, 'index.html')
            self._set_security_headers(response)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
    
    def _set_cache_headers(self, response, path: str):
        """Set appropriate caching headers"""
        if path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', 
                          '.svg', '.woff', '.woff2', '.ttf', '.eot')):
            # Static assets: cache for 1 year
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif path.endswith('.html'):
            # HTML files: no cache
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
        else:
            # Other files: cache for 1 hour
            response.headers['Cache-Control'] = 'public, max-age=3600'
    
    def _set_security_headers(self, response):
        """Set security headers"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _set_mime_type(self, response, path: str):
        """Set proper MIME types"""
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
    
    def _register_error_handlers(self, app):
        """Register error handlers"""
        from flask import jsonify
        
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal server error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
        
        @app.errorhandler(Exception)
        def handle_exception(error):
            self.logger.error(f"Unhandled exception: {error}", exc_info=True)
            return jsonify({'error': 'An unexpected error occurred'}), 500
    
    def _register_middleware(self, app):
        """Register middleware"""
        from flask import request
        
        def log_response_wrapper(response):
            return self.response_manager.log_response(response, request)
        
        app.after_request(log_response_wrapper)
    
    def _get_database_manager(self):
        """Get database manager with error handling"""
        try:
            from src.database_manager import get_database_manager
            return get_database_manager()
        except ImportError as e:
            self.logger.error(f"Failed to import database manager: {e}")
            raise ApplicationError("Database manager unavailable")
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            # Add cleanup logic here
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def create_app():
    """Public factory function"""
    factory = ApplicationFactory.get_instance()
    return factory.create_app()


def get_wsgi_application():
    """WSGI entry point for production servers"""
    return create_app()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Enhanced CaseStrainer Application")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5000")))
    parser.add_argument("--debug", action="store_true", 
                       default=os.getenv("FLASK_DEBUG", "").lower() == "true")
    parser.add_argument("--use-waitress", action="store_true", default=False)
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    logger = LoggingManager.setup_logging()
    
    # Log startup information
    logger.info("=" * 80)
    logger.info(f"Starting Enhanced CaseStrainer Application - {datetime.now()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Host: {args.host}, Port: {args.port}")
    logger.info(f"Debug: {args.debug}, Workers: {args.workers}")
    logger.info("=" * 80)
    
    try:
        app = create_app()
        
        if args.use_waitress:
            try:
                from waitress import serve
                logger.info("Starting with Waitress WSGI server")
                serve(app, host=args.host, port=args.port, threads=args.workers * 4)
            except ImportError:
                logger.warning("Waitress not installed. Using Flask dev server.")
                app.run(host=args.host, port=args.port, debug=args.debug)
        else:
            logger.info("Starting with Flask development server")
            app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
            
    except Exception as e:
        logger.critical("Fatal error in main execution", exc_info=True)
        sys.exit(1)


# Create app instance for WSGI servers
app = create_app()

if __name__ == "__main__":
    main()
