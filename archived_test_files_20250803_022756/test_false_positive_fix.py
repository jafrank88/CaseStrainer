#!/usr/bin/env python3
"""
Test the fixed production environment to verify false positive verification fixes
"""

import requests
import json
import time

def test_production_verification_fixes():
    """Test that the false positive verification fixes are working in production"""
    
    print("TESTING PRODUCTION VERIFICATION FIXES")
    print("=" * 50)
    
    # Test with the citations that were previously showing false positives
    test_citations = [
        "654 F. Supp. 2d 321",  # This was the false positive we identified
        "147 Wn. App. 891",    # Another citation from the original test
        "789 P.2d 123"         # This one was correctly unverified before
    ]
    
    # Combine all citations into one test text
    test_text = "\n".join([f"{i+1}. {cite}" for i, cite in enumerate(test_citations)])
    
    print(f"Test text:")
    print(test_text)
    print()
    
    # Test the production API
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze_enhanced"
    
    payload = {
        "text": test_text,
        "debug": True
    }
    
    try:
        print("Sending request to production API...")
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                citations = data.get('citations', [])
                print(f"\nFound {len(citations)} citations")
                
                print(f"\nVERIFICATION RESULTS:")
                print("-" * 40)
                
                for citation in citations:
                    cite_text = citation.get('citation', 'N/A')
                    verified = citation.get('verified', False)
                    canonical_name = citation.get('canonical_name', 'N/A')
                    source = citation.get('source', 'N/A')
                    url = citation.get('url', 'N/A')
                    
                    print(f"\nCitation: {cite_text}")
                    print(f"  Verified: {verified}")
                    print(f"  Source: {source}")
                    print(f"  Canonical Name: {canonical_name}")
                    print(f"  URL: {url}")
                    
                    # Check for false positive indicators
                    if verified and (canonical_name == 'N/A' or canonical_name is None or not canonical_name.strip()):
                        print(f"  ⚠️  WARNING: Verified but no canonical name - possible false positive!")
                    elif verified and (url == 'N/A' or url is None or not url.strip()):
                        print(f"  ⚠️  WARNING: Verified but no URL - possible false positive!")
                    elif verified and canonical_name and url:
                        print(f"  ✅ GOOD: Verified with complete data")
                    elif not verified:
                        print(f"  ✅ GOOD: Correctly unverified")
                
                # Summary
                verified_count = sum(1 for c in citations if c.get('verified', False))
                complete_verified_count = sum(1 for c in citations if c.get('verified', False) and 
                                            c.get('canonical_name') and c.get('canonical_name').strip() and
                                            c.get('url') and c.get('url').strip())
                
                print(f"\nSUMMARY:")
                print(f"  Total citations: {len(citations)}")
                print(f"  Verified citations: {verified_count}")
                print(f"  Complete verifications: {complete_verified_count}")
                print(f"  Potential false positives: {verified_count - complete_verified_count}")
                
                if verified_count == complete_verified_count:
                    print(f"\n✅ SUCCESS: No false positives detected!")
                    print(f"✅ All verified citations have complete canonical data")
                else:
                    print(f"\n❌ ISSUE: {verified_count - complete_verified_count} potential false positives detected")
                
                return citations
            else:
                print(f"API returned success=false: {data}")
                return None
        else:
            print(f"API error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None

def test_specific_false_positive_citation():
    """Test the specific citation that was a false positive"""
    
    print(f"\nTESTING SPECIFIC FALSE POSITIVE CITATION")
    print("=" * 45)
    
    # Test just the citation that was a false positive
    test_text = "654 F. Supp. 2d 321"
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze_enhanced"
    
    payload = {
        "text": test_text,
        "debug": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('citations'):
                citation = data['citations'][0]
                
                verified = citation.get('verified', False)
                canonical_name = citation.get('canonical_name')
                url_field = citation.get('url')
                source = citation.get('source', 'N/A')
                
                print(f"Citation: {citation.get('citation')}")
                print(f"Verified: {verified}")
                print(f"Canonical Name: '{canonical_name}'")
                print(f"URL: '{url_field}'")
                print(f"Source: {source}")
                
                if verified and canonical_name and canonical_name.strip() and url_field and url_field.strip():
                    print(f"\n✅ LEGITIMATE: Citation is properly verified with complete data")
                elif verified and (not canonical_name or not canonical_name.strip() or not url_field or not url_field.strip()):
                    print(f"\n❌ FALSE POSITIVE: Citation is verified but missing essential data")
                    print(f"❌ THE FIX DID NOT WORK - verification logic still has issues")
                else:
                    print(f"\n✅ CORRECTLY UNVERIFIED: Citation is not verified (as expected)")
                    print(f"✅ THE FIX WORKED - false positive prevented")
                
                return citation
            else:
                print("No citations found or API error")
                return None
        else:
            print(f"API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None

if __name__ == "__main__":
    # Test 1: General verification fixes
    citations = test_production_verification_fixes()
    
    # Test 2: Specific false positive citation
    specific_result = test_specific_false_positive_citation()
    
    print(f"\n" + "=" * 60)
    print("FINAL CONCLUSION:")
    
    if specific_result:
        if specific_result.get('verified') and not (specific_result.get('canonical_name') and specific_result.get('canonical_name').strip()):
            print("❌ FALSE POSITIVE VERIFICATION STILL EXISTS")
            print("❌ The fix did not resolve the issue - further investigation needed")
        elif not specific_result.get('verified'):
            print("✅ FALSE POSITIVE VERIFICATION FIXED")
            print("✅ Previously false positive citation is now correctly unverified")
        else:
            print("✅ CITATION IS LEGITIMATELY VERIFIED")
            print("✅ The citation has complete canonical data and is properly verified")
    else:
        print("❓ Unable to determine fix status - API issues")
    
    print("=" * 60)
