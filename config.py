"""
Configuration settings for CaseStrainer application
"""


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
    COURTLISTENER_API_KEY = (
        ""  # Will be loaded from config.json or environment variables
    )

    # Application Settings
    APP_NAME = "CaseStrainer"
    APP_VERSION = "4.0.0"
    ENHANCED_VALIDATOR_ENABLED = True
