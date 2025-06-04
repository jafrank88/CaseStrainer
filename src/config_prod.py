# Production Configuration
# This file contains settings specific to the production environment

import os
from datetime import timedelta

# Flask settings
DEBUG = False
TESTING = False
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "change-this-in-production")

# Database settings
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL", "postgresql://username:password@localhost/casestrainer_prod"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# API Settings
API_PREFIX = "/api"
API_VERSION = "v1"

# CORS Settings - Update with your production domains
CORS_ORIGINS = [
    "https://your-production-domain.com",
]

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File upload settings
UPLOAD_FOLDER = "/var/www/casestrainer/uploads"
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}

# Cache settings
CACHE_TYPE = "redis"
CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour

# Session settings
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Security settings
SECURITY_PASSWORD_SALT = os.environ.get(
    "SECURITY_PASSWORD_SALT", "change-this-in-production"
)
SECURITY_CONFIRMABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SECURITY_CHANGEABLE = True

# Rate limiting
RATELIMIT_STORAGE_URL = CACHE_REDIS_URL
RATELIMIT_STRATEGY = "fixed-window"
RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"

# Email settings
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.sendgrid.net")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "1", "t"]
MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ["true", "1", "t"]
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "apikey")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@yourdomain.com")

# Monitoring and error tracking
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")

# Feature flags
ENABLE_MAINTENANCE_MODE = False

# API keys (load from environment variables in production)
COURTLISTENER_API_KEY = os.environ.get("COURTLISTENER_API_KEY", "")
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", "")

# Storage settings
USE_S3 = os.environ.get("USE_S3", "false").lower() in ["true", "1", "t"]
if USE_S3:
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-west-2")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    UPLOAD_FOLDER = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
