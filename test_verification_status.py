#!/usr/bin/env python3
"""
Test script to show complete verification status and understand discrepancies
"""

import requests
import json

def test_verification_status():
    """Test the full verification process to understand discrepancies"""
    
    # Test with the full problematic text
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact. In re Marriage of Black, 188 Wn.2d 114, 392 P.3d 1041 (2017); 
In re Vulnerable Adult Petition for Knight, 178 Wn. App. 929, 317 P.3d 1068 (2014). We also 
review de novo the meaning of a statute. Blackmon v. Blackmon, 155 Wn. App. 715, 230 P.3d 233 (2010)."""
    
    print("🔍 Testing Full Text Verification Status")
    print("=" * 60)
    print(f"Test text length: {len(test_text)} characters")
    print(f"Test text preview: {test_text[:100]}...")
    print()
    
    try:
        # Test the API endpoint
        url = "http://localhost:5000/casestrainer/api/analyze"
        payload = {
            "text": test_text,
            "type": "text"
        }
        
        print(f"📡 Sending request to: {url}")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'No message')}")
            print(f"📊 Citations found: {len(result.get('result', {}).get('citations', []))}")
            print(f"📊 Clusters found: {len(result.get('result', {}).get('clusters', []))}")
            
            # Show all citations with complete verification details
            citations = result.get('result', {}).get('citations', [])
            print(f"\n🔍 Complete Citation Verification Details:")
            for i, citation in enumerate(citations, 1):
                print(f"\nCitation {i}:")
                print(f"  Text: {citation.get('citation', 'N/A')}")
                print(f"  Case Name: {citation.get('case_name', 'N/A')}")
                print(f"  Extracted Case: {citation.get('extracted_case_name', 'N/A')}")
                print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"  Extracted Date: {citation.get('extracted_date', 'N/A')}")
                print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'N/A')}")
                print(f"  True by Parallel: {citation.get('true_by_parallel', 'N/A')}")
                print(f"  Source: {citation.get('source', 'N/A')}")
                print(f"  URL: {citation.get('canonical_url', 'N/A')}")
                print(f"  Confidence: {citation.get('confidence', 'N/A')}")
                print(f"  Method: {citation.get('method', 'N/A')}")
                
                # Check metadata
                if citation.get('metadata'):
                    print(f"  Metadata:")
                    for key, value in citation['metadata'].items():
                        print(f"    {key}: {value}")
            
            # Show cluster information
            clusters = result.get('result', {}).get('clusters', [])
            print(f"\n🔍 Cluster Information:")
            for i, cluster in enumerate(clusters, 1):
                print(f"\nCluster {i}:")
                print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
                print(f"  Year: {cluster.get('year', 'N/A')}")
                print(f"  Size: {cluster.get('size', 'N/A')}")
                print(f"  Citations: {cluster.get('citations', [])}")
                print(f"  Type: {cluster.get('cluster_type', 'N/A')}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification_status()
