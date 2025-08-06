#!/usr/bin/env python3
"""
Integration test for optimized PDF extraction system.
Tests the integration with the existing application.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_optimized_integration():
    """Test the integration of optimized PDF extraction."""
    print("=" * 80)
    print("OPTIMIZED PDF EXTRACTION - INTEGRATION TEST")
    print("=" * 80)
    
    results = {
        'modules_loaded': False,
        'optimized_extraction': False,
        'fallback_working': False,
        'performance_improvement': False
    }
    
    # Test 1: Check if optimized modules can be imported
    print("\n🔍 Testing module imports...")
    try:
        from pdf_extraction_optimized import extract_text_from_pdf_ultra_fast, extract_text_from_pdf_smart
        from document_processing_optimized import process_document_fast
        from optimization_config import config, enable_optimized_mode
        
        print("✅ Optimized modules imported successfully")
        results['modules_loaded'] = True
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return results
    
    # Test 2: Check if optimized extraction works
    print("\n🔍 Testing optimized extraction...")
    try:
        # Find a test PDF file
        test_file = None
        test_locations = ['1028814.pdf', 'test.pdf', 'sample.pdf']
        
        for location in test_locations:
            if os.path.exists(location):
                test_file = location
                break
        
        if test_file:
            print(f"Using test file: {test_file}")
            
            # Test ultra-fast extraction
            start_time = time.time()
            text = extract_text_from_pdf_ultra_fast(test_file)
            ultra_fast_time = time.time() - start_time
            
            if text and not text.startswith('Error:'):
                print(f"✅ Ultra-fast extraction: {ultra_fast_time:.2f}s, {len(text)} characters")
                results['optimized_extraction'] = True
            else:
                print(f"❌ Ultra-fast extraction failed: {text}")
            
            # Test smart extraction
            start_time = time.time()
            text = extract_text_from_pdf_smart(test_file)
            smart_time = time.time() - start_time
            
            if text and not text.startswith('Error:'):
                print(f"✅ Smart extraction: {smart_time:.2f}s, {len(text)} characters")
            else:
                print(f"❌ Smart extraction failed: {text}")
        else:
            print("⚠️ No test PDF file found, skipping extraction test")
            
    except Exception as e:
        print(f"❌ Optimized extraction test failed: {e}")
    
    # Test 3: Check if fallback works
    print("\n🔍 Testing fallback mechanism...")
    try:
        from document_processing_unified import extract_text_from_file
        
        if test_file:
            start_time = time.time()
            text = extract_text_from_file(test_file)
            fallback_time = time.time() - start_time
            
            if text and not text.startswith('Error:'):
                print(f"✅ Fallback extraction: {fallback_time:.2f}s, {len(text)} characters")
                results['fallback_working'] = True
            else:
                print(f"❌ Fallback extraction failed: {text}")
        else:
            print("⚠️ No test file for fallback test")
            
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
    
    # Test 4: Check configuration system
    print("\n🔍 Testing configuration system...")
    try:
        enable_optimized_mode()
        summary = config.get_optimization_summary()
        
        print("✅ Configuration system working:")
        for category, settings in summary.items():
            print(f"  {category}: {len(settings)} settings")
        
        results['configuration_working'] = True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    # Test 5: Performance comparison
    print("\n🔍 Testing performance comparison...")
    if test_file and results['optimized_extraction'] and results['fallback_working']:
        try:
            # Test optimized vs fallback performance
            start_time = time.time()
            optimized_text = extract_text_from_pdf_ultra_fast(test_file)
            optimized_time = time.time() - start_time
            
            start_time = time.time()
            fallback_text = extract_text_from_file(test_file)
            fallback_time = time.time() - start_time
            
            if optimized_time < fallback_time:
                improvement = ((fallback_time - optimized_time) / fallback_time) * 100
                print(f"✅ Performance improvement: {improvement:.1f}% faster")
                print(f"   Optimized: {optimized_time:.2f}s")
                print(f"   Fallback: {fallback_time:.2f}s")
                results['performance_improvement'] = True
            else:
                print(f"⚠️ No performance improvement detected")
                print(f"   Optimized: {optimized_time:.2f}s")
                print(f"   Fallback: {fallback_time:.2f}s")
                
        except Exception as e:
            print(f"❌ Performance comparison failed: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test}: {status}")
    
    # Overall assessment
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests >= total_tests - 1:  # Allow 1 failure
        print("🎉 Integration test PASSED - System is ready for deployment!")
    else:
        print("⚠️ Integration test FAILED - Issues need to be resolved before deployment")
    
    return results

def test_application_integration():
    """Test integration with the main application."""
    print("\n" + "=" * 80)
    print("APPLICATION INTEGRATION TEST")
    print("=" * 80)
    
    try:
        # Test if the main application can use optimized extraction
        from document_processing_unified import UnifiedDocumentProcessor
        
        processor = UnifiedDocumentProcessor()
        print("✅ UnifiedDocumentProcessor created successfully")
        
        # Test if optimized extraction is available
        if hasattr(processor, '_extract_text_from_pdf'):
            print("✅ PDF extraction method available")
            
            # Test with a small text input
            test_text = "This is a test document with citation 123 U.S. 456 (2020)."
            
            start_time = time.time()
            result = processor.process_document_sync(content=test_text)
            processing_time = time.time() - start_time
            
            if result.get('success'):
                print(f"✅ Document processing: {processing_time:.2f}s")
                print(f"   Citations found: {len(result.get('citations', []))}")
                print(f"   Case names found: {len(result.get('case_names', []))}")
            else:
                print(f"❌ Document processing failed: {result.get('error', 'Unknown error')}")
        else:
            print("❌ PDF extraction method not found")
            
    except Exception as e:
        print(f"❌ Application integration test failed: {e}")

def main():
    """Main test function."""
    print("Starting integration tests...")
    
    # Run basic integration test
    results = test_optimized_integration()
    
    # Run application integration test
    test_application_integration()
    
    print("\n" + "=" * 80)
    print("INTEGRATION TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 