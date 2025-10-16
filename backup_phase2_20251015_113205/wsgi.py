"""
WSGI config for CaseStrainer.

This module contains the WSGI application used by the production server.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging before importing the app
try:
    from src.config import configure_logging
    configure_logging()
except ImportError:
    # Fallback if src.config is not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('wsgi.log')
        ]
    )

logger = logging.getLogger('wsgi')

# Add the project directory to the Python path
project_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_dir)

# Set the environment to production if not already set
os.environ.setdefault('FLASK_ENV', 'production')

# Import the application after path is set
from src.app_final_vue import create_app

# Create the application instance for WSGI servers
application = create_app()

if __name__ == "__main__":
    try:
        # Run the application using Waitress for production
        from waitress import serve

        # Get port from environment variable or use default
        port = int(os.environ.get("PORT", 5000))
        host = os.environ.get("HOST", "0.0.0.0")

        # Log startup information
        logger.info(f"Starting CaseStrainer on {host}:{port}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
        logger.info(f"Debug mode: {application.debug}")
        
        # Start the Waitress server with 4 threads
        serve(application, host=host, port=port, threads=4)
        
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}", exc_info=True)
        raise
