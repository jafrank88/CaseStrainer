"""
Test script to verify debug API registration in the application
"""
import sys
import os
import importlib

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_debug_api_registration():
    """Test if the debug API is being registered in the application"""
    print("=== TESTING DEBUG API REGISTRATION ===\n")
    
    try:
        # Import the application factory
        print("1. Importing application factory...")
        from src.app_final_vue import ApplicationFactory
        print("   ✅ Successfully imported ApplicationFactory")
        
        # Create a test application
        print("\n2. Creating test application...")
        app_factory = ApplicationFactory()
        app = app_factory.create_app()
        print("   ✅ Successfully created test application")
        
        # Check registered blueprints
        print("\n3. Checking registered blueprints:")
        for name, bp in app.blueprints.items():
            print(f"   - {name}: {bp}")
            print(f"     - URL Prefix: {getattr(bp, 'url_prefix', 'N/A')}")
        
        # Check if debug API is registered
        debug_api_registered = any('debug_api' in name for name in app.blueprints.keys())
        if debug_api_registered:
            print("\n⚠️  WARNING: Debug API is registered in the application")
            print("   This should only happen if Vue API registration failed")
        else:
            print("\n✅ Debug API is not registered (this is good!)")
        
        # Check registered routes
        print("\n4. Checking registered routes:")
        health_routes = [r for r in app.url_map.iter_rules() if 'health' in r.rule]
        for route in health_routes:
            print(f"   - {route.endpoint}: {route.rule} ({', '.join(route.methods)})")
        
        # Check if debug API health endpoint is registered
        debug_health_route = any('debug_api' in r.endpoint for r in health_routes)
        if debug_health_route:
            print("\n⚠️  WARNING: Debug API health endpoint is registered")
            print("   This should only happen if Vue API registration failed")
        else:
            print("\n✅ Debug API health endpoint is not registered (this is good!)")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_api_registration()
