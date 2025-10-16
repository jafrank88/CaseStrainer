#!/usr/bin/env python3
"""
Simple startup script for CaseStrainer backend
"""
import sys
import os

# Add the parent directory to Python path so 'src' is importable
sys.path.insert(0, os.path.abspath('.'))

from src.app_final_vue import app

if __name__ == '__main__':
    import waitress
    waitress.serve(app, host='0.0.0.0', port=5000, threads=2) 