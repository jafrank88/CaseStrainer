#!/usr/bin/env python3
"""
WSGI entry point for CaseStrainer web application.
This file is used by Gunicorn to run the Flask app.
"""

from app import app

if __name__ == "__main__":
    app.run()
