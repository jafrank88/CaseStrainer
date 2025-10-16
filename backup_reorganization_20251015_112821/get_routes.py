from flask import Flask
import os
import sys

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    # Try to import the app factory function
    from app_final_vue import create_app
    
    # Create the Flask app
    app = create_app()
    
    # Print all routes
    print("=" * 80)
    print(f"{'ENDPOINT':<60} {'METHODS'}")
    print("=" * 80)
    
    # Collect all routes
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        routes.append((rule.endpoint, rule.rule, methods))
    
    # Sort routes by endpoint name
    for endpoint, rule, methods in sorted(routes, key=lambda x: x[0]):
        print(f"{endpoint:<60} {methods:10} {rule}")
    
    print("\nNote: The API is mounted at /casestrainer/api/")
    print("Example endpoints:")
    print("  GET  /casestrainer/api/version")
    print('  POST /casestrainer/api/analyze -d {\"text\":\"Sample text with citation 534 F.3d 1290\"}')
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
