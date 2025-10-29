#!/usr/bin/env python3
"""
Test imports after refactoring cleanup
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_main_imports():
    """Test main application imports"""
    try:
        import src.app_final_vue
        print("✅ Main app imports successfully")
        return True
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False

def test_key_modules():
    """Test key module imports"""
    modules_to_test = [
        'src.unified_citation_processor_v2',
        'src.unified_verification_master', 
        'src.unified_case_name_extractor_v2',
        'src.citation_extraction_endpoint',
        'src.vue_api_endpoints_updated'
    ]
    
    results = {}
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} imports successfully")
            results[module] = True
        except Exception as e:
            print(f"❌ {module} import failed: {e}")
            results[module] = False
    
    return results

if __name__ == "__main__":
    print("Testing imports after refactoring cleanup...")
    print("=" * 50)
    
    main_success = test_main_imports()
    module_results = test_key_modules()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Main app: {'✅ PASS' if main_success else '❌ FAIL'}")
    
    failed_modules = [mod for mod, success in module_results.items() if not success]
    if failed_modules:
        print(f"Failed modules: {len(failed_modules)}")
        for module in failed_modules:
            print(f"  - {module}")
    else:
        print("All key modules: ✅ PASS")
    
    overall_success = main_success and all(module_results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASS' if overall_success else '❌ SOME TESTS FAILED'}")
