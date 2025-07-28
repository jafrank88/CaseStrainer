"""
Enhanced CaseStrainer Flask Application
Improved version with better error handling, performance, and maintainability
"""

import logging
import os
import sys
import signal
import threading
from pathlib import Path
from typing import Callable, Any, Union, Optional

from flask import Flask
import argparse
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.case_name_extraction_core import extract_case_name_and_date
# Import rate limiter
try:
    from src.rate_limiter import rate_limit, validate_input
    rate_limiter_available = True
except ImportError:
    rate_limiter_available = False
    # Fallback decorators that do nothing
    def rate_limit(max_calls: int = 100, window: int = 3600) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            return f
        return decorator
    
    def validate_input(input_type: str = 'text') -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            return f
        return decorator

# Enhanced citation verification function

def verify_citation_with_extraction(citation_text: str, document_text: str = "", api_key: Optional[str] = None) -> dict[str, Union[str, float, None]]:
    """
    Enhanced citation verification that includes both extraction and database verification.
    This should be called in your main verification workflow.
    """
    import logging
    logger = logging.getLogger("citation_verification")
    
    logger.info(f"🔍 DEBUG: verify_citation_with_extraction called")
    logger.info(f"  citation_text: '{citation_text}'")
    logger.info(f"  document_text length: {len(document_text) if document_text else 0}")
    
    result = {
        "citation": citation_text,
        "canonical_citation": citation_text,
        "primary_citation": citation_text,
        "extracted_case_name": "N/A",
        "extracted_date": "N/A",
        "case_name": "N/A",
        "canonical_name": "N/A",
        "canonical_date": "N/A",
        "verified": "false",
        "confidence": 0.0,
        "source": "Unknown",
        "url": None,
        "error": None,
        "explanation": None
    }
    try:
        if document_text and document_text.strip():
            logger.info(f"🔍 DEBUG: About to call extract_case_name_and_date")
            logger.info(f"  citation_text: '{citation_text}'")
            logger.info(f"  document_text: '{document_text[:100]}...'")
            
            extraction_result = extract_case_name_and_date(text=document_text,
                citation=citation_text)
            
            logger.info(f"🔍 DEBUG: extract_case_name_and_date returned:")
            logger.info(f"  Type: {type(extraction_result)}")
            logger.info(f"  Value: {extraction_result}")
            
            if extraction_result:
                logger.info(f"  Keys: {list(extraction_result.keys())}")
                for key, value in extraction_result.items():
                    logger.info(f"    {key}: '{value}'")
            else:
                logger.warning(f"🔍 DEBUG: extraction_result is None/False")
            if extraction_result:
                logger.info(f"Raw extraction result: {extraction_result}")
                logger.info(f"extraction_result keys: {list(extraction_result.keys())}")
                logger.info(f"case_name value: '{extraction_result.get('case_name', 'KEY_MISSING')}'")
                logger.info(f"year value: '{extraction_result.get('year', 'KEY_MISSING')}'")
                
                # Handle multiple possible field name formats
                extracted_name = (
                    extraction_result.get("case_name") or
                    extraction_result.get("extracted_case_name") or
                    "N/A"
                )
                
                extracted_date = (
                    extraction_result.get("year") or
                    extraction_result.get("date") or
                    "N/A"
                )
                
                # Map to the correct API field names
                result["extracted_case_name"] = extracted_name
                result["extracted_date"] = extracted_date
                result["case_name"] = extraction_result.get("case_name", "N/A")
                result["canonical_name"] = extraction_result.get("canonical_name", "N/A")
                result["canonical_date"] = extraction_result.get("canonical_date", "N/A")
                
                logger.info(f"🔍 DEBUG: After mapping:")
                logger.info(f"  extracted_case_name: '{result['extracted_case_name']}'")
                logger.info(f"  extracted_date: '{result['extracted_date']}'")
                logger.info(f"Mapped values: name='{extracted_name}', date='{extracted_date}'")
                logger.info(f"After assignment:")
                logger.info(f"  result['extracted_case_name']: '{result['extracted_case_name']}'")
                logger.info(f"  result['extracted_date']: '{result['extracted_date']}'")
                
                if result["canonical_name"] != "N/A" and result["canonical_name"]:
                    result["verified"] = "true"
                    result["confidence"] = extraction_result.get("confidence", 0.9)
                    result["source"] = "CourtListener"
                logger.info(f"Extraction complete - extracted: {result['extracted_case_name']}, canonical: {result['canonical_name']}")
            else:
                logger.warning(f"No extraction results for citation: {citation_text}")
                # Ensure we still have the extracted fields even if extraction failed
                result["extracted_case_name"] = "N/A"
                result["extracted_date"] = "N/A"
        if result["verified"] == "false":
            logger.info(f"Citation verification failed for: {citation_text}")
            # DO NOT fall back to canonical lookup here - this causes contamination
            # Canonical lookup should be done separately in the verification workflow
            result["error"] = "Citation could not be verified by any source"
            result["explanation"] = "Citation format may be valid but not found in searched databases"
    except Exception as e:
        logger.error(f"Error in citation verification: {e}")
        result["error"] = str(e)
        result["explanation"] = f"Verification failed: {e}"
    if result["verified"] == "false" and not result["error"]:
        result["error"] = "Citation could not be verified by any source"
        result["explanation"] = "Citation format may be valid but not found in searched databases"
    
    # Final check to ensure extracted fields are always present
    if "extracted_case_name" not in result:
        result["extracted_case_name"] = "N/A"
    if "extracted_date" not in result:
        result["extracted_date"] = "N/A"
    
    logger.info(f"Final result for {citation_text}: extracted_case_name='{result.get('extracted_case_name')}', extracted_date='{result.get('extracted_date')}'")
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
    
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__()
        self.logger = logger
        self._config: dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration with proper error handling"""
        try:
            from src.config import (
                UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH,
                CONTACT_EMAIL, CONTACT_SUBJECT_PREFIX
            )
            
            self._config = {
                'upload': {
                    'folder': UPLOAD_FOLDER,
                    'allowed_extensions': ALLOWED_EXTENSIONS,
                    'max_content_length': MAX_CONTENT_LENGTH
                },
                'contact': {
                    'email': CONTACT_EMAIL,
                    'subject_prefix': CONTACT_SUBJECT_PREFIX
                }
            }
            self.logger.info("Configuration loaded successfully")
            
        except ImportError as e:
            self.logger.error(f"Failed to import config module: {e}")
            raise ApplicationError(f"Configuration loading failed: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
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
    
    @staticmethod
    def sanitize_citation_input(citation: str) -> str:
        """Sanitize citation input to prevent injection attacks"""
        if not citation:
            return ""
        
        # Remove/escape dangerous characters
        import re
        sanitized = re.sub(r'[<>"\']', '', citation)
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_text_input(text: str) -> str:
        """Sanitize text input for processing"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        import re
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limit length
        if len(sanitized) > 100000:  # 100KB limit
            sanitized = sanitized[:100000]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and security"""
        if not url:
            return False
        
        # Basic URL validation
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))


class ResponseManager:
    """Handle response processing and logging"""
    
    def __init__(self, logger: logging.Logger) -> None:
        super().__init__()
        self.logger = logger
        self._response_count = 0
        self._lock = threading.Lock()
    
    def log_response(self, response: Any, request: Any) -> Any:
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
    
    def __init__(self) -> None:
        super().__init__()
        self.logger = LoggingManager.setup_logging()
        self.config_manager = ConfigManager(self.logger)
        self.response_manager = ResponseManager(self.logger)
        self._app: Optional[Flask] = None
        self._setup_signal_handlers()
    
    @classmethod
    def get_instance(cls) -> 'ApplicationFactory':
        """Thread-safe singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def create_app(self) -> 'Flask':
        """Create and configure Flask application"""
        if hasattr(self, '_app') and self._app:
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
            self.logger.critical(f"Failed to create Flask application: {str(e)}")
            raise ApplicationError(f"Application creation failed: {str(e)}")
    
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
    
    def _register_blueprints(self, app: Any) -> None:
        """Register application blueprints with proper error handling"""
        # Register blueprints
        self.logger.info("Starting blueprint registration...")
        
        try:
            # Register main production API endpoints
            self.logger.info("Attempting to import vue_api_endpoints...")
            from src.vue_api_endpoints import vue_api
            self.logger.info("vue_api_endpoints imported successfully")
            
            app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
            self.logger.info("Vue API blueprint registered successfully - PRODUCTION API ACTIVE")
            return  # Exit early if successful
            
        except Exception as e:
            self.logger.error(f"CRITICAL: Could not register Vue API: {e}")
            import traceback
            self.logger.error(f"Vue API import traceback: {traceback.format_exc()}")
            
            # Fallback to debug API (remove development mode restriction for troubleshooting)
            self.logger.warning("Falling back to debug API due to Vue API failure")
            try:
                from src.debug_test_api import debug_api
                app.register_blueprint(debug_api, url_prefix='/casestrainer/api')
                self.logger.warning("Debug API registered as fallback - THIS SHOULD NOT HAPPEN IN PRODUCTION")
            except Exception as e2:
                self.logger.critical(f"FATAL: Could not register any API endpoints: {e2}")
                raise RuntimeError(f"No API endpoints could be registered: Vue API failed with {e}, Debug API failed with {e2}")

    def _configure_cors(self, app: Any) -> None:
        """Configure CORS with security considerations"""
        from flask_cors import CORS

        cors_origins = os.getenv(
            'CORS_ORIGINS',
            'https://wolf.law.uw.edu,http://localhost:5000,http://localhost:8080'
        ).split(',')

        _ = CORS(app,
             resources={r"/*": {"origins": cors_origins}},
             supports_credentials=True,
             allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
             expose_headers=["Content-Disposition", "Content-Type"],
             max_age=3600)  # Cache preflight requests

        self.logger.info(f"CORS configured for origins: {cors_origins}")

    def _setup_upload_security(self, app: Any) -> None:
        """Setup secure upload directory"""
        upload_folder = self.config_manager.get('upload.folder')
        if not SecurityManager.setup_secure_upload_directory(upload_folder, self.logger):
            raise ApplicationError("Failed to setup secure upload directory")

    def _register_routes(self, app: Any) -> None:
        """Register application routes"""
        
        @app.route('/casestrainer/', defaults={'path': ''})
        @app.route('/casestrainer/<path:path>')
        def serve_vue_app(path: str) -> Any:
            return self._serve_static_file(path)
        
        # Test route for debugging
        @app.route('/test')
        def test() -> str:
            return 'Test route is working!'
        
        self.logger.info("Application routes registered")
        # Log all registered routes for debugging
        self.logger.info("=== REGISTERED ROUTES ===")
        for rule in app.url_map.iter_rules():
            self.logger.info(f"Route: {rule} -> Endpoint: {rule.endpoint}")
    
    def _serve_static_file(self, path: str) -> Any:
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
    
    def _set_cache_headers(self, response: Any, path: str) -> None:
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
    
    def _set_security_headers(self, response: Any) -> None:
        """Set comprehensive security headers"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                       "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                                       "font-src 'self'; connect-src 'self';"),
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _set_mime_type(self, response: Any, path: str) -> None:
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
    
    def _register_error_handlers(self, app: Any) -> None:
        """Register error handlers"""
        from flask import jsonify
        
        @app.errorhandler(404)
        def not_found(error: Any) -> tuple[Any, int]:
            return jsonify({'error': 'Not found'}), 404
        
        @app.errorhandler(500)
        def internal_error(error: Any) -> tuple[Any, int]:
            self.logger.error(f"Internal server error: {error}")
            return jsonify({'error': 'Internal server error'}), 500
        
        @app.errorhandler(Exception)
        def handle_exception(error: Any) -> tuple[Any, int]:
            self.logger.error(f"Unhandled exception: {error}", exc_info=True)
            return jsonify({'error': 'An unexpected error occurred'}), 500
    
    def _register_middleware(self, app: Any) -> None:
        """Register middleware"""
        from flask import request
        
        def log_response_wrapper(response: Any) -> Any:
            return self.response_manager.log_response(response, request)
        
        app.after_request(log_response_wrapper)
    
    def _get_database_manager(self) -> Any:
        """Get database manager with error handling"""
        try:
            from src.database_manager import get_database_manager
            return get_database_manager()
        except ImportError as e:
            self.logger.error(f"Failed to import database manager: {e}")
            raise ApplicationError("Database manager unavailable")
    
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers"""
        import threading
        def signal_handler(signum: int, frame: Any) -> None:
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            # Add cleanup logic here
            sys.exit(0)
        # Only set up signal handlers in the main thread
        if threading.current_thread() is threading.main_thread():
            _ = signal.signal(signal.SIGINT, signal_handler)
            _ = signal.signal(signal.SIGTERM, signal_handler)
        else:
            self.logger.info("Skipping signal handler setup (not in main thread)")


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
    _ = parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    _ = parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5000")))
    _ = parser.add_argument("--debug", action="store_true", 
                       default=os.getenv("FLASK_DEBUG", "").lower() == "true")
    _ = parser.add_argument("--use-waitress", action="store_true", default=False)
    _ = parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
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
            
    except Exception:
        logger.critical("Fatal error in main execution", exc_info=True)
        sys.exit(1)


# Create app instance for WSGI servers
app = create_app()

if __name__ == "__main__":
    main()
