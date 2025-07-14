#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import sys
import os

# Add src to sys.path for local script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

print("Python path:")
for path in sys.path:
    print(f"  {path}")

print("\nTesting imports...")

try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2, CitationResult
    print("✅ Successfully imported UnifiedCitationProcessorV2 and CitationResult")
    
    # Test instantiation
    processor = UnifiedCitationProcessorV2()
    print("✅ Successfully created UnifiedCitationProcessorV2 instance")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    
    # Check if file exists
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    target_file = os.path.join(src_path, 'unified_citation_processor_v2.py')
    print(f"Target file path: {target_file}")
    print(f"File exists: {os.path.exists(target_file)}")
    
    # List files in src directory
    if os.path.exists(src_path):
        print("Files in src directory:")
        for file in os.listdir(src_path):
            if file.endswith('.py'):
                print(f"  {file}")

except Exception as e:
    print(f"❌ Unexpected error: {e}") 