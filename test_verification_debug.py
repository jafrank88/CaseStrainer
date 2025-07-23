#!/usr/bin/env python3
"""
Debug script to test citation verification
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_verification():
    """Test citation verification step by step"""
    
    print("=== Testing Citation Verification ===")
    
    # Test 1: Check API key loading
    print("\n1. Testing API key loading...")
    try:
        from src.config import get_config_value
        api_key = get_config_value("COURTLISTENER_API_KEY")
        print(f"   API key from config: {api_key[:10] if api_key else 'None'}...")
        print(f"   API key length: {len(api_key) if api_key else 0}")
        print(f"   API key truthy: {bool(api_key)}")
    except Exception as e:
        print(f"   Error loading API key: {e}")
        return
    
    # Test 2: Check processor initialization
    print("\n2. Testing processor initialization...")
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        processor = UnifiedCitationProcessorV2()
        print(f"   Processor API key: {processor.courtlistener_api_key[:10] if processor.courtlistener_api_key else 'None'}...")
        print(f"   Processor API key truthy: {bool(processor.courtlistener_api_key)}")
        print(f"   Verification enabled: {processor.config.enable_verification}")
    except Exception as e:
        print(f"   Error initializing processor: {e}")
        return
    
    # Test 3: Test verification function directly
    print("\n3. Testing verification function directly...")
    try:
        from src.citation_verification import verify_citations_with_courtlistener_batch
        from src.models import CitationResult
        
        citations = [CitationResult(citation='147 P.3d 641')]
        result = verify_citations_with_courtlistener_batch(api_key, citations, "test text")
        print(f"   Verification result: {result.status_code if result else 'None'}")
        if result:
            print(f"   Response text: {result.text[:200]}...")
    except Exception as e:
        print(f"   Error in verification: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test full processing
    print("\n4. Testing full processing...")
    try:
        test_text = "Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006)"
        results = processor.process_text(test_text)
        print(f"   Processing completed")
        print(f"   Citations found: {len(results.get('citations', []))}")
        
        for i, citation in enumerate(results.get('citations', [])):
            print(f"   Citation {i+1}: {citation.citation}")
            print(f"     Verified: {citation.verified}")
            print(f"     Source: {citation.source}")
            print(f"     Canonical name: {citation.canonical_name}")
            print(f"     Canonical date: {citation.canonical_date}")
    except Exception as e:
        print(f"   Error in full processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification() 