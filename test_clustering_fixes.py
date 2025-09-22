#!/usr/bin/env python3

import requests
import json

def test_clustering_fixes():
    """Test the clustering fixes for parallel citations and case name propagation."""
    
    # Use the same text that was showing clustering issues
    test_text = '''Certified questions are questions of law that this court reviews de novo and in light of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018).'''
    
    print("CLUSTERING FIXES TEST")
    print("=" * 60)
    print("Testing parallel citation clustering and case name propagation...")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Found {len(citations)} citations and {len(clusters)} clusters")
            print()
            
            # Test Case 1: Lopez Demetrio parallel citations should be clustered together
            print("TEST CASE 1: Lopez Demetrio v. Sakuma Bros. Farms")
            print("-" * 50)
            
            lopez_citations = []
            for citation in citations:
                citation_text = citation.get('citation', '')
                canonical_name = citation.get('canonical_name', '') or ''
                if 'Lopez Demetrio' in canonical_name or 'Sakuma Bros' in canonical_name:
                    lopez_citations.append(citation)
                    print(f"Citation: {citation_text}")
                    print(f"  Canonical Name: {canonical_name}")
                    print(f"  Extracted Name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"  Cluster Case Name: {citation.get('cluster_case_name', 'N/A')}")
                    print(f"  Parallel Citations: {citation.get('parallel_citations', [])}")
                    print()
            
            # Check if they're in the same cluster
            lopez_cluster_ids = set()
            for citation in lopez_citations:
                cluster_id = citation.get('metadata', {}).get('cluster_id', 'N/A')
                lopez_cluster_ids.add(cluster_id)
            
            if len(lopez_cluster_ids) == 1:
                print("✅ SUCCESS: Lopez Demetrio citations are in the same cluster!")
            else:
                print(f"❌ ISSUE: Lopez Demetrio citations are in {len(lopez_cluster_ids)} different clusters: {lopez_cluster_ids}")
            
            print()
            
            # Test Case 2: Check cluster case names use canonical names
            print("TEST CASE 2: Cluster Case Name Propagation")
            print("-" * 50)
            
            for cluster in clusters:
                cluster_case_name = cluster.get('case_name', 'N/A')
                canonical_name = cluster.get('canonical_name', 'N/A')
                
                print(f"Cluster: {cluster.get('cluster_id', 'N/A')}")
                print(f"  Case Name: {cluster_case_name}")
                print(f"  Canonical Name: {canonical_name}")
                print(f"  Citations: {cluster.get('citations', [])}")
                
                # Check if case name uses canonical name when available
                if canonical_name and canonical_name != "N/A":
                    if cluster_case_name == canonical_name:
                        print("  ✅ Case name matches canonical name")
                    elif canonical_name in cluster_case_name or cluster_case_name in canonical_name:
                        print("  ✅ Case name is compatible with canonical name")
                    else:
                        print(f"  ❌ Case name doesn't match canonical name")
                else:
                    print("  ⚠️  No canonical name available")
                print()
            
            # Test Case 3: Check individual citation verification status
            print("TEST CASE 3: Individual Citation Verification")
            print("-" * 50)
            
            verified_count = 0
            total_count = len(citations)
            
            for citation in citations:
                citation_text = citation.get('citation', '')
                verified = citation.get('verified', False)
                canonical_name = citation.get('canonical_name', '')
                
                if verified:
                    verified_count += 1
                    status = "✅ VERIFIED"
                elif canonical_name and canonical_name != "N/A":
                    status = "⚠️  HAS CANONICAL DATA BUT NOT MARKED VERIFIED"
                else:
                    status = "❌ UNVERIFIED"
                
                print(f"{citation_text}: {status}")
            
            print(f"\nVerification Summary: {verified_count}/{total_count} citations verified")
            
            if verified_count > 0:
                print("✅ Some citations are being verified correctly")
            else:
                print("❌ No citations are marked as verified (verification issue)")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_clustering_fixes()
