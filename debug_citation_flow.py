#!/usr/bin/env python3
"""
Comprehensive debug script to trace citation verification flow.
This will help identify where canonical fields (URL, case name, date) are being lost.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_citation_flow(citation="534 F.3d 1290"):
    """Test the complete citation verification flow step by step."""
    print(f"\n{'='*80}")
    print(f"DEBUGGING CITATION FLOW: {citation}")
    print(f"{'='*80}")
    
    try:
        from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        # Initialize verifier
        verifier = EnhancedMultiSourceVerifier()
        
        print(f"\n1. INITIALIZATION:")
        print(f"   API Key available: {bool(verifier.courtlistener_api_key)}")
        print(f"   Cache enabled: {bool(verifier.cache)}")
        
        print(f"\n2. CITATION CLEANING:")
        cleaned = verifier._clean_citation_for_lookup(citation)
        print(f"   Original: '{citation}'")
        print(f"   Cleaned:  '{cleaned}'")
        
        print(f"\n3. CITATION COMPONENTS:")
        components = verifier._extract_citation_components(citation)
        print(f"   Components: {json.dumps(components, indent=2)}")
        
        print(f"\n4. COURT LISTENER LOOKUP (citation-lookup API):")
        lookup_result = verifier._lookup_citation(citation)
        print(f"   Lookup Result: {json.dumps(lookup_result, indent=2) if lookup_result else 'None'}")
        
        print(f"\n5. COURT LISTENER SEARCH (search API):")
        search_result = verifier._search_courtlistener_exact(citation)
        print(f"   Search Result: {json.dumps(search_result, indent=2) if search_result else 'None'}")
        
        print(f"\n6. COURT LISTENER VERIFICATION (combined):")
        courtlistener_result = verifier.verify_citation_unified_workflow(citation)
        print(f"   Combined Result: {json.dumps(courtlistener_result, indent=2) if courtlistener_result else 'None'}")
        
        print(f"\n7. API VERIFICATION (parallel sources):")
        api_result = verifier._verify_with_api(citation)
        print(f"   API Result: {json.dumps(api_result, indent=2) if api_result else 'None'}")
        
        print(f"\n8. FINAL VERIFICATION (main method):")
        final_result = verifier.verify_citation_unified_workflow(citation)
        print(f"   Final Result: {json.dumps(final_result, indent=2) if final_result else 'None'}")
        
        print(f"\n9. ANALYSIS:")
        print(f"   Final verified: {final_result.get('verified', False)}")
        print(f"   Final source: {final_result.get('source', 'None')}")
        print(f"   Final case_name: {final_result.get('case_name', 'None')}")
        print(f"   Final url: {final_result.get('url', 'None')}")
        print(f"   Final date_filed: {final_result.get('date_filed', 'None')}")
        print(f"   Final parallel_citations: {len(final_result.get('parallel_citations', []))}")
        
        # Check if canonical fields are missing
        missing_fields = []
        if not final_result.get('case_name'):
            missing_fields.append('case_name')
        if not final_result.get('url'):
            missing_fields.append('url')
        if not final_result.get('date_filed'):
            missing_fields.append('date_filed')
        
        if missing_fields:
            print(f"   ❌ MISSING CANONICAL FIELDS: {missing_fields}")
        else:
            print(f"   ✅ All canonical fields present")
            
        return final_result
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_raw_api_calls(citation="534 F.3d 1290"):
    """Test raw API calls to compare with backend processing."""
    print(f"\n{'='*80}")
    print(f"RAW API CALLS TEST: {citation}")
    print(f"{'='*80}")
    
    import requests
    import os
    
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("No CourtListener API key found")
        return
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test citation-lookup API
    print(f"\n1. CITATION-LOOKUP API:")
    try:
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        data = {"text": citation}
        response = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test search API
    print(f"\n2. SEARCH API:")
    try:
        url = f"https://www.courtlistener.com/api/rest/v4/opinions/?cite={citation}"
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Count: {data.get('count', 0)}")
            if data.get('results'):
                print(f"   First result: {json.dumps(data['results'][0], indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    citation = "534 F.3d 1290"
    
    # Test raw API calls first
    test_raw_api_calls(citation)
    
    # Test complete backend flow
    result = test_citation_flow(citation)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    if result:
        print(f"Final result source: {result.get('source')}")
        print(f"Final result verified: {result.get('verified')}")
        print(f"Canonical URL present: {bool(result.get('url'))}")
        print(f"Canonical name present: {bool(result.get('case_name'))}")
        print(f"Canonical date present: {bool(result.get('date_filed'))}")
    else:
        print("No result returned")

    # Test CourtListener API directly
    print(f"\n{'='*60}")
    print("TESTING COURTLISTENER API DIRECTLY")
    print(f"{'='*60}")
    
    try:
        courtlistener_result = verifier.verify_citation_unified_workflow(citation)
        print(f"CourtListener Result: {json.dumps(courtlistener_result, indent=2)}")
    except Exception as e:
        print(f"CourtListener Error: {e}") 