#!/usr/bin/env python3
"""
Test script for CitationParser integration with EnhancedDocumentProcessor.
This script tests the complete pipeline including case name and year extraction.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_case_name_extraction():
    """Test case name and year extraction with the enhanced processor."""
    
    # Sample legal text with known citations
    sample_text = """
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).
    Campbell & Gwinn, LLC v. Rock, 146 Wn.2d 1, 43 P.3d 4 (2002).
    """
    
    try:
        # Import the enhanced processor
        from src.document_processing import EnhancedDocumentProcessor
        
        # Initialize processor
        processor = EnhancedDocumentProcessor()
        
        # Process document
        result = processor.process_document(
            content=sample_text,
            extract_case_names=True,
            debug_mode=True
        )
        
        print("=== EXTRACTION RESULTS ===")
        print(f"Success: {result.get('success')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Case names found: {len(result.get('case_names', []))}")
        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
        
        # Check each citation
        for i, citation in enumerate(result.get('citations', []), 1):
            print(f"\nCitation {i}:")
            print(f"  Text: {citation.get('citation', 'N/A')}")
            print(f"  Case Name: {citation.get('case_name', 'N/A')}")
            print(f"  Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"  Year: {citation.get('year', 'N/A')}")
            print(f"  Extracted Date: {citation.get('extracted_date', 'N/A')}")
            print(f"  Method: {citation.get('method', 'N/A')}")
            print(f"  Verified: {citation.get('verified', False)}")
            
            # Check metadata if available
            metadata = citation.get('metadata', {})
            if metadata:
                print(f"  Parser Confidence: {metadata.get('parser_confidence', 'N/A')}")
                print(f"  Extraction Method: {metadata.get('extraction_method', 'N/A')}")
                print(f"  Full Citation Found: {metadata.get('full_citation_found', 'N/A')}")
        
        # Check case names
        print(f"\n=== CASE NAMES ===")
        for i, case_name in enumerate(result.get('case_names', []), 1):
            print(f"  {i}. {case_name}")
        
        # Check debug info
        debug_info = result.get('debug_info')
        if debug_info:
            print(f"\n=== DEBUG INFO ===")
            print(f"Debug info available: {len(debug_info)} items")
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

def test_citation_parser_direct():
    """Test the CitationParser directly."""
    
    try:
        from src.standalone_citation_parser import CitationParser
        
        parser = CitationParser()
        
        # Test cases
        test_cases = [
            "200 Wn.2d 72, 514 P.3d 643 (2022)",
            "171 Wn.2d 486, 256 P.3d 321 (2011)",
            "146 Wn.2d 1, 43 P.3d 4 (2002)"
        ]
        
        print("=== DIRECT CITATION PARSER TEST ===")
        
        for i, citation in enumerate(test_cases, 1):
            print(f"\nTest case {i}: {citation}")
            
            # Test extraction from text
            sample_text = f"Some context before {citation} and some context after."
            result = parser.extract_from_text(sample_text, citation)
            
            print(f"  Case Name: {result.get('case_name', 'N/A')}")
            print(f"  Year: {result.get('year', 'N/A')}")
            print(f"  Full Citation Found: {result.get('full_citation_found', 'N/A')}")
            print(f"  Extraction Method: {result.get('extraction_method', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Direct parser test failed: {e}", exc_info=True)
        return False

def test_enhanced_processor_availability():
    """Test that the enhanced processor is available."""
    
    try:
        from src.document_processing import ENHANCED_PROCESSOR_AVAILABLE
        
        print("=== PROCESSOR AVAILABILITY TEST ===")
        print(f"Enhanced processor available: {ENHANCED_PROCESSOR_AVAILABLE}")
        
        if ENHANCED_PROCESSOR_AVAILABLE:
            from src.document_processing import EnhancedDocumentProcessor
            processor = EnhancedDocumentProcessor()
            print(f"Processor initialized: {processor is not None}")
            
            # Check if CitationParser is available
            if hasattr(processor, 'processor') and hasattr(processor.processor, 'citation_parser'):
                print("CitationParser integration: ✅ Available")
                return True
            else:
                print("CitationParser integration: ❌ Not available")
                return False
        else:
            print("Enhanced processor: ❌ Not available")
            return False
            
    except Exception as e:
        logger.error(f"Availability test failed: {e}", exc_info=True)
        return False

def main():
    """Run all tests."""
    
    print("CitationParser Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Processor availability
    print("\n1. Testing processor availability...")
    availability_ok = test_enhanced_processor_availability()
    
    # Test 2: Direct parser test
    print("\n2. Testing CitationParser directly...")
    parser_ok = test_citation_parser_direct()
    
    # Test 3: Full integration test
    print("\n3. Testing full integration...")
    integration_ok = test_case_name_extraction()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Processor Availability: {'✅ PASS' if availability_ok else '❌ FAIL'}")
    print(f"Direct Parser Test: {'✅ PASS' if parser_ok else '❌ FAIL'}")
    print(f"Full Integration Test: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    if availability_ok and parser_ok and integration_ok:
        print("\n🎉 All tests passed! CitationParser integration is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 