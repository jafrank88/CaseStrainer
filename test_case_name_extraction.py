#!/usr/bin/env python3
"""
Test case name extraction functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_extraction():
    """Test case name extraction with the test citation"""
    try:
        from case_name_extraction_core import extract_case_name_and_date
        
        # Test text with the same citation from production test
        text = "In Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990), the court held that..."
        citation = "123 Wash. 2d 456, 789 P.2d 123"
        
        print(f"Testing case name extraction...")
        print(f"Text: {text}")
        print(f"Citation: {citation}")
        
        # Extract case name
        result = extract_case_name_and_date(text, citation)
        
        print(f"✅ Case name extraction result:")
        print(f"   Case name: {result.get('case_name', 'N/A')}")
        print(f"   Date: {result.get('date', 'N/A')}")
        print(f"   Year: {result.get('year', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        
        return result.get('case_name') != 'N/A'
        
    except Exception as e:
        print(f"❌ Case name extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_processor():
    """Test the unified processor case name extraction"""
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
            enable_verification=True,
            debug_mode=True
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Test text
        text = "In Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990), the court held that..."
        
        print(f"\nTesting unified processor...")
        print(f"Text: {text}")
        
        # Process text
        results = processor.process_text(text)
        
        print(f"✅ Unified processor results:")
        print(f"   Found {len(results)} citations")
        
        for i, result in enumerate(results):
            print(f"   Citation {i+1}:")
            print(f"     Citation: {result.citation}")
            print(f"     Extracted case name: {result.extracted_case_name}")
            print(f"     Extracted date: {result.extracted_date}")
            print(f"     Confidence: {result.confidence}")
        
        return len(results) > 0 and any(r.extracted_case_name for r in results)
        
    except Exception as e:
        print(f"❌ Unified processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing Case Name Extraction")
    print("=" * 50)
    
    # Test core extraction
    core_success = test_case_name_extraction()
    
    # Test unified processor
    unified_success = test_unified_processor()
    
    print(f"\n📊 Test Results:")
    print(f"   Core extraction: {'✅ PASSED' if core_success else '❌ FAILED'}")
    print(f"   Unified processor: {'✅ PASSED' if unified_success else '❌ FAILED'}")
    
    if core_success and unified_success:
        print("🎉 All tests passed! Case name extraction is working.")
        return True
    else:
        print("⚠️  Some tests failed. Case name extraction needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 