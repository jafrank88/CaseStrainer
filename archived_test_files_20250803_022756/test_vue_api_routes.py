"""
Test script to verify Vue API blueprint routes
"""
import sys
import os
from flask import Flask

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the Vue API blueprint
try:
    print("=== TESTING VUE API BLUEPRINT ROUTES ===\n")
    
    # Create a test Flask app
    app = Flask(__name__)
    
    # Import the Vue API blueprint
    print("1. Importing Vue API blueprint...")
    from src.vue_api_endpoints import vue_api
    print(f"   ✅ Successfully imported: {vue_api}")
    
    # Register the blueprint with the test app
    print("\n2. Registering Vue API blueprint with test app...")
    app.register_blueprint(vue_api, url_prefix='/casestrainer/api')
    print("   ✅ Successfully registered Vue API blueprint")
    
    # Print registered blueprints
    print("\n3. Registered Blueprints:")
    for name, bp in app.blueprints.items():
        print(f"   - {name}: {bp}")
    
    # Print registered routes
    print("\n4. Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"   - {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
    
    # Check if the health endpoint is registered
    health_route = next((r for r in app.url_map.iter_rules() if 'health' in r.rule), None)
    if health_route:
        print(f"\n✅ Health endpoint found: {health_route.rule}")
        print(f"   - Endpoint: {health_route.endpoint}")
        print(f"   - Methods: {', '.join(health_route.methods)}")
    else:
        print("\n❌ Health endpoint not found in registered routes")
    
    print("\nTest completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
