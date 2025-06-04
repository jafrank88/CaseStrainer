"""
Enhanced Validator Utilities

This module contains utility functions for registering and managing the enhanced validator.
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the registration function
register_enhanced_validator_func = None


def register_enhanced_validator_with_app(app):
    """Register the enhanced validator with the Flask app.

    This should be called from the application factory or main app file.
    """
    global register_enhanced_validator_func

    try:
        from enhanced_validator_production import register_enhanced_validator

        # Store the function for later use
        register_enhanced_validator_func = register_enhanced_validator

        # Register the enhanced validator with the app
        if callable(register_enhanced_validator_func):
            logger.info("Registering enhanced validator with Flask app")
            app = register_enhanced_validator_func(app)
            logger.info("Enhanced Validator registered successfully")

            # Log the registered blueprints for debugging
            if hasattr(app, "blueprints"):
                logger.info(f"Registered blueprints: {list(app.blueprints.keys())}")
            else:
                logger.warning("No blueprints registered in the app")

        else:
            logger.warning("register_enhanced_validator is not callable")

        return app
    except ImportError as e:
        logger.warning(f"Could not import enhanced validator: {e}")
        logger.warning("The application will run with basic validation only.")
    except Exception as e:
        logger.error(f"Error registering enhanced validator: {e}", exc_info=True)
        logger.warning("The application will run with basic validation only.")

    return app
