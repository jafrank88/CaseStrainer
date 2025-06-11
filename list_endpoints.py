from flask import Flask
import os
import sys

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the Flask app
from app_final_vue import create_app

app = create_app()

print("=" * 50)
print("AVAILABLE ROUTES:")
print("=" * 50)
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods))
    print(f"{methods:8} {rule.endpoint:40} {rule.rule}")
print("=" * 50)
