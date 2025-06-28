#!/usr/bin/env python3
"""
Simple test to identify issues with the unified processor.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    print("Testing imports...")
    from src.unified_citation_processor import UnifiedCitationProcessor, TextCleaner, DateExtractor
    print("✓ All imports successful")
    
    print("\nTesting TextCleaner...")
    test_text = "This   has   extra   spaces"
    cleaned = TextCleaner.clean_text(test_text)
    print(f"✓ Text cleaning works: '{cleaned}'")
    
    print("\nTesting DateExtractor...")
    test_text = "The court decided in 2024. See Smith v. Jones, 123 Wn. App. 456."
    date = DateExtractor.extract_date_from_context(test_text, 50, 65)
    print(f"✓ Date extraction works: {date}")
    
    print("\nTesting UnifiedCitationProcessor initialization...")
    processor = UnifiedCitationProcessor()
    print("✓ Processor initialized successfully")
    
    print("\nTesting basic citation extraction...")
    test_text = "See Smith v. Jones, 123 Wn. App. 456."
    result = processor.process_text(test_text)
    print(f"✓ Processing completed: {result['summary']}")
    
    print("\nAll tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
