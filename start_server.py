import os
import sys
import logging
from waitress import serve
from src.app_final_vue import create_app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("server.log")
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting CaseStrainer server...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Create the Flask app
        app = create_app()
        
        # Start the server
        logger.info("Starting Waitress server on 0.0.0.0:5000")
        serve(
            app,
            host='0.0.0.0',
            port=5000,
            threads=4,
            channel_timeout=300,
            cleanup_interval=30,
            connection_limit=1000,
            max_request_header_size=262144,
            max_request_body_size=1073741824
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
