#!/usr/bin/env python3

import requests
import json

def test_canonical_cluster_names():
    """Test canonical cluster case name selection and propagation."""
    
    # Text with parallel citations that should be in the same cluster
    test_text = '''Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015).'''
    
    print("CANONICAL CLUSTER CASE NAME TEST")
    print("=" * 60)
    print(f"Text: {test_text}")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Found {len(citations)} citations and {len(clusters)} clusters")
            print()
            
            # Show detailed cluster information
            print("CLUSTER ANALYSIS:")
            print("-" * 50)
            
            for i, cluster in enumerate(clusters, 1):
                cluster_id = cluster.get('cluster_id', 'N/A')
                case_name = cluster.get('case_name', 'N/A')
                canonical_name = cluster.get('canonical_name', 'N/A')
                citations_in_cluster = cluster.get('citations', [])
                
                print(f"Cluster {i}: {cluster_id}")
                print(f"  Case Name: {case_name}")
                print(f"  Canonical Name: {canonical_name}")
                print(f"  Citations: {citations_in_cluster}")
                
                # Check if case name matches canonical name
                if canonical_name and canonical_name != "N/A":
                    if case_name == canonical_name:
                        print("  ✅ Case name matches canonical name")
                    else:
                        print(f"  ❌ Case name mismatch!")
                        print(f"      Expected: {canonical_name}")
                        print(f"      Got: {case_name}")
                else:
                    print("  ⚠️  No canonical name available")
                print()
            
            # Show individual citation cluster assignments
            print("INDIVIDUAL CITATION CLUSTER ASSIGNMENTS:")
            print("-" * 50)
            
            for citation in citations:
                citation_text = citation.get('citation', 'N/A')
                cluster_case_name = citation.get('cluster_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', 'N/A')
                cluster_id = citation.get('metadata', {}).get('cluster_id', 'N/A')
                
                print(f"Citation: {citation_text}")
                print(f"  Cluster ID: {cluster_id}")
                print(f"  Cluster Case Name: {cluster_case_name}")
                print(f"  Individual Canonical Name: {canonical_name}")
                
                # Check consistency
                if cluster_case_name == canonical_name:
                    print("  ✅ Cluster case name matches individual canonical name")
                elif canonical_name and canonical_name != "N/A":
                    print("  ❌ Cluster case name doesn't match individual canonical name")
                else:
                    print("  ⚠️  No individual canonical name for comparison")
                print()
            
            # Check if parallel citations are clustered together
            print("PARALLEL CITATION CLUSTERING CHECK:")
            print("-" * 50)
            
            lopez_citations = []
            for citation in citations:
                canonical_name = citation.get('canonical_name', '') or ''
                if 'Lopez Demetrio' in canonical_name or 'Sakuma Bros' in canonical_name:
                    lopez_citations.append(citation)
            
            if len(lopez_citations) > 1:
                cluster_ids = set()
                for citation in lopez_citations:
                    cluster_id = citation.get('metadata', {}).get('cluster_id', 'N/A')
                    cluster_ids.add(cluster_id)
                
                if len(cluster_ids) == 1:
                    print(f"✅ SUCCESS: {len(lopez_citations)} Lopez Demetrio citations are in the same cluster")
                    print(f"   Cluster ID: {list(cluster_ids)[0]}")
                else:
                    print(f"❌ ISSUE: {len(lopez_citations)} Lopez Demetrio citations are in {len(cluster_ids)} different clusters")
                    print(f"   Cluster IDs: {cluster_ids}")
            else:
                print("⚠️  Only found one Lopez Demetrio citation")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_canonical_cluster_names()
