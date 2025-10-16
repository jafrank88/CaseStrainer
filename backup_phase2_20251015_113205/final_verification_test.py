import requests
import json
import sys
import os

def test_user_paragraph_final():
    """Final comprehensive test of the user's specific paragraph."""
    
    # The exact paragraph from the user
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    print("=" * 80)
    print("🎯 FINAL VERIFICATION TEST")
    print("Testing the user's specific paragraph for clustering and verification")
    print("=" * 80)
    
    print(f"Text length: {len(test_text)} characters")
    print(f"Expected: Should find Bostain parallel citations and create clusters")
    print()
    
    # Test the production API
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Final-Test/1.0'
    }
    
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        print("📤 Sending request to production API...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Save the response
            with open('final_test_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            # Analyze the results
            result = response_data.get('result', {})
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            metadata = result.get('metadata', {})
            
            print("📊 RESULTS:")
            print(f"  Citations found: {len(citations)}")
            print(f"  Clusters created: {len(clusters)}")
            print(f"  Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
            print(f"  Processing mode: {metadata.get('processing_mode', 'N/A')}")
            print()
            
            # Detailed citation analysis
            print("📋 CITATION ANALYSIS:")
            bostain_citations = []
            verified_citations = []
            
            for i, citation in enumerate(citations, 1):
                case_name = citation.get('extracted_case_name', 'N/A')
                citation_text = citation.get('citation', 'N/A')
                verified = citation.get('verified', False) or citation.get('is_verified', False)
                
                print(f"  {i}. {citation_text}")
                print(f"     Case: {case_name}")
                print(f"     Year: {citation.get('extracted_date', 'N/A')}")
                print(f"     Verified: {verified}")
                print(f"     Canonical: {citation.get('canonical_name', 'None')}")
                print()
                
                if 'bostain' in case_name.lower():
                    bostain_citations.append(citation)
                
                if verified:
                    verified_citations.append(citation)
            
            # Cluster analysis
            print("🔗 CLUSTER ANALYSIS:")
            if clusters:
                for i, cluster in enumerate(clusters, 1):
                    cluster_citations = cluster.get('citations', [])
                    print(f"  Cluster {i}: {len(cluster_citations)} citations")
                    for cite in cluster_citations:
                        print(f"    - {cite}")
                    print()
            else:
                print("  ❌ No clusters found")
            
            # Success criteria evaluation
            print("✅ SUCCESS CRITERIA:")
            
            # 1. Citation extraction
            if len(citations) >= 4:
                print("  ✅ Citation extraction: PASS (found 4+ citations)")
            else:
                print(f"  ❌ Citation extraction: FAIL (found {len(citations)}, expected 4+)")
            
            # 2. Bostain parallel citations
            if len(bostain_citations) >= 2:
                print(f"  ✅ Bostain citations: PASS (found {len(bostain_citations)} citations)")
                for cite in bostain_citations:
                    print(f"    - {cite.get('citation', 'N/A')}")
            else:
                print(f"  ❌ Bostain citations: FAIL (found {len(bostain_citations)}, expected 2)")
            
            # 3. Clustering
            if len(clusters) > 0:
                print(f"  ✅ Clustering: PASS (created {len(clusters)} clusters)")
            else:
                print("  ❌ Clustering: FAIL (no clusters created)")
            
            # 4. Verification
            if len(verified_citations) > 0:
                print(f"  ✅ Verification: PASS ({len(verified_citations)} citations verified)")
            else:
                print("  ❌ Verification: FAIL (no citations verified)")
            
            # Overall assessment
            clustering_works = len(clusters) > 0 and len(bostain_citations) >= 2
            verification_works = len(verified_citations) > 0
            
            print("\n🎯 OVERALL ASSESSMENT:")
            if clustering_works and verification_works:
                print("  🎉 SUCCESS: Both clustering and verification are working!")
            elif clustering_works:
                print("  ⚠️  PARTIAL: Clustering works, but verification needs attention")
            elif verification_works:
                print("  ⚠️  PARTIAL: Verification works, but clustering needs attention")
            else:
                print("  ❌ FAILURE: Both clustering and verification need fixes")
            
            return {
                'citations_count': len(citations),
                'clusters_count': len(clusters),
                'bostain_count': len(bostain_citations),
                'verified_count': len(verified_citations),
                'clustering_works': clustering_works,
                'verification_works': verification_works,
                'overall_success': clustering_works and verification_works
            }
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

def main():
    """Run the final verification test."""
    
    print("🚀 CaseStrainer Final Verification Test")
    print("Testing clustering and verification fixes")
    print()
    
    result = test_user_paragraph_final()
    
    print("\n" + "=" * 80)
    print("📋 FINAL SUMMARY")
    print("=" * 80)
    
    if result:
        if result['overall_success']:
            print("🎉 ALL FIXES SUCCESSFUL!")
            print("✅ Clustering is working correctly")
            print("✅ Verification is working correctly")
            print("✅ User's paragraph processes as expected")
        else:
            print("⚠️  PARTIAL SUCCESS - Some issues remain:")
            if not result['clustering_works']:
                print("❌ Clustering still needs fixes")
            if not result['verification_works']:
                print("❌ Verification still needs fixes")
        
        print(f"\nStatistics:")
        print(f"  Citations: {result['citations_count']}")
        print(f"  Clusters: {result['clusters_count']}")
        print(f"  Bostain citations: {result['bostain_count']}")
        print(f"  Verified citations: {result['verified_count']}")
    else:
        print("❌ TEST FAILED - Unable to get results")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
