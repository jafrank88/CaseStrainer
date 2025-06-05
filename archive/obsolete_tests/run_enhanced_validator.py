#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Validator Runner

This script ensures all the necessary modules are properly imported
for the Enhanced Citation Validator to work correctly.
"""

import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# Function to check and import a module
def ensure_module_imported(module_name):
    try:
        # Try to import the module
        __import__(module_name)
        print(f"✓ Successfully imported {module_name}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return False


# Check and import required modules
required_modules = [
    "citation_correction",
    "citation_classifier",
    "enhanced_citation_verifier",
]

all_modules_imported = True
for module_name in required_modules:
    if not ensure_module_imported(module_name):
        all_modules_imported = False

if not all_modules_imported:
    print("\nWarning: Some required modules could not be imported.")
    print("The Enhanced Validator may not function correctly.")
else:
    print("\nAll required modules successfully imported!")

# Import and run the Flask application
print("\nStarting the Enhanced Validator...")
import app_final

# Run the Flask application
if __name__ == "__main__":
    # Check if the app has a run method (Flask app)
    if hasattr(app_final, "app") and hasattr(app_final.app, "run"):
        app_final.app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        print("Error: Could not find Flask application in app_final.py")
