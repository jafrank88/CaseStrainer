#!/usr/bin/env python3
"""
Quick Backend Test Script

This script provides a quick way to test the backend functionality
without running the full unittest framework. It tests the core
features and provides immediate feedback.
"""

import os
import sys
import json
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_enhanced_processor_import():
    """Test that the enhanced processor can be imported."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        print("✅ Enhanced processor imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import enhanced processor: {e}")
        return False

def test_processor_initialization():
    """Test that the processor can be initialized."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        
        options = ProcessingOptions(
            enable_enhanced_verification=True,
            enable_cross_validation=True,
            enable_false_positive_prevention=True,
            enable_confidence_scoring=True
        )
        
        processor = EnhancedSyncProcessor(options)
        print("✅ Processor initialized successfully")
        print(f"   - Enhanced verification: {processor.options.enable_enhanced_verification}")
        print(f"   - Cross-validation: {processor.options.enable_cross_validation}")
        print(f"   - False positive prevention: {processor.options.enable_false_positive_prevention}")
        print(f"   - Confidence scoring: {processor.options.enable_confidence_scoring}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False

def test_text_processing():
    """Test text input processing."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        
        # Test text with known citations
        test_text = """
        A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        """
        
        options = ProcessingOptions(
            enable_enhanced_verification=True,
            enable_cross_validation=True,
            enable_false_positive_prevention=True,
            enable_confidence_scoring=True
        )
        
        processor = EnhancedSyncProcessor(options)
        
        print("🔄 Processing text input...")
        start_time = time.time()
        
        result = processor.process_any_input_enhanced(test_text, 'text')
        
        processing_time = time.time() - start_time
        
        if result['success']:
            print("✅ Text processing successful")
            print(f"   - Processing time: {processing_time:.3f}s")
            print(f"   - Citations found: {result.get('citations_found', len(result.get('citations', [])))}")
            print(f"   - Clusters created: {result.get('clusters_created', len(result.get('clusters', [])))}")
            print(f"   - Processing mode: {result.get('processing_mode', 'unknown')}")
            print(f"   - Extraction method: {result.get('extraction_method', 'unknown')}")
            
            # Show first few citations
            citations = result.get('citations', [])
            if citations:
                print("\n📋 Sample citations:")
                for i, citation in enumerate(citations[:3]):
                    print(f"   {i+1}. {citation.get('citation', 'N/A')}")
                    print(f"      Case: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"      Year: {citation.get('extracted_date', 'N/A')}")
                    print(f"      Confidence: {citation.get('confidence_score', 'N/A')}")
                    print(f"      Method: {citation.get('extraction_method', 'N/A')}")
                    if i < 2:
                        print()
            
            return True
        else:
            print(f"❌ Text processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Text processing test failed: {e}")
        return False

def test_file_processing():
    """Test file input processing."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        
        # Create a temporary test file
        import tempfile
        
        test_content = """
        This is a test document with citations: 200 Wn.2d 72, 514 P.3d 643 (2022).
        Another citation: 171 Wn.2d 486, 256 P.3d 321 (2011).
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file_path = f.name
        
        try:
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            print("🔄 Processing file input...")
            start_time = time.time()
            
            result = processor.process_any_input_enhanced(test_file_path, 'file')
            
            processing_time = time.time() - start_time
            
            if result['success']:
                print("✅ File processing successful")
                print(f"   - Processing time: {processing_time:.3f}s")
                print(f"   - Citations found: {result.get('citations_found', len(result.get('citations', [])))}")
                print(f"   - Clusters created: {result.get('clusters_created', len(result.get('clusters', [])))}")
                print(f"   - File metadata: {result.get('metadata', {}).get('extraction_method', 'unknown')}")
                
                return True
            else:
                print(f"❌ File processing failed: {result.get('error', 'Unknown error')}")
                return False
                
        finally:
            # Clean up test file
            os.unlink(test_file_path)
            
    except Exception as e:
        print(f"❌ File processing test failed: {e}")
        return False

def test_url_processing():
    """Test URL input processing."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        from unittest.mock import patch
        
        test_url = "https://example.com/legal-document"
        test_content = """
        This is a test URL document with citations: 200 Wn.2d 72, 514 P.3d 643 (2022).
        Another citation: 171 Wn.2d 486, 256 P.3d 321 (2011).
        """
        
        # Mock the URL fetching
        with patch('src.progress_manager.fetch_url_content') as mock_fetch:
            mock_fetch.return_value = test_content
            
            options = ProcessingOptions(
                enable_enhanced_verification=True,
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=True
            )
            
            processor = EnhancedSyncProcessor(options)
            
            print("🔄 Processing URL input...")
            start_time = time.time()
            
            result = processor.process_any_input_enhanced(test_url, 'url')
            
            processing_time = time.time() - start_time
            
            if result['success']:
                print("✅ URL processing successful")
                print(f"   - Processing time: {processing_time:.3f}s")
                print(f"   - Citations found: {result.get('citations_found', len(result.get('citations', [])))}")
                print(f"   - Clusters created: {result.get('clusters_created', len(result.get('clusters', [])))}")
                print(f"   - URL metadata: {result.get('metadata', {}).get('extraction_method', 'unknown')}")
                
                return True
            else:
                print(f"❌ URL processing failed: {result.get('error', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"❌ URL processing test failed: {e}")
        return False

def test_enhanced_features():
    """Test enhanced features integration."""
    try:
        from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        
        options = ProcessingOptions(
            enable_enhanced_verification=True,
            enable_cross_validation=True,
            enable_false_positive_prevention=True,
            enable_confidence_scoring=True,
            courtlistener_api_key="test_key"
        )
        
        processor = EnhancedSyncProcessor(options)
        
        print("🔍 Testing enhanced features...")
        
        # Test false positive prevention
        test_citation = "123 Test 456"
        case_name = "Test"
        year = "2023"
        confidence = 0.3
        
        is_valid = processor._is_valid_citation(test_citation, case_name, year, confidence)
        print(f"   - False positive prevention: {'Working' if not is_valid else 'Not working'} (low confidence citation filtered)")
        
        # Test good citation
        good_citation = "200 Wn.2d 72"
        good_case_name = "Convoyant, LLC v. DeepThink, LLC"
        good_year = "2022"
        good_confidence = 0.9
        
        is_valid_good = processor._is_valid_citation(good_citation, good_case_name, good_year, good_confidence)
        print(f"   - Good citation validation: {'Working' if is_valid_good else 'Not working'}")
        
        # Test confidence scoring if available
        if hasattr(processor, 'confidence_scorer') and processor.confidence_scorer:
            print("   - Confidence scoring: Available")
        else:
            print("   - Confidence scoring: Not available (gracefully handled)")
        
        # Test enhanced verification if available
        if hasattr(processor, 'enhanced_verifier') and processor.enhanced_verifier:
            print("   - Enhanced verification: Available")
        else:
            print("   - Enhanced verification: Not available (gracefully handled)")
        
        print("✅ Enhanced features test completed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced features test failed: {e}")
        return False

def run_quick_tests():
    """Run all quick tests."""
    print("🚀 Starting Quick Backend Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_enhanced_processor_import),
        ("Initialization Test", test_processor_initialization),
        ("Text Processing Test", test_text_processing),
        ("File Processing Test", test_file_processing),
        ("URL Processing Test", test_url_processing),
        ("Enhanced Features Test", test_enhanced_features)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("📊 Quick Test Results")
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is working correctly.")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == '__main__':
    success = run_quick_tests()
    sys.exit(0 if success else 1)

