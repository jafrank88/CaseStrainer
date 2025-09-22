#!/usr/bin/env python3

import requests
import json

def test_verification_detailed():
    """Test verification status in detail."""
    
    test_text = '''Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015).'''
    
    print("VERIFICATION STATUS DETAILED TEST")
    print("=" * 60)
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations")
            print()
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                verified = citation.get('verified', False)
                is_verified = citation.get('is_verified', False)
                canonical_name = citation.get('canonical_name', 'N/A')
                canonical_date = citation.get('canonical_date', 'N/A')
                extracted_name = citation.get('extracted_case_name', 'N/A')
                
                print(f"Citation {i}: {citation_text}")
                print(f"  verified: {verified}")
                print(f"  is_verified: {is_verified}")
                print(f"  canonical_name: {canonical_name}")
                print(f"  canonical_date: {canonical_date}")
                print(f"  extracted_case_name: {extracted_name}")
                
                # Check verification status
                if verified and canonical_name != 'N/A':
                    print("  ✅ PROPERLY VERIFIED")
                elif not verified and canonical_name != 'N/A':
                    print("  ❌ HAS CANONICAL DATA BUT NOT MARKED VERIFIED")
                elif verified and canonical_name == 'N/A':
                    print("  ⚠️  MARKED VERIFIED BUT NO CANONICAL DATA")
                else:
                    print("  ❌ NOT VERIFIED AND NO CANONICAL DATA")
                print()
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_verification_detailed()
