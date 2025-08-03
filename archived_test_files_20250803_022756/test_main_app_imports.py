"""
Test script to check import paths and module resolution in the main application context
"""
import os
import sys
import logging
import traceback
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports_in_app_context():
    """Test imports in the context of the main application"""
    print("=== TESTING IMPORTS IN MAIN APPLICATION CONTEXT ===\n")
    
    # Print environment information
    print("1. ENVIRONMENT INFORMATION:")
    print(f"   Python Executable: {sys.executable}")
    print(f"   Python Version: {sys.version}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Python Path:\n     - " + "\n     - ".join(sys.path))
    
    # Try to import the main application
    print("\n2. ATTEMPTING TO IMPORT MAIN APPLICATION:")
    try:
        # Import the application factory
        print("   Importing ApplicationFactory...")
        from src.app_final_vue import ApplicationFactory
        print("   ✅ Successfully imported ApplicationFactory")
        
        # Create an application instance
        print("\n3. CREATING APPLICATION INSTANCE:")
        try:
            app_factory = ApplicationFactory()
            app = app_factory.create_app()
            print("   ✅ Successfully created application instance")
            
            # Check registered blueprints
            print("\n4. CHECKING REGISTERED BLUEPRINTS:")
            if hasattr(app, 'blueprints'):
                for name, bp in app.blueprints.items():
                    print(f"   - {name}: {bp}")
                    print(f"     - URL Prefix: {getattr(bp, 'url_prefix', 'N/A')}")
            else:
                print("   No blueprints registered!")
            
            # Check registered routes
            print("\n5. CHECKING REGISTERED ROUTES:")
            for rule in app.url_map.iter_rules():
                print(f"   - {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
            
            # Try to access the health endpoint
            print("\n6. TESTING HEALTH ENDPOINT:")
            with app.test_client() as client:
                response = client.get('/casestrainer/api/health')
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)[:200]}...")
                
                # Check if this is the Vue API or debug API
                if "Vue API" in response.get_data(as_text=True):
                    print("   ✅ Vue API is responding")
                elif "Debug API" in response.get_data(as_text=True):
                    print("   ⚠️  Debug API is responding instead of Vue API")
                else:
                    print("   ❓ Unknown API response")
            
        except Exception as e:
            print(f"   ❌ Error creating application instance: {e}")
            traceback.print_exc()
            
    except ImportError as e:
        print(f"   ❌ Failed to import ApplicationFactory: {e}")
        traceback.print_exc()
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_imports_in_app_context()
