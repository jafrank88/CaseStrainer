#!/usr/bin/env python3
"""
Test if deprecated module imports are properly cleaned up
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_deprecated_imports_removed():
    """Test that deprecated modules can no longer be imported"""
    deprecated_modules = [
        'src.unified_sync_processor',
        'src.enhanced_fallback_verifier', 
        'src.deprecated_extraction_functions',
        'src.enhanced_courtlistener_verification'
    ]
    
    print("Testing that deprecated modules are removed...")
    for module in deprecated_modules:
        try:
            __import__(module)
            print(f"❌ {module} - Still exists (should be removed)")
            return False
        except ImportError:
            print(f"✅ {module} - Successfully removed")
        except Exception as e:
            print(f"⚠️  {module} - Error: {e}")
    
    return True

def test_backup_files_removed():
    """Test that backup files are removed"""
    backup_files = [
        'src/progress_manager.py.backup_20251014_183300',
        'src/unified_input_processor.py.backup_20251014_182424',
        'src/vue_api_endpoints.py.backup_20251014_182424'
    ]
    
    print("\nTesting that backup files are removed...")
    for backup_file in backup_files:
        full_path = os.path.join(os.path.dirname(__file__), backup_file)
        if os.path.exists(full_path):
            print(f"❌ {backup_file} - Still exists (should be removed)")
            return False
        else:
            print(f"✅ {backup_file} - Successfully removed")
    
    return True

def test_remaining_imports():
    """Test that remaining modules still work"""
    key_modules = [
        'src.unified_verification_master',
        'src.unified_case_name_extractor_v2',
        'src.citation_extraction_endpoint'
    ]
    
    print("\nTesting that key modules still work...")
    success_count = 0
    for module in key_modules:
        try:
            __import__(module)
            print(f"✅ {module} - Imports successfully")
            success_count += 1
        except Exception as e:
            print(f"❌ {module} - Import failed: {e}")
    
    return success_count == len(key_modules)

if __name__ == "__main__":
    print("CaseStrainer Refactoring Cleanup Test")
    print("=" * 50)
    
    test1 = test_deprecated_imports_removed()
    test2 = test_backup_files_removed() 
    test3 = test_remaining_imports()
    
    print("\n" + "=" * 50)
    print("CLEANUP RESULTS:")
    print(f"Deprecated modules removed: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Backup files removed: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Key modules working: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    overall_success = test1 and test2 and test3
    print(f"\nOverall cleanup: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
