import requests
import json
import time

def test_verification_working():
    """Test if citation verification is working for at least one case."""
    
    # Test with a well-known citation that should verify successfully
    test_text = """Brown v. Board of Education, 347 U.S. 483 (1954)"""
    
    print("🔍 TESTING CITATION VERIFICATION")
    print("=" * 60)
    print(f"Test citation: {test_text}")
    print("Expected: Should verify successfully (famous Supreme Court case)")
    print()
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Verification-Test/1.0'
    }
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        print("📤 Sending verification test request...")
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get('result', {})
            
            citations = result.get('citations', [])
            processing_strategy = result.get('processing_strategy', 'N/A')
            verification_enabled = result.get('verification_enabled', False)
            
            print(f"✅ API Response received")
            print(f"   Citations found: {len(citations)}")
            print(f"   Processing strategy: {processing_strategy}")
            print(f"   Verification enabled: {verification_enabled}")
            print()
            
            if citations:
                print("📋 CITATION ANALYSIS:")
                for i, citation in enumerate(citations, 1):
                    citation_text = citation.get('citation', 'N/A')
                    verified = citation.get('verified', False)
                    canonical_name = citation.get('canonical_name', None)
                    canonical_date = citation.get('canonical_date', None)
                    canonical_url = citation.get('canonical_url', None)
                    
                    print(f"   Citation {i}: {citation_text}")
                    print(f"     Verified: {verified}")
                    print(f"     Canonical name: {canonical_name}")
                    print(f"     Canonical date: {canonical_date}")
                    print(f"     Canonical URL: {canonical_url}")
                    print()
                    
                    if verified:
                        print(f"   ✅ VERIFICATION WORKING! Citation {i} is verified")
                        if canonical_name:
                            print(f"   ✅ Canonical data retrieved: {canonical_name}")
                        return True
                
                print("   ❌ NO VERIFIED CITATIONS FOUND")
                print("   Verification may be disabled or not working")
                
            else:
                print("❌ NO CITATIONS FOUND")
                print("   Citation extraction may have failed")
            
            # Save response for analysis
            with open('verification_test_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print("📄 Response saved to verification_test_response.json")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    return False

def test_verification_with_multiple_cases():
    """Test verification with multiple well-known cases."""
    
    test_cases = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Roe v. Wade, 410 U.S. 113 (1973)", 
        "Miranda v. Arizona, 384 U.S. 436 (1966)"
    ]
    
    print("\n🔍 TESTING VERIFICATION WITH MULTIPLE CASES")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case}")
        
        url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'CaseStrainer-Multi-Verification-Test/1.0'
        }
        data = {
            'text': test_case,
            'type': 'text'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                result = response_data.get('result', {})
                citations = result.get('citations', [])
                
                verified_count = sum(1 for c in citations if c.get('verified', False))
                print(f"   Citations: {len(citations)}, Verified: {verified_count}")
                
                if verified_count > 0:
                    print(f"   ✅ VERIFICATION WORKING for test {i}")
                    return True
                else:
                    print(f"   ❌ No verification for test {i}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Test {i} failed: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    print("=" * 60)
    return False

if __name__ == "__main__":
    # Test single case first
    verification_working = test_verification_working()
    
    if not verification_working:
        # If single case fails, try multiple cases
        verification_working = test_verification_with_multiple_cases()
    
    print("\n🎯 FINAL VERIFICATION STATUS:")
    if verification_working:
        print("✅ VERIFICATION IS WORKING!")
    else:
        print("❌ VERIFICATION IS NOT WORKING")
        print("   May need to re-enable verification in unified_citation_processor_v2.py")
