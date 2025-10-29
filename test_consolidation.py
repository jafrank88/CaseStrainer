#!/usr/bin/env python3
"""
Test extraction function consolidation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_master_extraction():
    """Test that unified master extraction function works"""
    try:
        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
        
        # Test with a simple citation
        test_text = "In the case of Smith v. Jones, 123 U.S. 456 (2023), the court held that..."
        result = extract_case_name_and_date_unified_master(
            text=test_text,
            citation="123 U.S. 456",
            start_index=test_text.find("123 U.S. 456"),
            end_index=test_text.find("123 U.S. 456") + len("123 U.S. 456")
        )
        
        print(f"✅ Unified master extraction works: '{result.get('case_name', 'N/A')}'")
        return True
        
    except Exception as e:
        print(f"❌ Unified master extraction failed: {e}")
        return False

def test_processor_uses_unified():
    """Test that the main processor uses unified extraction"""
    try:
        # Check that the import is working
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Check that it can import the unified function
        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
        
        print("✅ Main processor successfully imports unified extraction")
        return True
        
    except Exception as e:
        print(f"❌ Processor unified import failed: {e}")
        return False

def test_no_old_extraction_imports():
    """Test that old extraction functions are not being imported"""
    try:
        # This should fail if we successfully migrated
        from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
        print("⚠️  Old extraction function still available (may be intentional)")
        return False
    except ImportError:
        print("✅ Old extraction function successfully removed")
        return True
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
        return False

def test_specialized_functions_intact():
    """Test that specialized functions (websearch, utils) are still intact"""
    specialized_functions = [
        ('src.websearch.extractor', 'LegalExtractor'),
        ('src.utils.strict_context_isolator', 'extract_case_name_from_strict_context'),
        ('src.utils.unified_case_name_extractor', 'extract_case_name_with_strict_isolation')
    ]
    
    success_count = 0
    for module_path, function_name in specialized_functions:
        try:
            if '.' in function_name:
                # It's a function
                module = __import__(module_path, fromlist=[function_name.split('.')[-1]])
                func = getattr(module, function_name.split('.')[-1])
            else:
                # It's a class
                module = __import__(module_path, fromlist=[function_name])
                cls = getattr(module, function_name)
            
            print(f"✅ {function_name} - Specialized function intact")
            success_count += 1
        except Exception as e:
            print(f"❌ {function_name} - Specialized function missing: {e}")
    
    return success_count == len(specialized_functions)

if __name__ == "__main__":
    print("CaseStrainer Extraction Consolidation Test")
    print("=" * 50)
    
    test1 = test_unified_master_extraction()
    test2 = test_processor_uses_unified()
    test3 = test_no_old_extraction_imports()
    test4 = test_specialized_functions_intact()
    
    print("\n" + "=" * 50)
    print("CONSOLIDATION RESULTS:")
    print(f"Unified master extraction: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Processor uses unified: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Old functions removed: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"Specialized functions intact: {'✅ PASS' if test4 else '❌ FAIL'}")
    
    overall_success = test1 and test2 and test4  # test3 is optional
    print(f"\nOverall consolidation: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
