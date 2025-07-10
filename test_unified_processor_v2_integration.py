#!/usr/bin/env python3
"""
Test script to verify UnifiedCitationProcessorV2 integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_citation_service_integration():
    """Test that CitationService is using UnifiedCitationProcessorV2"""
    print("=== Testing CitationService Integration ===")
    
    try:
        from src.api.services.citation_service import CitationService
        
        service = CitationService()
        print(f"✅ CitationService initialized successfully")
        print(f"   Processor name: {service._get_processor_name()}")
        
        # Test immediate processing
        test_input = {
            'type': 'text',
            'text': 'See Brown v. Board of Education, 347 U.S. 483 (1954).'
        }
        
        should_immediate = service.should_process_immediately(test_input)
        print(f"   Should process immediately: {should_immediate}")
        
        if should_immediate:
            result = service.process_immediately(test_input)
            print(f"   Processing result: {result['status']}")
            print(f"   Citations found: {len(result.get('citations', []))}")
            
            if result.get('citations'):
                for i, citation in enumerate(result['citations']):
                    print(f"   Citation {i+1}: {citation.get('citation', 'N/A')}")
                    print(f"     Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"     Extracted date: {citation.get('extracted_date', 'N/A')}")
                    print(f"     Confidence: {citation.get('confidence', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ CitationService integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_processing_integration():
    """Test that document_processing is using UnifiedCitationProcessorV2"""
    print("\n=== Testing Document Processing Integration ===")
    
    try:
        from src.document_processing import process_document
        
        test_text = "The court held in Brown v. Board of Education, 347 U.S. 483 (1954) that segregation was unconstitutional."
        
        result = process_document(content=test_text, extract_case_names=True)
        print(f"✅ Document processing completed successfully")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Citations found: {len(result.get('citations', []))}")
        
        if result.get('citations'):
            for i, citation in enumerate(result['citations']):
                print(f"   Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"     Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"     Extracted date: {citation.get('extracted_date', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document processing integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_processor_availability():
    """Test that the enhanced processor is available"""
    print("\n=== Testing Enhanced Processor Availability ===")
    
    try:
        from src.document_processing import ENHANCED_PROCESSOR_AVAILABLE
        
        print(f"✅ Enhanced processor available: {ENHANCED_PROCESSOR_AVAILABLE}")
        
        if ENHANCED_PROCESSOR_AVAILABLE:
            from src.document_processing import EnhancedProcessor
            processor = EnhancedProcessor()
            print(f"✅ EnhancedProcessor initialized successfully")
            print(f"   Processor type: {type(processor).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced processor availability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_processor_v2_direct():
    """Test UnifiedCitationProcessorV2 directly"""
    print("\n=== Testing UnifiedCitationProcessorV2 Direct ===")
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            debug_mode=False
        )
        
        processor = UnifiedCitationProcessorV2(config)
        print(f"✅ UnifiedCitationProcessorV2 initialized successfully")
        
        test_text = "See Brown v. Board of Education, 347 U.S. 483 (1954)."
        result = processor.process_text(test_text)
        
        print(f"✅ Processing completed successfully")
        print(f"   Results found: {len(result)}")
        
        if result:
            for i, citation_result in enumerate(result):
                print(f"   Result {i+1}: {citation_result.citation}")
                print(f"     Case name: {citation_result.case_name}")
                print(f"     Date: {citation_result.extracted_date}")
                print(f"     Confidence: {citation_result.confidence}")
                print(f"     Source: {citation_result.source}")
        
        return True
        
    except Exception as e:
        print(f"❌ UnifiedCitationProcessorV2 direct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("🧪 Testing UnifiedCitationProcessorV2 Integration")
    print("=" * 60)
    
    tests = [
        test_unified_processor_v2_direct,
        test_enhanced_processor_availability,
        test_document_processing_integration,
        test_citation_service_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! UnifiedCitationProcessorV2 is properly integrated.")
    else:
        print("⚠️  Some integration tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 