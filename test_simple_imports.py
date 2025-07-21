#!/usr/bin/env python3
"""
Simple import test to verify basic functionality after consolidation.
"""

def test_basic_imports():
    """Test basic imports that should work without any external dependencies."""
    try:
        # Test config import
        from src.config import get_config_value
        print("✅ src.config imported successfully")
        
        # Test citation utils import
        from src.citation_utils_consolidated import normalize_citation
        print("✅ src.citation_utils_consolidated imported successfully")
        
        # Test case name extraction core import
        from src.case_name_extraction_core import CaseNameExtractor
        print("✅ src.case_name_extraction_core imported successfully")
        
        # Test unified processor import
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        print("✅ src.unified_citation_processor_v2 imported successfully")
        
        # Test that we can create instances
        extractor = CaseNameExtractor()
        print("✅ CaseNameExtractor instance created successfully")
        
        processor = UnifiedCitationProcessorV2()
        print("✅ UnifiedCitationProcessorV2 instance created successfully")
        
        # Test basic functionality
        result = normalize_citation("123 Wn. 2d 456")
        print(f"✅ Citation normalization works: {result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing basic imports...")
    success = test_basic_imports()
    if success:
        print("\n✅ All basic imports successful!")
    else:
        print("\n❌ Some imports failed!")
        exit(1) 