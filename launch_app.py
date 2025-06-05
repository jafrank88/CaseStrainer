import sys
import logging
from src.app_final_vue import create_app, app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)

    try:
        # Create the Flask app
        app = create_app()

        # Run the application
        logger.info("Starting CaseStrainer application...")
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)
