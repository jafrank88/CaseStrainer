#!/usr/bin/env python3
"""
Simple test of fallback verification without unicode issues
"""

import sys
import os
import logging

def test_fallback_verifier():
    """Test the fallback verifier directly"""
    
    print("TESTING FALLBACK VERIFIER")
    print("=" * 50)
    
    try:
        # Import the fallback verifier
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.fallback_verifier import FallbackVerifier
        
        print("SUCCESS: Imported FallbackVerifier")
        
        # Create verifier instance
        verifier = FallbackVerifier()
        print("SUCCESS: Created FallbackVerifier instance")
        
        # Test with a known citation
        citation = '194 Wn. 2d 784'
        case_name = 'State v. Arndt'
        date = '2019'
        
        print(f"Testing: {citation}")
        print(f"Expected case: {case_name}")
        print(f"Expected date: {date}")
        
        result = verifier.verify_citation(citation, case_name, date)
        
        print(f"Result: {result}")
        
        if result.get('verified'):
            print(f"SUCCESS: Verified via {result.get('source', 'unknown')}")
            print(f"Canonical name: {result.get('canonical_name', 'N/A')}")
            print(f"URL: {result.get('url', 'N/A')}")
            return True
        else:
            print(f"FAILED: Not verified")
            print(f"Error: {result.get('error', 'No error message')}")
            return False
            
    except ImportError as e:
        print(f"ERROR: Cannot import FallbackVerifier: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Exception in fallback test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_call():
    """Test the API call directly to see what's happening"""
    
    print("\nTESTING API CALL")
    print("=" * 50)
    
    import requests
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    test_text = "In State v. Arndt, 194 Wn. 2d 784, 453 P.3d 696 (2019), the court held..."
    
    try:
        response = requests.post(
            endpoint,
            json={"text": test_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"API SUCCESS: Found {len(citations)} citations")
            
            for i, citation in enumerate(citations):
                print(f"Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"  Verified: {citation.get('verified', False)}")
                print(f"  Source: {citation.get('source', 'N/A')}")
                print(f"  Canonical name: {citation.get('canonical_name', 'N/A')}")
                
                # Check if this is fallback
                source = citation.get('source', '')
                if 'Cornell' in source or 'Justia' in source or 'fallback' in source.lower():
                    print(f"  FALLBACK DETECTED: {source}")
                    return True
                elif source == 'regex':
                    print(f"  REGEX ONLY: No fallback attempted")
            
            return False
        else:
            print(f"API ERROR: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"API EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    print("DEBUGGING FALLBACK VERIFICATION")
    print("=" * 60)
    
    # Test 1: Direct fallback verifier
    fallback_works = test_fallback_verifier()
    
    # Test 2: API call
    api_has_fallback = test_api_call()
    
    print("\nSUMMARY")
    print("=" * 30)
    print(f"Fallback verifier works: {fallback_works}")
    print(f"API uses fallback: {api_has_fallback}")
    
    if fallback_works and not api_has_fallback:
        print("ISSUE: Fallback verifier works but API is not using it")
    elif not fallback_works:
        print("ISSUE: Fallback verifier itself is broken")
    else:
        print("SUCCESS: Both fallback verifier and API are working")
