#!/usr/bin/env python3
"""
Startup script for RQ worker with proper Python path configuration
"""
import os
import sys

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now import and run the worker
from rq_worker import main

if __name__ == '__main__':
    print(f"Python path: {sys.path}")
    print("Starting RQ worker...")
    main()
