#!/usr/bin/env python3
"""
Test parallel citation propagation to see why true_by_parallel is not working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_parallel_propagation():
    """Test parallel citation propagation."""
    
    # Text with Raines citations where L.Ed.2d should be verified
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)) that standing requirements cannot be erased.'
    
    print("🔍 TESTING PARALLEL CITATION PROPAGATION")
    print("=" * 60)
    print(f"📝 Text: {text}")
    print()
    
    # Call the API
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"type": "text", "text": text},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"📊 Found {len(citations)} citations in {len(clusters)} clusters")
            print()
            
            # Analyze each citation
            print("📋 CITATION ANALYSIS:")
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', 'N/A')
                case_name = citation.get('case_name', 'N/A')
                verified = citation.get('verified', False)
                true_by_parallel = citation.get('true_by_parallel', False)
                
                print(f"{i}. {citation_text}")
                print(f"   Case: {case_name}")
                print(f"   Verified: {verified}")
                print(f"   True by parallel: {true_by_parallel}")
                
                # Check verification status
                if verified:
                    print(f"   ✅ VERIFIED")
                elif true_by_parallel:
                    print(f"   🔗 TRUE BY PARALLEL")
                else:
                    print(f"   ❌ UNVERIFIED")
                print()
            
            # Analyze clusters
            print("🔗 CLUSTER ANALYSIS:")
            for i, cluster in enumerate(clusters, 1):
                cluster_name = cluster.get('case_name', 'N/A')
                cluster_citations = cluster.get('citations', [])
                
                print(f"{i}. Cluster: {cluster_name}")
                print(f"   Citations: {len(cluster_citations)}")
                
                # Check if cluster has any verified citations
                verified_count = 0
                unverified_count = 0
                parallel_count = 0
                
                for cit in cluster_citations:
                    if isinstance(cit, dict):
                        if cit.get('verified', False):
                            verified_count += 1
                        elif cit.get('true_by_parallel', False):
                            parallel_count += 1
                        else:
                            unverified_count += 1
                    else:
                        # Handle string citations
                        # Find the corresponding citation object
                        for full_cit in citations:
                            if full_cit.get('citation') == cit:
                                if full_cit.get('verified', False):
                                    verified_count += 1
                                elif full_cit.get('true_by_parallel', False):
                                    parallel_count += 1
                                else:
                                    unverified_count += 1
                                break
                
                print(f"   Verified: {verified_count}")
                print(f"   True by parallel: {parallel_count}")
                print(f"   Unverified: {unverified_count}")
                
                if verified_count > 0 and unverified_count > 0:
                    print(f"   ⚠️  ISSUE: Cluster has {verified_count} verified but {unverified_count} unverified citations!")
                elif verified_count > 0:
                    print(f"   ✅ All citations properly verified/propagated")
                else:
                    print(f"   ❌ No verified citations in cluster")
                print()
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_parallel_propagation()
