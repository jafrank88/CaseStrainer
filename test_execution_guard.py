#!/usr/bin/env python3
"""
Test Execution Guard
This file prevents test files from being executed in production
"""

import sys
import os

def block_test_execution():
    """Block test execution in production"""
    print("Test execution blocked in production environment")
    print("   Please run tests in a development environment")
    sys.exit(1)

# Check if we're in production
if os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production':
    block_test_execution()

# Check for test files in current directory
test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
if test_files:
    print(f"Test files detected: {test_files}")
    print("   Consider moving them to a test directory")
