"""
Configuration settings for CaseStrainer application
"""

import os


def get_config_value(key, default=None):
    """
    Get a configuration value from environment variables or the Config class.

    Args:
        key (str): The configuration key to look up
        default: Default value if key is not found

    Returns:
        The configuration value or the default if not found.
        If default is a string, ensures the return value is a string.
    """
    # First try to get from environment variables
    value = os.environ.get(key)
    if value is not None:
        # If default is a string, ensure we return a string
        if isinstance(default, str) and not isinstance(value, str):
            return str(value).lower()
        return value

    # Then try to get from Config class
    if hasattr(Config, key):
        value = getattr(Config, key)
        # If default is a string, ensure we return a string
        if isinstance(default, str) and not isinstance(value, str):
            return str(value).lower()
        return value

    # If default is provided, return it (will be converted to string if default is string)
    if default is not None and isinstance(default, str):
        return default.lower() if isinstance(default, str) else str(default).lower()
    return default


class Config:
    """Base configuration class"""

    DEBUG = False
    TESTING = False
    SECRET_KEY = "dev-key-for-casestrainer"
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # API Keys and External Services
    COURTLISTENER_API_KEY = os.environ.get("COURTLISTENER_API_KEY", "")
    COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v4/"

    # Database Configuration
    DATABASE_FILE = "citations.db"

    # File Upload Configuration
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}

    # Application Settings
    APP_NAME = "CaseStrainer"
    APP_VERSION = "4.0.0"

    # Feature Flags
    ENHANCED_VALIDATOR_ENABLED = True
    ENHANCED_VALIDATOR_MODEL_PATH = None
    ML_CLASSIFIER_AVAILABLE = False
    ML_CLASSIFIER_MODEL_PATH = None
    CORRECTION_ENGINE_AVAILABLE = False
    CORRECTION_ENGINE_MODEL_PATH = None

    # Email Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in [
        "true",
        "1",
        "t",
        "y",
        "yes",
    ]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in [
        "true",
        "1",
        "t",
        "y",
        "yes",
    ]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@example.com")
    MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "admin@example.com")
    MAIL_DEBUG = os.environ.get("MAIL_DEBUG", "false").lower() in [
        "true",
        "1",
        "t",
        "y",
        "yes",
    ]

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-for-casestrainer")

    # Session Configuration
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # File Upload Limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size


def configure_logging():
    """
    Configure logging for the application.

    Returns:
        logging.Logger: The configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler("casestrainer.log")],
    )
    logger = logging.getLogger("casestrainer")
    logger.info("Logging configured")
    return logger
