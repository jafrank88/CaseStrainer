"""
Blueprint registration for the CaseStrainer API
"""

import os

import sys
import logging

logger = logging.getLogger(__name__)


def register_blueprints(app):
    """Register all blueprints with the Flask application"""
    logger.info("=== REGISTERING BLUEPRINTS ===")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")

    try:
        from src.vue_api_endpoints_updated import vue_api as vue_api_blueprint

        if "vue_api" not in app.blueprints:
            app.register_blueprint(vue_api_blueprint, url_prefix="/casestrainer/api")
            logger.info("Vue API blueprint registered")
        else:
            logger.info("vue_api blueprint already registered, skipping")

        return app

    except Exception as e:
        logger.error(f"Error registering blueprints: {e}", exc_info=True)
        raise
