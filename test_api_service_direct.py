#!/usr/bin/env python3
"""
Test the API service directly without the problematic unified processor.
"""

import sys
import os
# Add src to Python path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def test_api_service_direct():
    """Test the API service directly."""
    print("Testing API service directly...")
    
    try:
        # Import the service
        from api.services.citation_service import CitationService
        
        # Create service
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
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_service_direct()
    if success:
        print("\n🎉 API service test passed!")
    else:
        print("\n❌ API service test failed!")
        sys.exit(1) 