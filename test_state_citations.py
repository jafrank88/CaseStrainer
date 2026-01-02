#!/usr/bin/env python3
"""Test State v. citations to debug why they're not showing"""

import requests
import json

def test_state_citations():
    """Test State v. citations"""
    
    print("Testing State v. citations...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test with various State v. citations
    test_text = """
    State v. Johnson, 123 Wn.2d 456 (2020). The defendant was charged with burglary.
    State v. Smith, 456 P.3d 789 (2021). This case established precedent.
    State v. Anderson, 789 F.3d 123 (2019). The court ruled on constitutional grounds.
    """
    
    # Test with JSON payload
    test_data = {
        "text": test_text,
        "type": "text",
        "enable_verification": False  # Disable verification to speed up test
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"\nFound {len(citations)} citations and {len(clusters)} clusters")
            
            if citations:
                print("\nCitations found:")
                for i, citation in enumerate(citations, 1):
                    print(f"\n{i}. Citation: {citation.get('citation', 'N/A')}")
                    print(f"   Case name: {citation.get('case_name', 'N/A')}")
                    print(f"   Extracted name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"   Verified: {citation.get('verified', False)}")
                    print(f"   Source: {citation.get('source', 'N/A')}")
                    print(f"   Method: {citation.get('method', 'N/A')}")
            else:
                print("\n❌ NO CITATIONS FOUND!")
                print("This indicates a problem with citation extraction.")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_state_citations()
