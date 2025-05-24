#!/usr/bin/env python
"""
Simple script to start the CaseStrainer Vue.js frontend
Uses the same approach as run_production.py
"""
import os
import sys
import subprocess
import argparse


def main():
    """Start the CaseStrainer Vue.js frontend."""
    print("Starting CaseStrainer Vue.js frontend...")

    # Get configuration from command line arguments
    parser = argparse.ArgumentParser(description="Run CaseStrainer Vue.js frontend")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the server on (default: 5000)",
    )
    args = parser.parse_args()

    # Set environment variables
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)

    # Get the path to the app_final_vue.py file
    app_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "app_final_vue.py"
    )
    print(f"Starting application from: {app_path}")

    # Execute the app_final_vue.py file directly using the current Python executable
    try:
        subprocess.call(
            [sys.executable, app_path, "--host", args.host, "--port", str(args.port)]
        )
    except Exception as e:
        print(f"Error starting application: {e}")


if __name__ == "__main__":
    main()
