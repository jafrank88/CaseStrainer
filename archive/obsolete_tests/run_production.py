#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CaseStrainer Production Runner

This script ensures proper startup of CaseStrainer with the Enhanced Validator
in the production environment.
"""

import os
import sys
import argparse
import traceback

# Parse command line arguments
parser = argparse.ArgumentParser(description="Run CaseStrainer in production mode")
parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
args = parser.parse_args()

# Set environment variables for app_final.py
os.environ["HOST"] = args.host
os.environ["PORT"] = str(args.port)
os.environ["USE_CHEROOT"] = "True"

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Starting CaseStrainer on {args.host}:{args.port}...")

# Try to import the app_final module
try:
    import app_final

    # Check if the app has a run method (Flask app)
    if hasattr(app_final, "app") and hasattr(app_final.app, "run"):
        # Add the Enhanced Validator route to the app_final app
        @app_final.app.route("/enhanced-validator")
        @app_final.app.route("/casestrainer/enhanced-validator")
        def enhanced_validator():
            """
            Display the Enhanced Citation Validator page.
            This provides a comprehensive interface for validating citations with multiple sources,
            displaying detailed citation information, and suggesting corrections.
            """
            return app_final.render_template("enhanced_validator.html")

        print("Enhanced Validator route added to app_final.app")

        # Run the Flask application
        app_final.app.run(host=args.host, port=args.port, debug=False)
    else:
        print("Error: Could not find Flask application in app_final.py")
        sys.exit(1)
except ImportError as e:
    print(f"Error importing app_final: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"Error starting CaseStrainer: {e}")
    traceback.print_exc()
    sys.exit(1)
