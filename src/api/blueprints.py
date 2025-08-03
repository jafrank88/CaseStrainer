"""
Blueprint registration for the CaseStrainer API
"""
import os
import sys
import logging
from flask import Blueprint

# Set up logging
logger = logging.getLogger(__name__)

def register_blueprints(app):
    """Register all blueprints with the Flask application"""
    logger.info("=== REGISTERING BLUEPRINTS ===")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    try:
        # Try to import the Vue API blueprint
        logger.info("Attempting to import Vue API blueprint...")
        try:
            # Try absolute import first - use the updated version
            from src.vue_api_endpoints_updated import vue_api as vue_api_blueprint
            logger.info("✅ Successfully imported Vue API blueprint (updated) using absolute import")
        except ImportError as e1:
            logger.warning(f"Updated import failed: {e1}")
            # Fall back to original version
            try:
                from src.vue_api_endpoints import vue_api as vue_api_blueprint
                logger.info("✅ Successfully imported Vue API blueprint (original) using absolute import")
            except ImportError as e2:
                logger.warning(f"Original absolute import failed: {e2}")
                # Fall back to relative import
                try:
                    from ..vue_api_endpoints import vue_api as vue_api_blueprint
                    logger.info("✅ Successfully imported Vue API blueprint using relative import")
                except ImportError as e3:
                    logger.error(f"All import attempts failed: {e1} / {e2} / {e3}")
                    logger.error(f"Python path: {sys.path}")
                    logger.error(f"Current directory contents: {os.listdir(os.path.dirname(__file__))}")
                    raise ImportError(f"Could not import Vue API blueprint: {e1} / {e2} / {e3}")
        
        # Log blueprint details before registration
        logger.info(f"Blueprint details: {vue_api_blueprint}")
        logger.info(f"- Name: {vue_api_blueprint.name}")
        logger.info(f"- Import Name: {vue_api_blueprint.import_name}")
        
        # Register the Vue API blueprint
        logger.info("Registering Vue API blueprint...")
        app.register_blueprint(
            vue_api_blueprint,
            url_prefix='/casestrainer/api'
        )
        logger.info("✅ Vue API blueprint registered successfully")
        
        # Log all registered blueprints
        logger.info("\n=== CURRENTLY REGISTERED BLUEPRINTS ===")
        for name, bp in app.blueprints.items():
            logger.info(f"- {name}: {bp}")
            logger.info(f"  - URL Prefix: {getattr(bp, 'url_prefix', 'N/A')}")
            logger.info(f"  - Import Name: {getattr(bp, 'import_name', 'N/A')}")
        
        return app
        
    except Exception as e:
        logger.error(f"❌ Error registering blueprints: {e}", exc_info=True)
        raise
