"""
Debug endpoint to test Vue API registration and functionality
"""
import os
import sys
import logging
from flask import Flask, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_debug_app():
    """Create a debug Flask application to test Vue API registration"""
    app = Flask(__name__)
    
    # Add a test route to verify the app is running
    @app.route('/test')
    def test():
        return jsonify({
            'status': 'ok',
            'message': 'Debug endpoint is working',
            'python_path': sys.path,
            'cwd': os.getcwd()
        })
    
    # Try to import and register the Vue API blueprint
    try:
        logger.info("Attempting to import Vue API blueprint...")
        from src.vue_api_endpoints import vue_api
        logger.info("✅ Successfully imported Vue API blueprint")
        
        # Register the blueprint
        app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
        logger.info("✅ Successfully registered Vue API blueprint")
        
        # Log registered routes
        logger.info("\n=== REGISTERED ROUTES ===")
        for rule in app.url_map.iter_rules():
            methods = rule.methods or set()
            logger.info(f"- {rule.endpoint}: {rule.rule} ({', '.join(methods)})")
        
        # Check if the health endpoint is registered
        health_route = next((r for r in app.url_map.iter_rules() if 'health' in r.rule), None)
        if health_route:
            logger.info(f"\n✅ Health endpoint found: {health_route.rule}")
        else:
            logger.warning("\n❌ Health endpoint not found in registered routes")
        
    except Exception as e:
        logger.error(f"❌ Error registering Vue API blueprint: {e}", exc_info=True)
    
    return app

if __name__ == "__main__":
    # Create and run the debug application
    debug_app = create_debug_app()
    debug_app.run(host='0.0.0.0', port=5001, debug=True)
