#!/usr/bin/env python3
"""
Test all the fixes we've implemented
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import_fixes():
    """Test that import issues are fixed"""
    print("🔧 Testing Import Fixes...")
    
    try:
        # Test enhanced extractor import
        from legal_case_extractor_enhanced import LegalCaseExtractorEnhanced
        print("   ✅ Enhanced extractor import works")
        
        # Test unified processor import
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        print("   ✅ Unified processor import works")
        
        # Test case name extraction import
        from case_name_extraction_core import extract_case_name_and_date
        print("   ✅ Case name extraction import works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False

def test_docker_upload_fix():
    """Test that Docker upload function is available"""
    print("🔧 Testing Docker Upload Fix...")
    
    try:
        from document_processing_unified import extract_text_from_file
        print("   ✅ extract_text_from_file function is available")
        
        # Test that it can be imported in the API service
        from api.services.citation_service import CitationService
        print("   ✅ CitationService can be imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Docker upload test failed: {e}")
        return False

def test_case_name_extraction_fix():
    """Test case name extraction with a simple case"""
    print("🔧 Testing Case Name Extraction Fix...")
    
    try:
        from case_name_extraction_core import extract_case_name_and_date
        
        # Test with a simple case that should work
        text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
        citation = "123 F.3d 456"
        
        result = extract_case_name_and_date(text, citation)
        
        print(f"   Case name: '{result.get('case_name', 'N/A')}'")
        print(f"   Date: '{result.get('date', 'N/A')}'")
        print(f"   Year: '{result.get('year', 'N/A')}'")
        
        # Check if we got a case name
        if result.get('case_name') and result.get('case_name') != 'N/A':
            print("   ✅ Case name extraction works")
            return True
        else:
            print("   ⚠️  Case name extraction returned N/A - needs improvement")
            return False
            
    except Exception as e:
        print(f"   ❌ Case name extraction test failed: {e}")
        return False

def test_unified_processor():
    """Test the unified processor"""
    print("🔧 Testing Unified Processor...")
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        # Create processor
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            enable_verification=False,  # Disable verification for testing
            debug_mode=True
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Test text
        text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
        
        # Process text
        results = processor.process_text(text)
        
        print(f"   Found {len(results)} citations")
        
        for i, result in enumerate(results):
            print(f"   Citation {i+1}: {result.citation}")
            print(f"     Extracted case name: {result.extracted_case_name}")
            print(f"     Extracted date: {result.extracted_date}")
        
        if len(results) > 0:
            print("   ✅ Unified processor works")
            return True
        else:
            print("   ⚠️  Unified processor found no citations")
            return False
            
    except Exception as e:
        print(f"   ❌ Unified processor test failed: {e}")
        return False

def main():
    print("🧪 Testing All Fixes")
    print("=" * 50)
    
    tests = [
        ("Import Fixes", test_import_fixes),
        ("Docker Upload Fix", test_docker_upload_fix),
        ("Case Name Extraction Fix", test_case_name_extraction_fix),
        ("Unified Processor", test_unified_processor),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes are working!")
        return True
    else:
        print("⚠️  Some fixes need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 