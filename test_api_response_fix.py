#!/usr/bin/env python3
"""
Test script to verify the API response structure fix.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api.services.citation_service import CitationService

def test_api_response():
    """Test the API response structure."""
    print("Testing API response structure...")
    
    # Create citation service
    service = CitationService()
    
    # Test text with citations
    test_text = "The court in Brown v. Board of Education, 347 U.S. 483 (1954) held that segregation was unconstitutional."
    
    print(f"Processing text: {test_text}")
    
    # Process the text
    result = service.process_immediately({'text': test_text})
    
    print(f"Response status: {result.get('status')}")
    print(f"Citations found: {len(result.get('citations', []))}")
    print(f"Results found: {len(result.get('results', []))}")
    print(f"Statistics: {result.get('statistics')}")
    print(f"Summary: {result.get('summary')}")
    print(f"Metadata: {result.get('metadata')}")
    
    # Check if citations are properly formatted
    citations = result.get('citations', [])
    if citations:
        print(f"\nFirst citation structure:")
        for key, value in citations[0].items():
            print(f"  {key}: {value}")
    
    # Verify the structure matches what frontend expects
    expected_keys = ['status', 'citations', 'results', 'statistics', 'summary', 'metadata']
    missing_keys = [key for key in expected_keys if key not in result]
    
    if missing_keys:
        print(f"\n❌ Missing keys: {missing_keys}")
        return False
    else:
        print(f"\n✅ All expected keys present")
    
    # Check if citations have required fields
    if citations:
        citation = citations[0]
        required_fields = ['citation', 'verified', 'case_name', 'extracted_case_name', 'canonical_name', 'canonical_date', 'extracted_date']
        missing_fields = [field for field in required_fields if field not in citation]
        
        if missing_fields:
            print(f"❌ Missing citation fields: {missing_fields}")
            return False
        else:
            print(f"✅ All required citation fields present")
    
    return True

if __name__ == "__main__":
    success = test_api_response()
    if success:
        print("\n🎉 API response structure test passed!")
    else:
        print("\n❌ API response structure test failed!")
        sys.exit(1) 