"""
WSGI config for CaseStrainer.

This module contains the WSGI application used by the production server.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_dir)


def create_app():
    """Create and configure the Flask application."""
    # Load environment variables from .env.production if it exists
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(__file__), ".env.production")
    if os.path.exists(env_path):
        load_dotenv(env_path)

    # Import the application factory
    from src.app_final_vue import create_app

    # Create the application instance
    app = create_app()

    # Configure logging
    from src.logging_config import configure_logging

    app = configure_logging(app)

    # Log application startup
    app.logger.info("WSGI application created")

    return app


# Create the application instance for WSGI servers
application = create_app()

if __name__ == "__main__":
    # Run the application using Waitress for production
    from waitress import serve

    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))

    # Log startup information
    print(f"Starting CaseStrainer on port {port}...")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")

    # Start the server
    serve(application, host="0.0.0.0", port=port, threads=4)
