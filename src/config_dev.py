# Development Configuration
# This file contains settings specific to the development environment

import os

# Flask settings
DEBUG = True
TESTING = False
SECRET_KEY = "dev-key-please-change-in-production"

# Database settings
SQLALCHEMY_DATABASE_URI = "sqlite:///casestrainer_dev.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# API Settings
API_PREFIX = "/api"
API_VERSION = "v1"

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:4173",  # Vite preview
    "http://127.0.0.1:4173",
]

# Logging
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}

# Cache settings
CACHE_TYPE = "simple"
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

# Session settings
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Security settings
SECURITY_PASSWORD_SALT = "dev-salt-please-change-in-production"
SECURITY_CONFIRMABLE = False
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SECURITY_CHANGEABLE = True

# Email settings (for password reset, etc.)
MAIL_SERVER = "smtp.example.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = "noreply@example.com"
MAIL_PASSWORD = "your-email-password"
MAIL_DEFAULT_SENDER = "noreply@example.com"
