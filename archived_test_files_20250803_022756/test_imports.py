"""
Test script to verify imports and blueprint registration
"""
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    print("=== TESTING VUE API IMPORT ===")
    from src.vue_api_endpoints import vue_api
    print("✅ Successfully imported vue_api from src.vue_api_endpoints")
    print(f"vue_api name: {vue_api.name}")
    print(f"vue_api url_prefix: {getattr(vue_api, 'url_prefix', 'Not set')}")
    print(f"vue_api template_folder: {getattr(vue_api, 'template_folder', 'Not set')}")
    print("\nAvailable routes:")
    for rule in vue_api.url_map.iter_rules():
        print(f"- {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
except Exception as e:
    print(f"❌ Error importing vue_api: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n=== TESTING BLUEPRINTS IMPORT ===")
    from src.api.blueprints import register_blueprints
    print("✅ Successfully imported register_blueprints from src.api.blueprints")
    
    # Test creating a minimal Flask app
    from flask import Flask
    app = Flask(__name__)
    print("\n=== REGISTERING BLUEPRINTS ===")
    app = register_blueprints(app)
    
    print("\nRegistered blueprints:")
    for name, blueprint in app.blueprints.items():
        print(f"- {name}: {blueprint}")
    
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"- {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
    
except Exception as e:
    print(f"❌ Error testing blueprints: {e}")
    import traceback
    traceback.print_exc()
