#!/usr/bin/env python3
"""
RQ Worker for Linux/Docker environments
This script starts an RQ worker for the CaseStrainer application
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if __name__ == '__main__':
    # Import and run RQ worker
    from rq.cli import main
    main() 