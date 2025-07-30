#!/usr/bin/env python3
"""
Simple test to verify false positive verification fixes
"""

import requests
import json

def test_false_positive_fix():
    """Test if the false positive verification fix is working"""
    
    print("Testing False Positive Verification Fix")
    print("=" * 40)
    
    # Test the citation that was previously a false positive
    test_citation = "654 F. Supp. 2d 321"
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze_enhanced"
    payload = {"text": test_citation}
    
    try:
        print(f"Testing citation: {test_citation}")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('citations'):
                citation = data['citations'][0]
                
                verified = citation.get('verified', False)
                canonical_name = citation.get('canonical_name')
                url_field = citation.get('url')
                source = citation.get('source', 'N/A')
                
                print(f"Verified: {verified}")
                print(f"Canonical Name: '{canonical_name}'")
                print(f"URL: '{url_field}'")
                print(f"Source: {source}")
                
                # Determine if this is a false positive
                has_complete_data = (canonical_name and canonical_name.strip() and 
                                   url_field and url_field.strip())
                
                if verified and has_complete_data:
                    print(f"\nResult: LEGITIMATE VERIFICATION")
                    print(f"The citation has complete canonical data")
                elif verified and not has_complete_data:
                    print(f"\nResult: FALSE POSITIVE DETECTED")
                    print(f"Citation marked as verified but missing essential data")
                    print(f"THE FIX DID NOT WORK")
                else:
                    print(f"\nResult: CORRECTLY UNVERIFIED")
                    print(f"Citation is not verified (preventing false positive)")
                    print(f"THE FIX WORKED")
                
                return {
                    'verified': verified,
                    'has_complete_data': has_complete_data,
                    'is_false_positive': verified and not has_complete_data
                }
            else:
                print("No citations found in response")
                return None
        else:
            print(f"API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_false_positive_fix()
    
    if result:
        if result['is_false_positive']:
            print(f"\n❌ FALSE POSITIVE VERIFICATION STILL EXISTS")
        elif result['verified'] and result['has_complete_data']:
            print(f"\n✅ LEGITIMATE VERIFICATION (citation is actually in CourtListener)")
        else:
            print(f"\n✅ FALSE POSITIVE VERIFICATION FIXED")
    else:
        print(f"\n❓ Unable to determine fix status")
