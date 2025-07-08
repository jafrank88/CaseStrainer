import os
import json
from dotenv import load_dotenv
import logging
from typing import Optional

# Optional Sentry integration
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

# Load environment variables from .env if present
load_dotenv()

# Load config.json once
CONFIG_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
try:
    with open(CONFIG_JSON_PATH, "r") as f:
        CONFIG_JSON = json.load(f)
except Exception:
    CONFIG_JSON = {}


def get_config_value(key, default=None):
    # Try environment variable (case-sensitive)
    value = os.environ.get(key)
    if value is not None and value != "":
        return value
    # Try config.json (case-sensitive, then lower-case fallback)
    if key in CONFIG_JSON:
        return CONFIG_JSON[key]
    if key.lower() in CONFIG_JSON:
        return CONFIG_JSON[key.lower()]
    return default


# General app config (use get_config_value for all relevant keys)
SECRET_KEY: str = get_config_value("SECRET_KEY", "devkey")
# Get the base directory (one level up from src)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Set the database file path to be in the data directory
DATABASE_FILE: str = get_config_value(
    "DATABASE_FILE", os.path.join(BASE_DIR, "data", "citations.db")
)
print(f"Database file path: {DATABASE_FILE}")  # Debug print

# Feature flags
USE_ENHANCED_VALIDATOR: bool = get_config_value("USE_ENHANCED_VALIDATOR", True)
ENHANCED_VALIDATOR_AVAILABLE: bool = get_config_value(
    "ENHANCED_VALIDATOR_AVAILABLE", True
)
ENHANCED_VALIDATOR_MODEL_PATH: str = get_config_value(
    "ENHANCED_VALIDATOR_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "enhanced_validator"),
)
ML_CLASSIFIER_AVAILABLE: bool = get_config_value("ML_CLASSIFIER_AVAILABLE", True)
ML_CLASSIFIER_MODEL_PATH: str = get_config_value(
    "ML_CLASSIFIER_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "ml_classifier"),
)
CORRECTION_ENGINE_AVAILABLE: bool = get_config_value(
    "CORRECTION_ENGINE_AVAILABLE", True
)
CORRECTION_ENGINE_MODEL_PATH: str = get_config_value(
    "CORRECTION_ENGINE_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "correction_engine"),
)

# Upload settings
UPLOAD_FOLDER = os.path.abspath("uploads")
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'html', 'htm'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size

# Email configuration for UW SMTP
MAIL_SERVER: str = get_config_value("MAIL_SERVER", "smtp.uw.edu")
MAIL_PORT: int = int(get_config_value("MAIL_PORT", 587))
MAIL_USE_TLS: bool = get_config_value("MAIL_USE_TLS", "True").lower() == "true"
MAIL_USE_SSL: bool = get_config_value("MAIL_USE_SSL", "False").lower() == "true"
MAIL_USERNAME: str = get_config_value(
    "MAIL_USERNAME", "jafrank"
)  # Just the NetID, not full email
MAIL_PASSWORD: str = get_config_value("MAIL_PASSWORD", "Race4theGa!axy!")
MAIL_DEFAULT_SENDER: str = get_config_value("MAIL_DEFAULT_SENDER", "jafrank@uw.edu")
MAIL_RECIPIENT: str = get_config_value("MAIL_RECIPIENT", "jafrank@uw.edu")
MAIL_DEBUG: bool = (
    get_config_value("MAIL_DEBUG", "True").lower() == "true"
)  # Enable debug output
COURTLISTENER_API_URL: str = get_config_value(
    "COURTLISTENER_API_URL", "https://www.courtlistener.com/api/rest/v4/opinions/"
)
COURTLISTENER_API_KEY: str = get_config_value("COURTLISTENER_API_KEY", "")


LANGSEARCH_API_KEY: str = get_config_value("LANGSEARCH_API_KEY", "")
SESSION_TYPE: str = get_config_value("SESSION_TYPE", "filesystem")
SESSION_FILE_DIR: str = get_config_value(
    "SESSION_FILE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "casestrainer_sessions"),
)
SESSION_COOKIE_PATH: str = get_config_value("SESSION_COOKIE_PATH", "/casestrainer/")
SENTRY_DSN: Optional[str] = get_config_value("SENTRY_DSN")

if SENTRY_DSN and sentry_sdk:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,  # Adjust as needed
        environment=os.environ.get("ENVIRONMENT", "production"),
    )

# ============================================================================
# CITATION PROCESSING SETTINGS (ADDED FOR CITATIONSERVICE)
# ============================================================================

# Citation extraction settings for CitationService
CITATION_CONTEXT_WINDOW: int = int(get_config_value("CITATION_CONTEXT_WINDOW", "300"))
CITATION_CHUNK_SIZE: int = int(get_config_value("CITATION_CHUNK_SIZE", "5000"))
MIN_CITATION_CONFIDENCE: float = float(get_config_value("MIN_CITATION_CONFIDENCE", "0.7"))

# Immediate processing thresholds for CitationService
IMMEDIATE_PROCESSING_MAX_LENGTH: int = int(get_config_value("IMMEDIATE_PROCESSING_MAX_LENGTH", "50"))
IMMEDIATE_PROCESSING_MAX_WORDS: int = int(get_config_value("IMMEDIATE_PROCESSING_MAX_WORDS", "10"))

# Citation extraction timeout
CITATION_EXTRACTION_TIMEOUT: int = int(get_config_value("CITATION_EXTRACTION_TIMEOUT", "120"))

# ============================================================================
# HELPER FUNCTIONS FOR CITATIONSERVICE
# ============================================================================

def get_citation_config() -> dict:
    """
    Get citation processing configuration for CitationService.
    """
    return {
        'context_window': CITATION_CONTEXT_WINDOW,
        'chunk_size': CITATION_CHUNK_SIZE,
        'min_confidence': MIN_CITATION_CONFIDENCE,
        'immediate_max_length': IMMEDIATE_PROCESSING_MAX_LENGTH,
        'immediate_max_words': IMMEDIATE_PROCESSING_MAX_WORDS,
        'extraction_timeout': CITATION_EXTRACTION_TIMEOUT
    }

def get_external_api_config() -> dict:
    """
    Get external API configuration for CitationService.
    """
    return {
        'courtlistener': {
            'api_key': COURTLISTENER_API_KEY,
            'api_url': COURTLISTENER_API_URL
        },
        'langsearch': {
            'api_key': LANGSEARCH_API_KEY
        }
    }

def get_file_config() -> dict:
    """
    Get file processing configuration for CitationService.
    """
    return {
        'upload_folder': UPLOAD_FOLDER,
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'max_content_length': MAX_CONTENT_LENGTH
    }

# ============================================================================
# TESTING THE CONFIG ADDITIONS
# ============================================================================

def test_config_additions():
    """Test that the new config additions work correctly."""
    print("Testing config additions...")
    
    # Test citation config
    citation_config = get_citation_config()
    print(f"Citation config: {citation_config}")
    
    # Test API config  
    api_config = get_external_api_config()
    print(f"API config: {api_config}")
    
    # Test file config
    file_config = get_file_config()
    print(f"File config: {file_config}")
    
    # Test individual values
    print(f"Context window: {CITATION_CONTEXT_WINDOW}")
    print(f"Chunk size: {CITATION_CHUNK_SIZE}")
    print(f"Immediate max length: {IMMEDIATE_PROCESSING_MAX_LENGTH}")
    print(f"CourtListener API key: {'✓ Set' if COURTLISTENER_API_KEY else '✗ Not set'}")
    
    print("Config test complete!")


def configure_logging(log_level: int = logging.INFO) -> None:
    """
    Configure logging for the CaseStrainer application.
    Uses ConcurrentRotatingFileHandler for robust log rotation on Windows (requires concurrent-log-handler package).
    Creates a 'logs' directory if it does not exist and sets up file and stream handlers.
    Args:
        log_level (int): Logging level (default: logging.INFO)
    """
    import sys

    # Use project root logs directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Use ConcurrentRotatingFileHandler for robust log rotation on Windows
    try:
        from concurrent_log_handler import ConcurrentRotatingFileHandler

        file_handler = ConcurrentRotatingFileHandler(
            os.path.join(logs_dir, "casestrainer.log"), maxBytes=5 * 1024 * 1024, backupCount=5
        )
    except ImportError:
        file_handler = logging.FileHandler(os.path.join(logs_dir, "casestrainer.log"))
    try:
        from colorama import init, Fore, Style

        init()
        COLORAMA_AVAILABLE = True
    except ImportError:
        COLORAMA_AVAILABLE = False

    # Use ISO 8601 format with timezone for consistent timestamps
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"  # FIXED: Removed %f and %z for compatibility
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Stream handler (console)
    class ColorizingStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                msg = self.format(record)
                if COLORAMA_AVAILABLE:
                    if record.levelno >= logging.ERROR:
                        msg = f"{Fore.RED}{msg}{Style.RESET_ALL}"
                    elif record.levelno == logging.WARNING:
                        msg = f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"
                    elif record.levelno == logging.INFO:
                        msg = f"{Fore.CYAN}{msg}{Style.RESET_ALL}"
                # Safely write the message to handle Unicode characters
                try:
                    self.stream.write(msg + self.terminator)
                except UnicodeEncodeError:
                    # If Unicode fails, write a safe version
                    safe_msg = msg.encode('cp1252', errors='replace').decode('cp1252')
                    self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

    stream_handler = ColorizingStreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    # Configure specific loggers based on environment variables
    configure_specific_loggers()


def configure_specific_loggers() -> None:
    """
    Configure specific loggers based on environment variables.
    This allows fine-grained control over logging levels for different components.
    """
    # Configure case_name_extraction logger
    case_name_log_level = os.environ.get("LOG_LEVEL_CASE_NAME_EXTRACTION", "WARNING")
    try:
        # Convert string level to logging constant
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        case_name_level = level_map.get(case_name_log_level.upper(), logging.WARNING)
        
        case_name_logger = logging.getLogger("case_name_extraction")
        case_name_logger.setLevel(case_name_level)
        
        # Log the configuration
        root_logger = logging.getLogger()
        root_logger.info(f"Configured case_name_extraction logger to level: {case_name_log_level} ({case_name_level})")
        
    except Exception as e:
        # Fallback to warning if configuration fails
        logging.getLogger().warning(f"Failed to configure case_name_extraction logger: {e}")
        case_name_logger = logging.getLogger("case_name_extraction")
        case_name_logger.setLevel(logging.WARNING)

# ============================================================================
# MAIN BLOCK FOR TESTING
# ============================================================================

if __name__ == "__main__":
    test_config_additions()
