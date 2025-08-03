"""
Configuration settings for CaseStrainer application
"""

import os
import logging


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
    # Application settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-casestrainer')
    
    # Session settings
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Application settings
    ENV = os.environ.get('FLASK_ENV', 'production')
    APP_NAME = "CaseStrainer"
    APP_VERSION = "0.6.4"
    
    # Static files
    STATIC_FOLDER = '../static/vue'
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Upload settings
    UPLOAD_FOLDER = os.path.abspath("uploads")
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'html', 'htm'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # API settings
    API_PREFIX = '/api'
    COURTLISTENER_API_KEY = os.environ.get('COURTLISTENER_API_KEY', '')
    COURTLISTENER_API_URL = 'https://www.courtlistener.com/api/rest/v4/'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///citations.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS settings
    CORS_HEADERS = 'Content-Type'
    
    # Application root
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/casestrainer')


class DefaultConfig(Config):
    """Default configuration that can be overridden by environment variables"""
    pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Development server settings
    HOST = '127.0.0.1'
    PORT = 5000
    
    # Enable more verbose logging
    SQLALCHEMY_ECHO = False
    
    # Disable caching in development
    SEND_FILE_MAX_AGE_DEFAULT = 0


class ProductionConfig(Config):
    """Production configuration"""
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production server settings
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Enable protection against common attacks
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'dev-password-salt')
    
    # Logging
    LOG_LEVEL = 'WARNING'


def configure_logging():
    """
    Configure logging for the application.

    Returns:
        logging.Logger: The configured logger instance
    """
    # Use /app/logs in Docker or ./logs locally
    log_dir = "/app/logs" if os.path.exists("/app/logs") else "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "casestrainer.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file)],
    )
    logger = logging.getLogger("casestrainer")
    logger.info("Logging configured")
    return logger
