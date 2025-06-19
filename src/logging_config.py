"""
Production logging configuration for CaseStrainer.
"""

import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
ERROR_LOG = os.path.join(LOG_DIR, "error.log")
ACCESS_LOG = os.path.join(LOG_DIR, "access.log")
APPLICATION_LOG = os.path.join(LOG_DIR, "application.log")

# Email configuration for error notifications
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.example.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "1", "t"]
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "noreply@example.com")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
ADMINS = os.environ.get("ADMINS", "admin@example.com").split(",")


class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record):
        from flask import g

        record.request_id = getattr(g, "request_id", "no-request-id")
        return True


def configure_logging(app):
    """Configure logging for the application."""
    # Disable default Flask/Werkzeug logging
    app.logger.handlers.clear()

    # Set log level
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    app.logger.setLevel(log_level)

    # Allow dynamic log level adjustment for performance optimization
    def set_performance_mode(enabled=True):
        """Adjust logging level for performance-critical operations."""
        if enabled:
            app.logger.setLevel(logging.WARNING)  # Reduce logging during high-load operations
            app.logger.info("Performance mode enabled: Logging level set to WARNING")
        else:
            app.logger.setLevel(log_level)  # Restore original log level
            app.logger.info(f"Performance mode disabled: Logging level restored to {log_level}")

    app.set_performance_mode = set_performance_mode

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(request_id)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler for errors
    error_handler = RotatingFileHandler(
        ERROR_LOG, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(RequestIdFilter())

    # File handler for application logs
    app_handler = RotatingFileHandler(
        APPLICATION_LOG,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)
    app_handler.addFilter(RequestIdFilter())

    # Console handler for development
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(RequestIdFilter())
        app.logger.addHandler(console_handler)

    # Email handler for critical errors
    if not app.debug and MAIL_SERVER:
        mail_handler = SMTPHandler(
            mailhost=(MAIL_SERVER, MAIL_PORT),
            fromaddr=f'noreply@{app.config["SERVER_NAME"] or "example.com"}',
            toaddrs=ADMINS,
            subject=f'CaseStrainer Application Error - {app.config["ENV"].title()}',
            credentials=(MAIL_USERNAME, MAIL_PASSWORD) if MAIL_USERNAME else None,
            secure=() if MAIL_USE_TLS else None,
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(
            logging.Formatter(
                """\
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:
%(message)s
"""
            )
        )
        mail_handler.addFilter(RequestIdFilter())
        app.logger.addHandler(mail_handler)

    # Add handlers to the logger
    app.logger.addHandler(error_handler)
    app.logger.addHandler(app_handler)

    # Log application startup
    app.logger.info("CaseStrainer application started")
    app.logger.info(f'Environment: {app.config["ENV"]}')
    app.logger.info(f"Debug mode: {app.debug}")

    # Log unhandled exceptions
    def log_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        app.logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    import sys

    sys.excepthook = log_exception

    return app
