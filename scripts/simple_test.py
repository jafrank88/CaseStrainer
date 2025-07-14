#!/usr/bin/env python3
"""
Simple test script to validate that the basic imports work.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_imports():
    """Test that basic imports work."""
    try:
        print("Testing basic imports...")
        
        # Test unified citation processor import
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        print("✓ UnifiedCitationProcessorV2 imported successfully")
        
        # Test file utils import
        from file_utils import extract_text_from_pdf
        print("✓ file_utils imported successfully")
        
        # Test case name extraction core
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        print("✓ case_name_extraction_core imported successfully")
        
        print("\nAll basic imports successful!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_processor_initialization():
    """Test that the processor can be initialized."""
    try:
        print("\nTesting processor initialization...")
        
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        processor = UnifiedCitationProcessorV2()
        print("✓ Processor initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Processor initialization failed: {e}")
        return False

def test_basic_text_processing():
    """Test basic text processing functionality."""
    try:
        print("\nTesting basic text processing...")
        
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Test text
        test_text = """
        A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        """
        
        processor = UnifiedCitationProcessorV2()
        result = processor.process_text(test_text)
        
        print(f"✓ Text processing successful, found {len(result)} citations")
        
        # Show first few citations
        for i, citation in enumerate(result[:3]):
            print(f"  Citation {i+1}: {citation.citation}")
        
        return True
        
    except Exception as e:
        print(f"✗ Text processing failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Simple Import and Functionality Test")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_processor_initialization,
        test_basic_text_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 