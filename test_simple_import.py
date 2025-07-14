#!/usr/bin/env python3
"""
Simple test to verify imports work correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def test_imports():
    """Test that all critical imports work."""
    try:
        # Test the main processor import
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        print("✅ Successfully imported UnifiedCitationProcessorV2")
        
        # Test creating an instance
        config = ProcessingConfig(debug_mode=True)
        processor = UnifiedCitationProcessorV2(config)
        print("✅ Successfully created UnifiedCitationProcessorV2 instance")
        
        # Test basic functionality
        test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)"
        results = processor.process_text(test_text)
        print(f"✅ Successfully processed text, found {len(results)} citations")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 All import tests passed!")
    else:
        print("\n💥 Import tests failed!")
        sys.exit(1) 