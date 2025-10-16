"""
Development server for CaseStrainer.

This script starts a development server with auto-reload and debug mode enabled.
"""

import os
from src.app_final_vue import create_app

# Set the environment to development
os.environ['FLASK_ENV'] = 'development'

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Get host and port from config
    host = app.config.get('HOST', '127.0.0.1')
    port = int(app.config.get('PORT', 5000))
    
    # Run the development server
    app.run(host=host, port=port, debug=True)
