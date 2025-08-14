#!/usr/bin/env python3
"""
Direct test of citation extraction using the unified processor
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_citation_extraction():
    """Test citation extraction directly with the unified processor"""
    print("=" * 60)
    print("DIRECT CITATION EXTRACTION TEST")
    print("=" * 60)
    
    # Test text with known citations
    test_text = """
    The Supreme Court decided in Brown v. Board of Education, 347 U.S. 483 (1954), 
    that separate educational facilities are inherently unequal. This landmark case 
    overturned Plessy v. Ferguson, 163 U.S. 537 (1896). Another important case is 
    Miranda v. Arizona, 384 U.S. 436 (1966), which established the Miranda rights.
    """
    
    try:
        # Create processor with verification enabled
        config = ProcessingConfig()
        config.enable_verification = True  # Ensure verification is enabled
        config.debug_mode = True  # Enable debug logging
        
        processor = UnifiedCitationProcessorV2(config=config)
        
        print(f"Processing text (length: {len(test_text)})")
        print(f"Verification enabled: {config.enable_verification}")
        
        # Process the text (async)
        import asyncio
        result = asyncio.run(processor.process_text(test_text))
        
        print(f"\nResults:")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Clusters found: {len(result.get('clusters', []))}")
        
        # Display first few citations
        citations = result.get('citations', [])
        for i, citation in enumerate(citations[:5]):  # Show first 5
            print(f"\nCitation {i+1}:")
            print(f"  Citation: {getattr(citation, 'citation', 'N/A')}")
            print(f"  Case Name: {getattr(citation, 'extracted_case_name', 'N/A')}")
            print(f"  Year: {getattr(citation, 'extracted_date', 'N/A')}")
            print(f"  Verified: {getattr(citation, 'verified', 'N/A')}")
            print(f"  Canonical Name: {getattr(citation, 'canonical_name', 'N/A')}")
            print(f"  Canonical Date: {getattr(citation, 'canonical_date', 'N/A')}")
        
        return len(citations) > 0
        
    except Exception as e:
        print(f"Error in direct citation extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_citation_extraction():
    """Test with a very simple citation"""
    print("\n" + "=" * 60)
    print("SIMPLE CITATION TEST")
    print("=" * 60)
    
    simple_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    try:
        config = ProcessingConfig()
        config.enable_verification = False  # Disable verification for speed
        config.debug_mode = True
        
        processor = UnifiedCitationProcessorV2(config=config)
        
        print(f"Processing simple text: {simple_text}")
        
        result = asyncio.run(processor.process_text(simple_text))
        
        print(f"\nResults:")
        print(f"Citations found: {len(result.get('citations', []))}")
        
        citations = result.get('citations', [])
        for citation in citations:
            print(f"  Citation: {getattr(citation, 'citation', 'N/A')}")
            print(f"  Case Name: {getattr(citation, 'extracted_case_name', 'N/A')}")
        
        return len(citations) > 0
        
    except Exception as e:
        print(f"Error in simple citation extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regex_extraction():
    """Test just the regex extraction component"""
    print("\n" + "=" * 60)
    print("REGEX EXTRACTION TEST")
    print("=" * 60)
    
    test_text = "347 U.S. 483"
    
    try:
        config = ProcessingConfig()
        processor = UnifiedCitationProcessorV2(config=config)
        
        # Test regex extraction directly
        citations = processor._extract_with_regex_enhanced(test_text)
        
        print(f"Regex extraction found: {len(citations)} citations")
        for citation in citations:
            print(f"  Citation: {getattr(citation, 'citation', 'N/A')}")
        
        return len(citations) > 0
        
    except Exception as e:
        print(f"Error in regex extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing citation extraction components...")
    
    # Test regex first
    regex_works = test_regex_extraction()
    
    # Test simple citation
    simple_works = test_simple_citation_extraction()
    
    # Test full extraction
    full_works = test_direct_citation_extraction()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Regex extraction: {'✓ PASS' if regex_works else '✗ FAIL'}")
    print(f"Simple citation: {'✓ PASS' if simple_works else '✗ FAIL'}")
    print(f"Full extraction: {'✓ PASS' if full_works else '✗ FAIL'}")
    
    if not any([regex_works, simple_works, full_works]):
        print("\n❌ ALL TESTS FAILED - Citation extraction is broken")
        sys.exit(1)
    else:
        print(f"\n✅ Some tests passed - Citation extraction is working")
