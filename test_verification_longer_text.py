import requests
import json

def test_verification_longer_text():
    """Test verification with longer text that should trigger full processing."""
    
    # Longer text with well-known citations to ensure full processing
    test_text = """
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
    held that racial segregation in public schools was unconstitutional. This decision overturned 
    the "separate but equal" doctrine established in Plessy v. Ferguson, 163 U.S. 537 (1896).
    
    Later, in Miranda v. Arizona, 384 U.S. 436 (1966), the Court established the requirement 
    that suspects must be informed of their rights before custodial interrogation. This built 
    upon earlier due process protections recognized in cases like Gideon v. Wainwright, 372 U.S. 335 (1963).
    
    The Court's approach to privacy rights evolved significantly in Roe v. Wade, 410 U.S. 113 (1973),
    which recognized a constitutional right to privacy in reproductive decisions. This case has been
    the subject of extensive legal debate and subsequent Supreme Court decisions for decades.
    """
    
    print("🔍 TESTING VERIFICATION WITH LONGER TEXT")
    print("=" * 60)
    print(f"Text length: {len(test_text)} characters")
    print("Expected: Should trigger full processing with verification")
    print()
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Long-Verification-Test/1.0'
    }
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        print("📤 Sending longer text verification test...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get('result', {})
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            processing_strategy = result.get('processing_strategy', 'N/A')
            verification_enabled = result.get('verification_enabled', False)
            
            print(f"✅ API Response received")
            print(f"   Citations found: {len(citations)}")
            print(f"   Clusters found: {len(clusters)}")
            print(f"   Processing strategy: {processing_strategy}")
            print(f"   Verification enabled: {verification_enabled}")
            print()
            
            verified_count = 0
            if citations:
                print("📋 CITATION VERIFICATION ANALYSIS:")
                for i, citation in enumerate(citations, 1):
                    citation_text = citation.get('citation', 'N/A')
                    verified = citation.get('verified', False)
                    canonical_name = citation.get('canonical_name', None)
                    canonical_date = citation.get('canonical_date', None)
                    
                    print(f"   Citation {i}: {citation_text}")
                    print(f"     Verified: {verified}")
                    if canonical_name:
                        print(f"     Canonical name: {canonical_name}")
                    if canonical_date:
                        print(f"     Canonical date: {canonical_date}")
                    print()
                    
                    if verified:
                        verified_count += 1
                
                print(f"📊 VERIFICATION SUMMARY:")
                print(f"   Total citations: {len(citations)}")
                print(f"   Verified citations: {verified_count}")
                print(f"   Verification rate: {verified_count/len(citations)*100:.1f}%")
                
                if verified_count > 0:
                    print(f"   ✅ VERIFICATION IS WORKING!")
                    print(f"   {verified_count} citation(s) successfully verified")
                else:
                    print(f"   ❌ VERIFICATION NOT WORKING")
                    print(f"   No citations were verified despite longer text")
                
            else:
                print("❌ NO CITATIONS FOUND")
            
            # Save response for analysis
            with open('verification_longer_test_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print("📄 Response saved to verification_longer_test_response.json")
            
            return verified_count > 0
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)

if __name__ == "__main__":
    verification_working = test_verification_longer_text()
    
    print("\n🎯 FINAL VERIFICATION STATUS:")
    if verification_working:
        print("✅ VERIFICATION IS WORKING!")
    else:
        print("❌ VERIFICATION IS NOT WORKING")
        print("   The full processing pipeline may not be running verification")
