#!/usr/bin/env python3
"""
Debug script to test true_by_parallel logic
"""

import requests
import json

def test_api():
    """Test the API and debug true_by_parallel logic"""
    
    # Test data
    test_text = """Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018)."""
    
    # Make API call
    url = "http://localhost:5000/casestrainer/api/analyze"
    payload = {"text": test_text}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print("=== API RESPONSE DEBUG ===")
        print(f"Citations count: {len(data.get('citations', []))}")
        print(f"Clusters count: {len(data.get('clusters', []))}")
        
        # Debug citations
        print("\n=== CITATIONS DEBUG ===")
        for i, citation in enumerate(data.get('citations', [])):
            print(f"Citation {i+1}: {citation.get('citation', 'N/A')}")
            print(f"  Verified: {citation.get('verified', False)}")
            print(f"  True by Parallel: {citation.get('true_by_parallel', False)}")
            print(f"  Source: {citation.get('source', 'N/A')}")
            print()
        
        # Debug clusters
        print("=== CLUSTERS DEBUG ===")
        for i, cluster in enumerate(data.get('clusters', [])):
            print(f"Cluster {i+1}: {cluster.get('cluster_name', 'N/A')}")
            print(f"  Cluster Has Verified: {cluster.get('cluster_has_verified', False)}")
            print(f"  Verified Citations: {cluster.get('verified_citations_count', 0)}")
            print(f"  Citations: {cluster.get('citations', [])}")
            print()
        
        # Manual true_by_parallel analysis
        print("=== MANUAL TRUE_BY_PARALLEL ANALYSIS ===")
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        # Build true_by_parallel set manually
        true_by_parallel_citations = set()
        for cluster in clusters:
            cluster_has_verified = cluster.get('cluster_has_verified', False)
            if cluster_has_verified:
                cluster_citations = cluster.get('citations', [])
                print(f"Processing cluster: {cluster.get('cluster_name', 'N/A')}")
                print(f"  Cluster has verified: {cluster_has_verified}")
                print(f"  Cluster citations: {cluster_citations}")
                
                for citation_text in cluster_citations:
                    # Check if this citation is verified
                    citation_verified = False
                    for citation in citations:
                        if citation.get('citation') == citation_text and citation.get('verified', False):
                            citation_verified = True
                            break
                    
                    print(f"  Citation '{citation_text}': verified={citation_verified}")
                    
                    # If citation is not verified, add it to true_by_parallel set
                    if not citation_verified:
                        true_by_parallel_citations.add(citation_text)
                        print(f"    -> Added to true_by_parallel set")
        
        print(f"\nTrue by parallel citations set: {true_by_parallel_citations}")
        
        # Check each citation
        for citation in citations:
            citation_text = citation.get('citation', '')
            should_be_true_by_parallel = citation_text in true_by_parallel_citations
            actual_true_by_parallel = citation.get('true_by_parallel', False)
            
            print(f"Citation: {citation_text}")
            print(f"  Should be true_by_parallel: {should_be_true_by_parallel}")
            print(f"  Actual true_by_parallel: {actual_true_by_parallel}")
            print(f"  Match: {should_be_true_by_parallel == actual_true_by_parallel}")
            print()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()









