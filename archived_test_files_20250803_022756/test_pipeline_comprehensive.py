#!/usr/bin/env python3
"""
Comprehensive test of the improved CaseStrainer pipeline
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_single_citation():
    """Test a single problematic citation from your CSV data."""
    
    print("Testing single citation verification...")
    print("=" * 50)
    
    # Import the fallback verifier directly
    from src.fallback_verifier import FallbackVerifier
    
    verifier = FallbackVerifier()
    
    # Test the specific citation from your CSV that was problematic
    citation_text = "385 U.S. 493"
    extracted_case_name = "Davis v. Alaska"  # This was wrong in your CSV
    extracted_date = "1967"
    
    print(f"Citation: {citation_text}")
    print(f"Extracted case name (from CSV): {extracted_case_name}")
    print(f"Extracted date: {extracted_date}")
    print()
    
    result = verifier.verify_citation(citation_text, extracted_case_name, extracted_date)
    
    print("Fallback verification result:")
    print(f"  Verified: {result['verified']}")
    print(f"  Source: {result.get('source', 'none')}")
    print(f"  Canonical name: {result.get('canonical_name', 'none')}")
    print(f"  Canonical date: {result.get('canonical_date', 'none')}")
    print(f"  URL: {result.get('url', 'none')}")
    print(f"  Confidence: {result.get('confidence', 0.0)}")
    
    # Check if the canonical name is correct
    canonical_name = result.get('canonical_name', '')
    if 'garrity' in canonical_name.lower():
        print("\n✅ SUCCESS: Correctly identified as Garrity v. New Jersey!")
    elif 'davis' in canonical_name.lower():
        print("\n❌ ISSUE: Still showing as Davis v. Alaska (incorrect)")
    else:
        print(f"\n⚠️  UNCLEAR: Canonical name doesn't clearly match expected case")
    
    return result

def test_api_integration():
    """Test if the improved pipeline works through the API."""
    
    print("\nTesting API integration...")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Test with the production API
        api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        
        test_text = "See Davis v. Alaska, 385 U.S. 493 (1967), which held that..."
        
        data = {
            'text': test_text,
            'source': 'text_input'
        }
        
        print(f"Sending request to: {api_url}")
        print(f"Test text: {test_text}")
        print()
        
        response = requests.post(api_url, json=data, timeout=60)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('data', {}).get('all_citations', [])
            
            print(f"Found {len(citations)} citations")
            
            for citation in citations:
                print(f"\nCitation: {citation.get('citation_text', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'false')}")
                print(f"  Canonical name: {citation.get('canonical_name', 'N/A')}")
                print(f"  Source: {citation.get('source', 'N/A')}")
                
                # Check if this citation is now properly verified
                if '385 U.S. 493' in citation.get('citation_text', ''):
                    if citation.get('verified', 'false').lower() == 'true':
                        print("  ✅ SUCCESS: 385 U.S. 493 is now verified!")
                    else:
                        print("  ❌ STILL UNVERIFIED: 385 U.S. 493 not verified")
        
        elif response.status_code == 202:
            # Async processing
            job_data = response.json()
            job_id = job_data.get('job_id') or job_data.get('task_id')
            print(f"Job queued with ID: {job_id}")
            print("Note: This would require polling for results in a full implementation")
        
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"API test failed: {str(e)}")

if __name__ == "__main__":
    # Test 1: Direct fallback verifier
    test_single_citation()
    
    # Test 2: API integration
    test_api_integration()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("The improved pipeline should now:")
    print("1. ✅ Verify citations through Cornell Law when CourtListener fails")
    print("2. ✅ Correctly identify Garrity v. New Jersey for 385 U.S. 493")
    print("3. ✅ Reduce the number of 'unverified' citations significantly")
    print()
    print("Next step: Re-run your brief processing script to see the improvement!")
