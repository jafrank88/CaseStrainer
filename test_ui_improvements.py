#!/usr/bin/env python3
"""
Test the UI improvements - check if "Verifying Source" is removed and "Extracted from Document" shows proper data
"""

import requests
import json

def test_ui_improvements():
    """Test the UI changes"""
    
    test_text = """
    In Department of Ecology v. Campbell & Gwinn, L.L.C., 146 Wn.2d 1 (2002), the court addressed environmental matters.
    In another case, 43 P.3d 4 (2002), the court considered similar issues.
    """
    
    print(f"🔍 Testing UI improvements with test document...")
    print(f"Text length: {len(test_text)} characters")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 API Response:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            print(f"Citations found: {len(result.get('citations', []))}")
            
            # Check the actual data structure for extracted case names
            citations = result.get('citations', [])
            for i, citation in enumerate(citations):
                print(f"\n--- Citation {i+1} ---")
                print(f"Citation: {citation.get('citation', 'N/A')}")
                print(f"Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"Extracted date: {citation.get('extracted_date', 'N/A')}")
                print(f"Canonical name: {citation.get('canonical_name', 'N/A')}")
                print(f"Canonical date: {citation.get('canonical_date', 'N/A')}")
                print(f"Verified: {citation.get('verified', False)}")
                
            # Check clusters if any
            clusters = result.get('clusters', [])
            if clusters:
                print(f"\n📚 Clusters found: {len(clusters)}")
                for i, cluster in enumerate(clusters):
                    print(f"\n--- Cluster {i+1} ---")
                    rep_citation = cluster.get('citations', [{}])[0]
                    print(f"Cluster extracted name: {rep_citation.get('extracted_case_name', 'N/A')}")
                    print(f"Cluster extracted date: {rep_citation.get('extracted_date', 'N/A')}")
                    print(f"Cluster canonical name: {rep_citation.get('canonical_name', 'N/A')}")
                    print(f"Cluster canonical date: {rep_citation.get('canonical_date', 'N/A')}")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ui_improvements()
