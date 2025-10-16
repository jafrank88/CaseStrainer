#!/usr/bin/env python3
"""
Test if the worker function can be imported
"""
import sys
sys.path.insert(0, '/app/src')

print("Testing worker function import...")

try:
    from src.progress_manager import process_citation_task_direct
    print("✓ Function imported successfully!")
    print(f"  Function: {process_citation_task_direct}")
    print(f"  Module: {process_citation_task_direct.__module__}")
    
    # Try calling it with test data
    print("\nTesting function call...")
    result = process_citation_task_direct(
        'test-123',
        'text',
        {'text': 'Test citation: 123 Wn.2d 456'}
    )
    print(f"✓ Function executed!")
    print(f"  Result type: {type(result)}")
    print(f"  Success: {result.get('success') if isinstance(result, dict) else 'N/A'}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
