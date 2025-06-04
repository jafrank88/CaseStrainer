"""
Simple script to check Flask app initialization and routes.
"""

import os
import sys
from flask import Flask


def print_environment():
    print("\n=== Environment ===")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Path: {sys.path}")


def check_flask_app():
    print("\n=== Checking Flask App ===")
    try:
        from app_final_vue import create_app

        print("Creating Flask app...")
        app = create_app()

        print("\n=== Registered Routes ===")
        with app.app_context():
            for rule in app.url_map.iter_rules():
                methods = list(rule.methods)
                if "HEAD" in methods:
                    methods.remove("HEAD")
                if "OPTIONS" in methods:
                    methods.remove("OPTIONS")
                print(f"{rule.rule} -> {rule.endpoint} [{', '.join(methods)}]")

        # Check blueprints
        print("\n=== Registered Blueprints ===")
        for name, bp in app.blueprints.items():
            print(f"- {name}: {bp}")

    except Exception as e:
        print(f"\n!!! Error creating Flask app: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print_environment()
    check_flask_app()
