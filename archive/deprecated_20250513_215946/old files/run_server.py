#!/usr/bin/env python3
"""
Script to run the CaseStrainer web application using Waitress.
This allows multiple users to use the site simultaneously.
"""

import argparse
from waitress import serve
from app import app


def run_server():
    """Run the CaseStrainer web application using Waitress."""
    parser = argparse.ArgumentParser(description="Run the CaseStrainer web application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to bind to")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads")

    args = parser.parse_args()

    print(f"Starting server on {args.host}:{args.port}")
    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == "__main__":
    run_server()
