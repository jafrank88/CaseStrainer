"""
Test script to verify Vue API blueprint registration
"""
import os
import sys
import logging
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_blueprint_import():
    """Test importing the Vue API blueprint"""
    print("\n=== TESTING VUE API BLUEPRINT IMPORT ===")
    
    # Add project root to Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print(f"Python path: {sys.path}")
    
    # Try to import the blueprint
    try:
        print("\nAttempting to import vue_api from src.vue_api_endpoints")
        from src.vue_api_endpoints import vue_api
        print("✅ Successfully imported vue_api:")
        print(f"  - Name: {vue_api.name}")
        print(f"  - Import Name: {vue_api.import_name}")
        print(f"  - URL Prefix: {getattr(vue_api, 'url_prefix', 'Not set')}")
        return vue_api
    except ImportError as e:
        print(f"❌ Failed to import vue_api: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_blueprint_registration():
    """Test registering the Vue API blueprint with a Flask app"""
    print("\n=== TESTING BLUEPRINT REGISTRATION ===")
    
    # Create a test Flask app
    app = Flask(__name__)
    
    # Import the blueprint
    vue_api = test_blueprint_import()
    if not vue_api:
        print("❌ Cannot test registration - failed to import blueprint")
        return
    
    # Register the blueprint
    try:
        print("\nRegistering blueprint with URL prefix '/casestrainer/api'")
        app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
        
        # Print registered blueprints
        print("\nRegistered Blueprints:")
        for name, bp in app.blueprints.items():
            print(f"- {name}: {bp}")
            print(f"  - URL Prefix: {getattr(bp, 'url_prefix', 'Not set')}")
        
        # Print registered routes
        print("\nRegistered Routes:")
        for rule in app.url_map.iter_rules():
            print(f"- {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
        
        return app
        
    except Exception as e:
        print(f"❌ Error registering blueprint: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=== VUE API BLUEPRINT TEST ===\n")
    
    # Test blueprint import and registration
    test_app = test_blueprint_registration()
    
    if test_app:
        print("\n✅ Vue API blueprint test completed successfully")
    else:
        print("\n❌ Vue API blueprint test failed")
