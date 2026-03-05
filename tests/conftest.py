"""
Pytest configuration and shared fixtures for CaseStrainer tests.
"""

import sys
import os

# Ensure project root is on path so "src" imports work
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
