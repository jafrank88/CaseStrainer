#!/usr/bin/env python3
"""
Test the enhanced verification system against problematic citations
"""

import os
import sys
sys.path.insert(0, 'src')

def get_api_key():
    """Get CourtListener API key"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'COURTLISTENER_API_KEY=' in line:
                    return line.split('=')[1].strip().strip('"\'')
    except:
        pass
    return os.getenv('COURTLISTENER_API_KEY')

def test_enhanced_verification():
    """Test enhanced verification against known problematic citations"""
    
    api_key = get_api_key()
    if not api_key:
        print("No API key found")
        return
    
    print("TESTING ENHANCED VERIFICATION SYSTEM")
    print("=" * 45)
    
    # Test citations - including the problematic false positive
    test_citations = [
        ("654 F. Supp. 2d 321", "Benckini v. Hawk"),  # The false positive
        ("147 Wn. App. 891", None),                   # Another test case
        ("999 F.3d 999", None),                       # Non-existent citation
        ("456 F.3d 789", None),                       # Valid citation test
    ]
    
    for citation, extracted_name in test_citations:
        print(f"\n{'='*60}")
        print(f"TESTING: {citation}")
        if extracted_name:
            print(f"EXTRACTED NAME: {extracted_name}")
        print(f"{'='*60}")
        
        try:
            # Test with enhanced verification
            from src.enhanced_courtlistener_verification import verify_with_courtlistener_enhanced
            
            result = verify_with_courtlistener_enhanced(api_key, citation, extracted_name)
            
            print(f"\nRESULT:")
            print(f"  Verified: {result.get('verified')}")
            print(f"  Canonical Name: '{result.get('canonical_name')}'")
            print(f"  Canonical Date: '{result.get('canonical_date')}'")
            print(f"  URL: '{result.get('url')}'")
            print(f"  Source: '{result.get('source')}'")
            print(f"  Confidence: {result.get('confidence', 0.0)}")
            print(f"  Validation Method: {result.get('validation_method')}")
            
            # Analysis
            verified = result.get('verified', False)
            canonical_name = result.get('canonical_name')
            url = result.get('url')
            confidence = result.get('confidence', 0.0)
            
            if verified and canonical_name and canonical_name.strip() and url and url.strip():
                print(f"\n✅ ANALYSIS: LEGITIMATE VERIFICATION")
                print(f"   Citation has complete canonical data with confidence {confidence}")
                if citation == "654 F. Supp. 2d 321":
                    print(f"   🔍 This was previously a false positive - now properly validated!")
            elif verified and (not canonical_name or not canonical_name.strip() or not url or not url.strip()):
                print(f"\n❌ ANALYSIS: FALSE POSITIVE DETECTED")
                print(f"   Citation is verified but missing essential data")
                print(f"   🚨 ENHANCED VERIFICATION FAILED TO PREVENT FALSE POSITIVE")
            else:
                print(f"\n✅ ANALYSIS: CORRECTLY UNVERIFIED")
                print(f"   Citation is not verified (preventing false positive)")
                if citation == "654 F. Supp. 2d 321":
                    print(f"   🎯 Enhanced verification successfully prevented false positive!")
        
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
        
        print(f"\n{'-'*60}")
    
    print(f"\nTEST COMPLETE")
    print("=" * 20)

if __name__ == "__main__":
    test_enhanced_verification()
