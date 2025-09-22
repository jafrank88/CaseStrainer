#!/usr/bin/env python3

import requests
import json

def test_clustering_production():
    """Test clustering functionality in production."""
    
    print("🔗 PRODUCTION CLUSTERING TEST")
    print("=" * 60)
    
    # Test parallel citations that should cluster together
    test_text = '''State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). The court also cited Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 355 P.3d 258 (2015).'''
    
    print(f"📝 Test text: {test_text}")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"✅ Found {len(citations)} citations")
            print(f"🔗 Found {len(clusters)} clusters")
            print()
            
            # Analyze citations
            print("📋 CITATIONS ANALYSIS:")
            parallel_groups = {}
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', '')
                extracted_case_name = citation.get('extracted_case_name', 'N/A')
                cluster_case_name = citation.get('cluster_case_name', 'N/A')
                is_parallel = citation.get('is_parallel', False)
                
                print(f"   {i}. {citation_text}")
                print(f"      Case: {extracted_case_name}")
                print(f"      Cluster: {cluster_case_name}")
                print(f"      Parallel: {is_parallel}")
                
                # Group by case name for parallel citation analysis
                if extracted_case_name != 'N/A':
                    if extracted_case_name not in parallel_groups:
                        parallel_groups[extracted_case_name] = []
                    parallel_groups[extracted_case_name].append(citation_text)
                print()
            
            # Analyze clusters
            print("🔗 CLUSTERS ANALYSIS:")
            if clusters:
                for i, cluster in enumerate(clusters, 1):
                    cluster_id = cluster.get('cluster_id', 'N/A')
                    cluster_extracted = cluster.get('extracted_case_name', 'N/A')
                    cluster_citations = cluster.get('citations', [])
                    cluster_size = cluster.get('size', 0)
                    
                    print(f"   Cluster {i} ({cluster_id}):")
                    print(f"      Case: {cluster_extracted}")
                    print(f"      Size: {cluster_size}")
                    print(f"      Citations: {cluster_citations}")
                    print()
            else:
                print("   No clusters found")
                print()
            
            # Check for expected parallel citations
            print("🔍 PARALLEL CITATION VERIFICATION:")
            
            # Check State v. Johnson citations
            johnson_citations = [c for c in citations if 'State v. Johnson' in c.get('extracted_case_name', '')]
            if len(johnson_citations) >= 2:
                print(f"   ✅ State v. Johnson: Found {len(johnson_citations)} citations (expected 2+)")
                for cite in johnson_citations:
                    print(f"      - {cite.get('citation', '')}")
            else:
                print(f"   ⚠️  State v. Johnson: Found {len(johnson_citations)} citations (expected 2+)")
            
            # Check Lopez Demetrio citations  
            lopez_citations = [c for c in citations if 'Lopez Demetrio' in c.get('extracted_case_name', '')]
            if len(lopez_citations) >= 2:
                print(f"   ✅ Lopez Demetrio: Found {len(lopez_citations)} citations (expected 2+)")
                for cite in lopez_citations:
                    print(f"      - {cite.get('citation', '')}")
            else:
                print(f"   ⚠️  Lopez Demetrio: Found {len(lopez_citations)} citations (expected 2+)")
            
            print()
            
            # Overall assessment
            total_expected_citations = 6  # 3 for each case (full + individual)
            clustering_working = len(clusters) > 0
            parallel_detection_working = any(c.get('is_parallel', False) for c in citations)
            
            print("🎯 OVERALL ASSESSMENT:")
            print(f"   Citations found: {len(citations)} (expected ~{total_expected_citations})")
            print(f"   Clusters found: {len(clusters)} (expected 2+)")
            print(f"   Parallel detection: {'✅' if parallel_detection_working else '❌'}")
            print(f"   Clustering: {'✅' if clustering_working else '❌'}")
            
            if clustering_working and parallel_detection_working:
                print("\n🎉 SUCCESS: Clustering and parallel citation detection working!")
            else:
                print("\n⚠️  PARTIAL: Some clustering features may need attention")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_clustering_production()
