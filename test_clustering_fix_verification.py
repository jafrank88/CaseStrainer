import requests
import json
import time

def test_clustering_fix():
    """Test if the clustering fix is working with the production API."""
    
    # Test with the user's original paragraph
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    print("🔧 TESTING CLUSTERING FIX")
    print("=" * 60)
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Clustering-Fix-Test/1.0'
    }
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        print("📤 Sending test request...")
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get('result', {})
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            processing_strategy = result.get('processing_strategy', 'N/A')
            
            print(f"✅ API Response received")
            print(f"   Citations: {len(citations)}")
            print(f"   Clusters: {len(clusters)}")
            print(f"   Strategy: {processing_strategy}")
            print()
            
            # Check for Bostain citations
            bostain_citations = []
            for citation in citations:
                case_name = citation.get('extracted_case_name', '').lower()
                if 'bostain' in case_name:
                    bostain_citations.append(citation['citation'])
            
            print(f"🔍 Bostain citations found: {len(bostain_citations)}")
            for citation in bostain_citations:
                print(f"   - {citation}")
            print()
            
            # Check clusters
            if clusters:
                print(f"🎯 CLUSTERS FOUND: {len(clusters)}")
                for i, cluster in enumerate(clusters, 1):
                    cluster_id = cluster.get('cluster_id', 'N/A')
                    cluster_citations = cluster.get('citations', [])
                    print(f"   Cluster {i}: {cluster_id}")
                    print(f"     Citations: {cluster_citations}")
                    
                    # Check if this is the Bostain cluster
                    if 'bostain' in cluster_id.lower():
                        print(f"     ✅ BOSTAIN CLUSTER FOUND!")
                        if len(cluster_citations) >= 2:
                            print(f"     ✅ PARALLEL CITATIONS CLUSTERED!")
                        else:
                            print(f"     ⚠️  Only {len(cluster_citations)} citation(s) in cluster")
                print()
            else:
                print("❌ NO CLUSTERS FOUND")
                print("   The clustering fix may need additional work")
                print()
            
            # Overall assessment
            if len(bostain_citations) >= 2 and clusters:
                bostain_cluster_found = any('bostain' in c.get('cluster_id', '').lower() for c in clusters)
                if bostain_cluster_found:
                    print("🎉 SUCCESS: Clustering fix is working!")
                    print("   ✅ Bostain citations found")
                    print("   ✅ Clusters created")
                    print("   ✅ Bostain parallel citations clustered")
                else:
                    print("⚠️  PARTIAL SUCCESS: Clusters found but Bostain not clustered")
            else:
                print("❌ ISSUE REMAINS: Clustering not working as expected")
            
            # Save response for analysis
            with open('clustering_fix_test_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print("📄 Response saved to clustering_fix_test_response.json")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_clustering_fix()
