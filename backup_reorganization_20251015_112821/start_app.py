import os
import sys
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Set up logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(
    logs_dir, f"app_startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

try:
    logger.info("Starting CaseStrainer application...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")

    # Import and create the app
    from app_final_vue import create_app

    app = create_app()

    # Start the application
    logger.info("Starting Flask development server...")
    app.run(host="0.0.0.0", port=5000, debug=True)

except Exception as e:
    logger.error(f"Failed to start application: {str(e)}")
    logger.error(traceback.format_exc())
    raise
