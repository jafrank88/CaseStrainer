#!/usr/bin/env python3

import requests
import json

def test_verification_status():
    """Test verification status discrepancy between citations and clusters."""
    
    # Text with multiple citations that should be verified
    text = """
    The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016) that standing requirements cannot be erased.
    
    In Raines v. Byrd, 521 U.S. 811, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997), the Court addressed legislative standing.
    
    The decision in Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954) was landmark.
    """
    
    print("VERIFICATION STATUS TEST")
    print("=" * 60)
    print(f"Text: {text[:100]}...")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Found {len(citations)} citations and {len(clusters)} clusters")
            print()
            
            # Analyze citation verification status
            print("CITATION VERIFICATION STATUS:")
            print("-" * 40)
            verified_citations = 0
            unverified_citations = 0
            true_by_parallel_citations = 0
            
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                verified = citation.get('verified', False)
                true_by_parallel = citation.get('true_by_parallel', False)
                verification_completed = citation.get('verification_completed', False)
                canonical_name = citation.get('canonical_name', 'N/A')
                canonical_url = citation.get('canonical_url', 'N/A')
                
                status_icon = "✅" if verified else "❌"
                parallel_icon = "🔗" if true_by_parallel else "⭕"
                
                print(f"{i:2d}. {status_icon} {parallel_icon} {citation_text}")
                print(f"     Case: {case_name}")
                print(f"     Verified: {verified}, True by Parallel: {true_by_parallel}")
                print(f"     Verification Completed: {verification_completed}")
                print(f"     Canonical Name: {canonical_name}")
                print(f"     Canonical URL: {canonical_url[:50]}..." if len(str(canonical_url)) > 50 else f"     Canonical URL: {canonical_url}")
                print()
                
                if verified:
                    verified_citations += 1
                else:
                    unverified_citations += 1
                    
                if true_by_parallel:
                    true_by_parallel_citations += 1
            
            print(f"CITATION SUMMARY:")
            print(f"  Verified: {verified_citations}")
            print(f"  Unverified: {unverified_citations}")
            print(f"  True by Parallel: {true_by_parallel_citations}")
            print()
            
            # Analyze cluster verification status
            print("CLUSTER VERIFICATION STATUS:")
            print("-" * 40)
            for i, cluster in enumerate(clusters, 1):
                cluster_case_name = cluster.get('case_name', 'N/A')
                cluster_citations = cluster.get('citations', [])
                verified_in_cluster = cluster.get('verified', False)
                any_verified = cluster.get('any_verified', False)
                
                print(f"Cluster {i}: {cluster_case_name}")
                print(f"  Citations: {cluster_citations}")
                print(f"  Cluster Verified: {verified_in_cluster}")
                print(f"  Any Verified: {any_verified}")
                
                # Check individual citation status within cluster
                cluster_verified_count = 0
                cluster_parallel_count = 0
                for citation_text in cluster_citations:
                    # Find matching citation in citations list
                    matching_citation = next((c for c in citations if c.get('citation') == citation_text), None)
                    if matching_citation:
                        if matching_citation.get('verified'):
                            cluster_verified_count += 1
                        if matching_citation.get('true_by_parallel'):
                            cluster_parallel_count += 1
                
                print(f"  Individual Citations Verified: {cluster_verified_count}/{len(cluster_citations)}")
                print(f"  Individual Citations True by Parallel: {cluster_parallel_count}/{len(cluster_citations)}")
                print()
            
            # Check for discrepancies
            print("DISCREPANCY ANALYSIS:")
            print("-" * 40)
            if unverified_citations == len(citations):
                print("🚨 ISSUE: ALL citations are unverified!")
                print("   This suggests verification is not working properly.")
            
            if true_by_parallel_citations == 0:
                print("🚨 ISSUE: NO citations marked as 'true_by_parallel'!")
                print("   This suggests parallel citation verification is not working.")
            
            if any(cluster.get('any_verified', False) for cluster in clusters):
                print("🚨 DISCREPANCY: Some clusters show verification but individual citations don't!")
                print("   This suggests verification status is not being propagated to individual citations.")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_verification_status()
