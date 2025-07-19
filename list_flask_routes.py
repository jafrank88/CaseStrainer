import sys
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)


def list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, rule)
        output.append(line)

    for line in sorted(output):
        logger.info(line)


def create_app():
    # Add the src directory to the path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

    # Import the app factory function
    from app_final_vue import create_app

    # Create the app instance
    app = create_app()
    return app


if __name__ == "__main__":
    logger.info("Creating Flask app...")
    app = create_app()

    logger.info("\nRegistered routes:")
    logger.info("-" * 80)
    list_routes(app)

    logger.info("\nAvailable endpoints:")
    logger.info("  GET  /api/version")
    logger.info("  POST /api/analyze")
    logger.info("  GET  /api/confirmed_with_multitool_data")
    logger.info("  GET  /api/processing_progress")
    logger.info("  POST /api/validate_citations")
