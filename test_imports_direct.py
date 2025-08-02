"""
Test script to verify direct imports and module resolution for the Vue API
"""
import os
import sys
import importlib
import traceback
from pathlib import Path

def test_imports():
    """Test all relevant imports and module paths"""
    print("=== TESTING IMPORTS AND MODULE RESOLUTION ===\n")
    
    # Print environment information
    print("1. ENVIRONMENT INFORMATION:")
    print(f"   Python Executable: {sys.executable}")
    print(f"   Python Version: {sys.version}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Python Path:\n     - " + "\n     - ".join(sys.path))
    
    # Test importing the Vue API blueprint directly
    print("\n2. TESTING VUE API BLUEPRINT IMPORT:")
    try:
        # Try absolute import first
        print("   Attempting absolute import: from src.vue_api_endpoints import vue_api")
        from src.vue_api_endpoints import vue_api
        print(f"   ✅ Success! Blueprint: {vue_api}")
        print(f"   - Name: {vue_api.name}")
        print(f"   - Import Name: {vue_api.import_name}")
        print(f"   - File: {os.path.abspath(sys.modules[vue_api.import_name].__file__)}")
    except ImportError as e:
        print(f"   ❌ Absolute import failed: {e}")
        traceback.print_exc()
        
        # Try relative import
        try:
            print("\n   Attempting relative import: from ..vue_api_endpoints import vue_api")
            sys.path.insert(0, os.path.abspath('.'))
            from vue_api_endpoints import vue_api
            print(f"   ✅ Success! Blueprint: {vue_api}")
            print(f"   - Name: {vue_api.name}")
            print(f"   - Import Name: {vue_api.import_name}")
            print(f"   - File: {os.path.abspath(sys.modules[vue_api.import_name].__file__)}")
        except ImportError as e2:
            print(f"   ❌ Relative import failed: {e2}")
            traceback.print_exc()
    
    # Test importing the blueprints module
    print("\n3. TESTING BLUEPRINTS MODULE IMPORT:")
    try:
        print("   Attempting to import blueprints module...")
        import src.api.blueprints as blueprints
        print(f"   ✅ Success! Module: {blueprints.__file__}")
        
        # Test the register_blueprints function
        print("\n4. TESTING REGISTER_BLUEPRINTS FUNCTION:")
        try:
            from flask import Flask
            test_app = Flask(__name__)
            print("   Created test Flask app")
            
            # Call register_blueprints
            print("   Calling register_blueprints...")
            result = blueprints.register_blueprints(test_app)
            print(f"   ✅ register_blueprints completed. Result: {result is not None}")
            
            # Check if blueprints were registered
            print("\n   REGISTERED BLUEPRINTS:")
            if hasattr(test_app, 'blueprints'):
                for name, bp in test_app.blueprints.items():
                    print(f"   - {name}: {bp}")
                    print(f"     - URL Prefix: {getattr(bp, 'url_prefix', 'N/A')}")
            else:
                print("   No blueprints registered!")
            
            # Check registered routes
            print("\n   REGISTERED ROUTES:")
            for rule in test_app.url_map.iter_rules():
                print(f"   - {rule.endpoint}: {rule.rule} ({', '.join(rule.methods)})")
            
        except Exception as e:
            print(f"   ❌ Error testing register_blueprints: {e}")
            traceback.print_exc()
            
    except ImportError as e:
        print(f"   ❌ Failed to import blueprints module: {e}")
        traceback.print_exc()
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_imports()
