#!/usr/bin/env python3
"""
Debug script to test single citation and see the exact data structure
"""

import requests
import json

def test_single_citation_debug():
    """Test single citation and show exact data structure"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test with a single citation
    test_data = {
        "type": "text",
        "text": "The court held in United States v. Caraway, 534 F.3d 1290 (10th Cir. 2008), that the defendant's rights were violated."
    }
    
    print("🧪 Testing single citation data structure...")
    print(f"URL: {url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📊 RESPONSE STRUCTURE:")
            print(f"Status: {result.get('status')}")
            print(f"Has citations: {bool(result.get('citations'))}")
            print(f"Citations length: {len(result.get('citations', []))}")
            print(f"Has clusters: {bool(result.get('clusters'))}")
            print(f"Clusters length: {len(result.get('clusters', []))}")
            
            print("\n📋 CITATIONS DATA:")
            for i, citation in enumerate(result.get('citations', [])):
                print(f"\nCitation {i+1}:")
                print(f"  Citation: {citation.get('citation')}")
                print(f"  Verified: {citation.get('verified')}")
                print(f"  Canonical Name: {citation.get('canonical_name')}")
                print(f"  Canonical Date: {citation.get('canonical_date')}")
                print(f"  Extracted Name: {citation.get('extracted_case_name')}")
                print(f"  Extracted Date: {citation.get('extracted_date')}")
                print(f"  URL: {citation.get('url')}")
            
            print("\n🔍 TEMPLATE CONDITIONS:")
            print(f"results exists: {bool(result)}")
            print(f"results.clusters exists: {bool(result.get('clusters'))}")
            print(f"results.clusters length > 0: {len(result.get('clusters', [])) > 0}")
            print(f"results.citations exists: {bool(result.get('citations'))}")
            print(f"results.citations length > 0: {len(result.get('citations', [])) > 0}")
            
            # Check which template condition should be met
            if result.get('clusters') and len(result.get('clusters', [])) > 0:
                print("\n✅ Should show CLUSTERED display")
            elif result.get('citations') and len(result.get('citations', [])) > 0:
                print("\n✅ Should show SINGLE CITATION display (FALLBACK)")
            else:
                print("\n❌ Should show NO RESULTS")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_citation_debug() 