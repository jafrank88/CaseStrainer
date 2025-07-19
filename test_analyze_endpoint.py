#!/usr/bin/env python3
"""
Test the analyze endpoint directly with citation 534 F.3d 1290
"""

import sys
import os
import requests
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_analyze_endpoint():
    """Test the analyze endpoint with the specific citation"""
    
    print("=== Testing Analyze Endpoint with 534 F.3d 1290 ===")
    
    # Test URL - try both local and production
    urls = [
        "http://localhost:5000/casestrainer/api/analyze",
        "http://localhost/casestrainer/api/analyze"
    ]
    
    # Test payload
    payload = {
        "text": "534 F.3d 1290",
        "type": "text"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for i, url in enumerate(urls):
        print(f"\n--- Testing URL {i+1}: {url} ---")
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Request completed in {processing_time:.2f}s - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Check citations
                citations = data.get('citations', [])
                print(f"Citations found: {len(citations)}")
                
                for j, citation in enumerate(citations):
                    print(f"\nCitation {j+1}:")
                    print(f"  Citation: {citation.get('citation', 'N/A')}")
                    print(f"  Verified: {citation.get('verified', 'N/A')}")
                    print(f"  Source: {citation.get('source', 'N/A')}")
                    print(f"  Canonical name: {citation.get('canonical_name', 'N/A')}")
                    print(f"  Canonical date: {citation.get('canonical_date', 'N/A')}")
                    print(f"  Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"  Extracted date: {citation.get('extracted_date', 'N/A')}")
                    print(f"  URL: {citation.get('url', 'N/A')}")
                    print(f"  Method: {citation.get('method', 'N/A')}")
                    
                    # Check for normalization data
                    if 'normalized_citation' in citation:
                        print(f"  Normalized citation: {citation.get('normalized_citation', 'N/A')}")
                    
                    # Check metadata
                    metadata = citation.get('metadata', {})
                    if metadata:
                        print(f"  Metadata keys: {list(metadata.keys())}")
                        for key, value in metadata.items():
                            print(f"    {key}: {value}")
                
                # Check clusters
                clusters = data.get('clusters', [])
                print(f"\nClusters found: {len(clusters)}")
                
                for j, cluster in enumerate(clusters):
                    print(f"\nCluster {j+1}:")
                    print(f"  Canonical name: {cluster.get('canonical_name', 'N/A')}")
                    print(f"  Canonical date: {cluster.get('canonical_date', 'N/A')}")
                    print(f"  Citations: {len(cluster.get('citations', []))}")
                    
            else:
                print(f"❌ Error response: {response.text}")
                
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"❌ Request failed after {processing_time:.2f}s: {e}")

def test_analyze_with_context():
    """Test with more context around the citation"""
    
    print("\n=== Testing Analyze Endpoint with Context ===")
    
    # Test with context around the citation
    test_texts = [
        "534 F.3d 1290",
        "The court in United States v. Caraway, 534 F.3d 1290 (10th Cir. 2008) held that...",
        "See United States v. Caraway, 534 F.3d 1290, 1295 (10th Cir. 2008).",
        "In 534 F.3d 1290, the Tenth Circuit addressed..."
    ]
    
    url = "http://localhost/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}
    
    for i, text in enumerate(test_texts):
        print(f"\n--- Test {i+1}: {text[:50]}... ---")
        
        payload = {"text": text, "type": "text"}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get('citations', [])
                print(f"Citations found: {len(citations)}")
                
                for citation in citations:
                    print(f"  {citation.get('citation', 'N/A')} -> verified={citation.get('verified', False)}, canonical={citation.get('canonical_name', 'N/A')}")
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_analyze_endpoint()
    test_analyze_with_context() 