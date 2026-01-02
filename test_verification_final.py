#!/usr/bin/env python3
"""
Final verification test - demonstrates that the verification paradox is fixed
"""

import requests
import json

def test_verification_fix():
    """Test that citations with canonical data are correctly marked as verified"""
    
    print("🔧 TESTING VERIFICATION PARADOX FIX")
    print("=" * 50)
    
    # Test text with a known verifiable citation
    test_text = "The Supreme Court decision in 521 U.S. 811 established important precedent."
    
    print(f"Test text: {test_text}")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"\n📋 Found {len(citations)} citations:")
            
            for i, citation in enumerate(citations):
                print(f"\n  Citation {i+1}: {citation.get('citation', 'N/A')}")
                
                verified = citation.get('verified', False)
                canonical_name = citation.get('canonical_name', 'N/A')
                canonical_date = citation.get('canonical_date', 'N/A')
                canonical_url = citation.get('canonical_url', 'N/A')
                
                # Check if fix is working
                has_canonical_data = bool(canonical_name and canonical_date and canonical_url)
                fix_working = verified and has_canonical_data
                
                print(f"    ✅ Verified: {verified}")
                print(f"    ✅ Canonical Name: {canonical_name}")
                print(f"    ✅ Canonical Date: {canonical_date}")
                print(f"    ✅ Canonical URL: {canonical_url}")
                
                if fix_working:
                    print(f"    🎉 VERIFICATION PARADOX FIXED: Citation with canonical data is marked as verified!")
                else:
                    print(f"    ❌ VERIFICATION PARADOX STILL EXISTS")
            
            # Overall assessment
            if citations and all(c.get('verified', False) and 
                                c.get('canonical_name') and 
                                c.get('canonical_date') and 
                                c.get('canonical_url') for c in citations):
                print(f"\n🎉 SUCCESS: All citations correctly show verified=True with canonical data!")
                print(f"✅ The verification paradox has been FIXED!")
            else:
                print(f"\n❌ FAILURE: Verification paradox still exists")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_verification_fix()
