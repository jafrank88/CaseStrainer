import sys
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import app_final_vue
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))


def list_routes():
    try:
        from src.app_final_vue import create_app

        logger.info("Creating app instance...")
        app = create_app()

        logger.info("\nRegistered routes:")
        logger.info("-" * 80)

        # Get all routes and sort them
        routes = []
        for rule in app.url_map.iter_rules():
            methods = ",".join(rule.methods - {"OPTIONS", "HEAD"})
            routes.append((str(rule), rule.endpoint, methods))

        # Sort routes by URL
        routes.sort(key=lambda x: x[0])

        # Print routes
        for route, endpoint, methods in routes:
            logger.info(f"{endpoint:50s} {methods:20s} {route}")

        logger.info("\nNote: The API is mounted at /casestrainer/api/")
        logger.info("Example endpoints:")
        logger.info("  GET  /casestrainer/api/version")
        logger.info(
            '  POST /casestrainer/api/analyze -d \'{"text":"Sample text with citation 534 F.3d 1290"}\''
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    list_routes()
