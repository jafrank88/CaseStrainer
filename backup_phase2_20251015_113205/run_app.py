"""
Simple script to run the Flask application directly
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variables
os.environ['FLASK_APP'] = 'src.app_final_vue:app'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Import and run the application
from src.app_final_vue import app, create_app

if __name__ == '__main__':
    # Create the app instance
    app = create_app()
    
    # Print registered routes
    print("\n=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
    
    # Run the application
    print("\n=== STARTING FLASK APPLICATION ===")
    app.run(host='0.0.0.0', port=5000, debug=True)
