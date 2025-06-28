import os
import sys
import logging
import traceback
from datetime import datetime

# Set up logging
# Use project root logs directory
project_root = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def log_system_info():
    """Log system and environment information."""
    import platform

    logger.info("=" * 80)
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Current Working Directory: {os.getcwd()}")
    logger.info(f"Python Path: {sys.path}")
    logger.info("=" * 80)


def main():
    try:
        log_system_info()

        # Import the app
        logger.info("Attempting to import app_final_vue...")
        from src.app_final_vue import create_app

        logger.info("Creating app instance...")
        app = create_app()

        # Log some basic info about the app
        logger.info(f"App name: {app.name}")
        logger.info(f"App debug: {app.debug}")
        logger.info(f"App root_path: {app.root_path}")

        # Try to access a route to see if it works
        with app.test_client() as client:
            logger.info("Testing root route...")
            response = client.get("/")
            logger.info(f"Root route status code: {response.status_code}")

            logger.info("Testing API health check...")
            response = client.get("/casestrainer/api/health")
            logger.info(f"Health check status code: {response.status_code}")
            logger.info(f"Health check response: {response.data.decode()}")

        # Start the development server if everything looks good
        logger.info("Starting Flask development server...")
        app.run(host="0.0.0.0", port=5000, debug=True)

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
