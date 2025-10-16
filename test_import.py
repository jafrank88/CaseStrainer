#!/usr/bin/env python
"""Test UnifiedInputProcessor import"""
try:
    from src.unified_input_processor import UnifiedInputProcessor
    print("✅ Import successful")
    print(f"✅ Class: {UnifiedInputProcessor}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
