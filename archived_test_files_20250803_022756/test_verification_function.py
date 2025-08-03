#!/usr/bin/env python3
"""
Direct test of the verification function to check if the false positive fix is working
"""

import os
import sys
sys.path.insert(0, 'src')

from src.courtlistener_verification import verify_with_courtlistener

def test_verification_function():
    """Test the verification function directly"""
    
    # Get API key
    api_key = None
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'COURTLISTENER_API_KEY=' in line:
                    api_key = line.split('=')[1].strip().strip('"\'')
                    break
    except:
        pass
    
    if not api_key:
        api_key = os.getenv('COURTLISTENER_API_KEY')
    
    if not api_key:
        print("No API key found")
        return
    
    print("TESTING VERIFICATION FUNCTION DIRECTLY")
    print("=" * 45)
    
    # Test the citation that was a false positive
    citation = "654 F. Supp. 2d 321"
    
    print(f"Testing citation: {citation}")
    print("Calling verify_with_courtlistener...")
    
    result = verify_with_courtlistener(api_key, citation)
    
    print(f"\nRESULT:")
    print(f"  Verified: {result.get('verified')}")
    print(f"  Canonical Name: '{result.get('canonical_name')}'")
    print(f"  Canonical Date: '{result.get('canonical_date')}'")
    print(f"  URL: '{result.get('url')}'")
    print(f"  Source: '{result.get('source')}'")
    
    # Check if this is a false positive
    verified = result.get('verified', False)
    canonical_name = result.get('canonical_name')
    url = result.get('url')
    
    if verified and canonical_name and canonical_name.strip() and url and url.strip():
        print(f"\nANALYSIS: LEGITIMATE VERIFICATION")
        print(f"The citation has complete canonical data")
        print(f"Either the fix worked and this is actually legitimate, or there's another issue")
    elif verified and (not canonical_name or not canonical_name.strip() or not url or not url.strip()):
        print(f"\nANALYSIS: FALSE POSITIVE DETECTED")
        print(f"Citation is verified but missing essential data")
        print(f"THE FIX DID NOT WORK - validation logic failed")
    else:
        print(f"\nANALYSIS: CORRECTLY UNVERIFIED")
        print(f"Citation is not verified (preventing false positive)")
        print(f"THE FIX WORKED")
    
    return result

if __name__ == "__main__":
    test_verification_function()
