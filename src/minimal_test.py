"""Minimal test script to check Flask app initialization."""

import sys
import os
from flask import Flask

print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("\nTrying to import create_app...")

try:
    from app_final_vue import create_app

    print("Successfully imported create_app")

    print("\nCreating app...")
    app = create_app()
    print("App created successfully")

    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

except Exception as e:
    print("\nError:", str(e))
    import traceback

    traceback.print_exc()
