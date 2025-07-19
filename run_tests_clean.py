#!/usr/bin/env python3
"""
Script to run tests with clean logging (no pdfminer debug spam)
"""

import logging
import sys
import pytest

# Suppress pdfminer debug logging
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('pdfminer.psparser').setLevel(logging.WARNING)
logging.getLogger('pdfminer.pdfinterp').setLevel(logging.WARNING)
logging.getLogger('pdfminer.cmapdb').setLevel(logging.WARNING)

# Suppress other noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

if __name__ == "__main__":
    # Run pytest with clean output
    sys.exit(pytest.main([
        '-v',
        '--maxfail=5', 
        '--disable-warnings',
        '--tb=short',
        '--log-cli-level=WARNING'
    ])) 