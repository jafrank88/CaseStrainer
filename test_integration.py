#!/usr/bin/env python3
"""
Test script to verify the enhanced extractor integration works correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_extraction():
    """Test basic case name extraction"""
    try:
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        
        # Test text
        text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
        citation = "123 F.3d 456"
        
        # Extract case name
        case_name, date, confidence = extract_case_name_triple_comprehensive(text, citation)
        
        print(f"✅ Basic extraction test passed!")
        print(f"   Case name: {case_name}")
        print(f"   Date: {date}")
        print(f"   Confidence: {confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic extraction test failed: {e}")
        return False

def test_enhanced_extractor():
    """Test the enhanced extractor directly"""
    try:
        from src.legal_case_extractor_enhanced import LegalCaseExtractorEnhanced
        
        extractor = LegalCaseExtractorEnhanced()
        
        # Test text
        text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
        
        # Extract cases
        cases = extractor.extract_cases(text)
        
        print(f"✅ Enhanced extractor test passed!")
        print(f"   Found {len(cases)} cases")
        
        for case in cases:
            print(f"   - {case.case_name} ({case.year}) - Confidence: {case.confidence:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced extractor test failed: {e}")
        return False

def test_legacy_fallback():
    """Test that legacy fallback works if enhanced extractor fails"""
    try:
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        
        # Test with a simple case that should work with legacy patterns
        text = "The case of Brown v. Board, 347 U.S. 483 (1954) was a landmark case."
        citation = "347 U.S. 483"
        
        case_name, date, confidence = extract_case_name_triple_comprehensive(text, citation)
        
        print(f"✅ Legacy fallback test passed!")
        print(f"   Case name: {case_name}")
        print(f"   Date: {date}")
        print(f"   Confidence: {confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Legacy fallback test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Extractor Integration")
    print("=" * 50)
    
    tests = [
        ("Basic Extraction", test_basic_extraction),
        ("Enhanced Extractor", test_enhanced_extractor),
        ("Legacy Fallback", test_legacy_fallback),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please fix issues before production deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 