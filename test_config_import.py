#!/usr/bin/env python
"""Test config import"""
try:
    from src.config import DEFAULT_REQUEST_TIMEOUT
    print(f"✅ DEFAULT_REQUEST_TIMEOUT = {DEFAULT_REQUEST_TIMEOUT}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
