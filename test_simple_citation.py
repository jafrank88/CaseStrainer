#!/usr/bin/env python3
"""
Simple test to check citation extraction.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def test_simple_citation():
    """Test simple citation extraction."""
    print("Testing simple citation extraction...")
    
    # Create processor
    processor = UnifiedCitationProcessor()
    
    # Test text with a simple citation
    test_text = "347 U.S. 483"
    
    print(f"Processing text: {test_text}")
    
    # Process the text
    result = processor.process_text(test_text, extract_case_names=True, verify_citations=True)
    
    print(f"Result keys: {list(result.keys())}")
    print(f"Results found: {len(result.get('results', []))}")
    print(f"Summary: {result.get('summary')}")
    
    # Check if citations were found
    citations = result.get('results', [])
    if citations:
        print(f"\nFound {len(citations)} citations:")
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.get('citation', 'N/A')}")
            print(f"     Verified: {citation.get('verified', 'N/A')}")
            print(f"     Case name: {citation.get('case_name', 'N/A')}")
    else:
        print("\nNo citations found")
    
    return len(citations) > 0

if __name__ == "__main__":
    success = test_simple_citation()
    if success:
        print("\n🎉 Citation extraction test passed!")
    else:
        print("\n❌ Citation extraction test failed!")
        sys.exit(1) 