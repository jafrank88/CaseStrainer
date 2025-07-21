#!/usr/bin/env python3
"""
Simple import test script to verify all modules can be imported correctly
after the consolidation work.
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    # Test basic imports
    try:
        from src.config import get_config_value
        print("✅ src.config imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import src.config: {e}")
        return False
    
    try:
        from src.citation_utils_consolidated import normalize_citation
        print("✅ src.citation_utils_consolidated imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import src.citation_utils_consolidated: {e}")
        return False
    
    try:
        from src.toa_utils_consolidated import extract_table_of_authorities
        print("✅ src.toa_utils_consolidated imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import src.toa_utils_consolidated: {e}")
        return False
    
    try:
        from src.test_utilities_consolidated import create_test_citation
        print("✅ src.test_utilities_consolidated imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import src.test_utilities_consolidated: {e}")
        return False
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        print("✅ src.unified_citation_processor_v2 imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import src.unified_citation_processor_v2: {e}")
        return False
    
    try:
        from src.case_name_extraction_core import extract_case_name_triple_comprehensive
        print("✅ src.case_name_extraction_core imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import src.case_name_extraction_core: {e}")
        return False
    
    # Test that deprecated modules are properly marked
    try:
        import src.citation_verification
        print("⚠️  src.citation_verification imported (deprecated)")
    except ImportError as e:
        print(f"❌ Failed to import src.citation_verification: {e}")
    
    try:
        import src.websearch_utils
        print("⚠️  src.websearch_utils imported (deprecated)")
    except ImportError as e:
        print(f"❌ Failed to import src.websearch_utils: {e}")
    
    print("\n✅ All critical imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 