#!/usr/bin/env python3
"""
Test the analyze endpoint with Washington citations (Wn.2d, Wn.App., etc.)
"""

import sys
import os
import requests
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_washington_citations():
    """Test Washington citations through the analyze endpoint"""
    
    print("=== Testing Washington Citations Through Analyze Endpoint ===")
    
    # Test the standard Washington citations from the test text
    test_texts = [
        # Individual citations
        "200 Wn.2d 72",
        "514 P.3d 643", 
        "171 Wn.2d 486",
        "256 P.3d 321",
        "146 Wn.2d 1",
        "43 P.3d 4",
        
        # Full standard test text
        "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)",
        
        # Washington Court of Appeals citations
        "123 Wn.App. 456",
        "456 P.3d 789",
        "State v. Smith, 123 Wn.App. 456, 460, 456 P.3d 789 (2020)"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n--- Test {i+1}: {text[:50]}... ---")
        
        try:
            # Call the analyze endpoint
            response = requests.post(
                'http://localhost:5000/casestrainer/api/analyze',
                json={'text': text, 'type': 'text'},
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get('citations', [])
                print(f"✅ Citations found: {len(citations)}")
                
                for j, citation in enumerate(citations):
                    print(f"\n  Citation {j+1}:")
                    print(f"    Citation: {citation.get('citation', 'N/A')}")
                    print(f"    Verified: {citation.get('verified', 'N/A')}")
                    print(f"    Source: {citation.get('source', 'N/A')}")
                    print(f"    Canonical name: {citation.get('canonical_name', 'N/A')}")
                    print(f"    Canonical date: {citation.get('canonical_date', 'N/A')}")
                    print(f"    Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"    Extracted date: {citation.get('extracted_date', 'N/A')}")
                    print(f"    Method: {citation.get('method', 'N/A')}")
                    
                    # Check for normalization data
                    if 'normalized_citation' in citation:
                        print(f"    Normalized citation: {citation.get('normalized_citation', 'N/A')}")
                    
                    # Check metadata for normalization info
                    metadata = citation.get('metadata', {})
                    if metadata:
                        print(f"    Metadata keys: {list(metadata.keys())}")
                        for key, value in metadata.items():
                            if key in ['normalized_citation', 'citation_variants', 'reporter_mapping']:
                                print(f"      {key}: {value}")
                
                # Check clusters
                clusters = data.get('clusters', [])
                if clusters:
                    print(f"\n  Clusters found: {len(clusters)}")
                    for j, cluster in enumerate(clusters):
                        print(f"    Cluster {j+1}: {cluster.get('canonical_name', 'N/A')} ({cluster.get('canonical_date', 'N/A')})")
                
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Failed: {e}")

def test_washington_normalization():
    """Test specific Washington citation normalization patterns"""
    
    print("\n=== Testing Washington Citation Normalization ===")
    
    # Test different Washington citation formats
    washington_citations = [
        "200 Wn.2d 72",
        "200 Wn. 2d 72",  # With space
        "200 Wn.2d 72, 73",  # With pinpoint
        "200 Wn.2d 72 (2022)",  # With year
        "123 Wn.App. 456",
        "123 Wn. App. 456",  # With space
        "456 P.3d 789",
        "456 P. 3d 789",  # With space
        "171 Wn.2d 486, 493, 256 P.3d 321",  # Parallel citations
        "146 Wn.2d 1, 9, 43 P.3d 4"  # Another parallel
    ]
    
    for citation in washington_citations:
        print(f"\n--- Testing: {citation} ---")
        
        try:
            response = requests.post(
                'http://localhost:5000/casestrainer/api/analyze',
                json={'text': citation, 'type': 'text'},
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get('citations', [])
                print(f"Citations found: {len(citations)}")
                
                for citation_obj in citations:
                    print(f"  {citation_obj.get('citation', 'N/A')} -> verified={citation_obj.get('verified', False)}")
                    if citation_obj.get('canonical_name'):
                        print(f"    Canonical: {citation_obj.get('canonical_name')} ({citation_obj.get('canonical_date', 'N/A')})")
                
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_washington_citations()
    test_washington_normalization() 