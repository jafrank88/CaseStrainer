#!/usr/bin/env python3
"""
Test fast verification system with production API
"""

import requests
import json
import time

def test_production_fast_verification():
    """Test the fast verification system in production"""
    
    print("🌐 TESTING PRODUCTION FAST VERIFICATION")
    print("=" * 60)
    
    # Test text with D2 59366-1-II style citations
    test_text = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    STATE OF WASHINGTON,
        Respondent,
    v.
    JOHN DOE,
        Appellant.
    
    No. 59366-1-II
    UNPUBLISHED OPINION
    
    The trial court erred in denying the motion to suppress. As held in State v. Ladson, 
    148 Wn.2d 325, 59 P.3d 771 (2002), we review de novo Fourth Amendment violations. 
    The State must show reasonable suspicion as required in State v. Harrington, 
    167 Wn.2d 656, 260 P.3d 951 (2011). In State v. Madsen, 168 Wn.2d 496, 229 P.3d 729 (2010), 
    the Supreme Court held that reasonable suspicion exists when an officer observes 
    a traffic violation. See also State v. Kennedy, 133 Wn.2d 598, 947 P.2d 1001 (1997).
    """
    
    print(f"📤 Testing with {len(test_text)} characters of D2 59366-1-II content...")
    
    try:
        url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        data = {
            "text": test_text,
            "extract_case_names": True
        }
        
        start_time = time.time()
        print("📤 Sending to production API...")
        
        response = requests.post(url, json=data, timeout=30)
        end_time = time.time()
        
        print(f"⏱️ Total API response time: {end_time - start_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\n📋 Production Results:")
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            if citations:
                print(f"\n📊 Citation Analysis:")
                print("=" * 80)
                
                verified_count = 0
                verification_sources = {}
                
                for i, citation in enumerate(citations):
                    print(f"\n--- Citation {i+1} ---")
                    print(f"Citation: {citation.get('citation', 'N/A')}")
                    print(f"Extracted: '{citation.get('extracted_case_name', 'N/A')}'")
                    print(f"Canonical: '{citation.get('canonical_name', 'N/A')}'")
                    print(f"Verified: {citation.get('verified', False)}")
                    print(f"Source: {citation.get('verification_source', 'N/A')}")
                    print(f"Confidence: {citation.get('confidence', 0):.2f}")
                    
                    if citation.get('verified', False):
                        verified_count += 1
                    
                    source = citation.get('verification_source', 'N/A')
                    verification_sources[source] = verification_sources.get(source, 0) + 1
                
                # Summary
                print(f"\n🎯 PRODUCTION VERIFICATION SUMMARY:")
                print("=" * 80)
                print(f"✅ Total citations: {len(citations)}")
                print(f"✅ Verified citations: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
                print(f"✅ Processing time: {end_time - start_time:.2f}s")
                print(f"✅ Average time per citation: {(end_time - start_time)/len(citations):.2f}s")
                
                print(f"\n📋 Verification Sources:")
                for source, count in verification_sources.items():
                    print(f"  {source}: {count} citations")
                
                # Quality assessment
                high_confidence = sum(1 for c in citations if c.get('confidence', 0) >= 0.7)
                print(f"\n📊 Quality Metrics:")
                print(f"  High confidence citations: {high_confidence}/{len(citations)}")
                print(f"  Average confidence: {sum(c.get('confidence', 0) for c in citations)/len(citations):.2f}")
                
                # Speed comparison
                old_system_time = len(citations) * 60  # 60 seconds per citation
                print(f"\n🚀 SPEED COMPARISON:")
                print(f"  Old system estimate: {old_system_time}s")
                print(f"  Fast system actual: {end_time - start_time:.2f}s")
                print(f"  Speed improvement: {old_system_time/(end_time - start_time):.0f}x faster")
                
                # Overall assessment
                if verified_count == len(citations) and (end_time - start_time) < 10:
                    print(f"\n🎉 EXCELLENT: Fast verification working perfectly in production!")
                elif verified_count >= len(citations) * 0.8:
                    print(f"\n✅ GOOD: Fast verification working well in production")
                else:
                    print(f"\n⚠️ NEEDS ATTENTION: Some issues in production")
            
            else:
                print(f"\n❌ No citations found in production")
        
        else:
            print(f"❌ Production API error: {response.status_code}")
            print(f"Response: {response.text[:300]}...")
    
    except Exception as e:
        print(f"❌ Production test error: {e}")

if __name__ == "__main__":
    test_production_fast_verification()
