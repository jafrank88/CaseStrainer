#!/usr/bin/env python3
"""
Test script to test PDF upload with canonical information fix
"""

import requests
import json
import time

def test_pdf_upload():
    """Test PDF upload with a known verifiable citation"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test with a simple text that contains a known verifiable citation
    test_data = {
        "type": "text",
        "text": "The court held in United States v. Caraway, 534 F.3d 1290 (10th Cir. 2008), that the defendant's rights were violated."
    }
    
    print("🧪 Testing PDF/Text upload with canonical information fix...")
    print(f"URL: {url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! API Response:")
            print(json.dumps(result, indent=2))
            
            # Check if we got citations
            if 'citations' in result and result['citations']:
                print("\n🔍 CANONICAL INFORMATION ANALYSIS:")
                for i, citation in enumerate(result['citations']):
                    print(f"\nCitation {i + 1}:")
                    print(f"  Citation: {citation.get('citation', 'N/A')}")
                    print(f"  Canonical Name: '{citation.get('canonical_name', 'N/A')}'")
                    print(f"  Canonical Date: '{citation.get('canonical_date', 'N/A')}'")
                    print(f"  Extracted Case Name: '{citation.get('extracted_case_name', 'N/A')}'")
                    print(f"  Extracted Date: '{citation.get('extracted_date', 'N/A')}'")
                    print(f"  Verified: {citation.get('verified', False)}")
                    print(f"  URL: '{citation.get('url', 'N/A')}'")
                    
                    # Check if canonical information is present
                    canonical_name = citation.get('canonical_name')
                    canonical_date = citation.get('canonical_date')
                    
                    if canonical_name and canonical_name != 'N/A':
                        print(f"  ✅ CANONICAL NAME FOUND: {canonical_name}")
                    else:
                        print(f"  ❌ NO CANONICAL NAME")
                        
                    if canonical_date and canonical_date != 'N/A':
                        print(f"  ✅ CANONICAL DATE FOUND: {canonical_date}")
                    else:
                        print(f"  ❌ NO CANONICAL DATE")
            else:
                print("⚠️  No citations found in response")
                
            # Check clusters if available
            if 'clusters' in result and result['clusters']:
                print("\n🔍 CLUSTER ANALYSIS:")
                for i, cluster in enumerate(result['clusters']):
                    print(f"\nCluster {i + 1}:")
                    print(f"  Canonical Name: '{cluster.get('canonical_name', 'N/A')}'")
                    print(f"  Canonical Date: '{cluster.get('canonical_date', 'N/A')}'")
                    print(f"  Extracted Case Name: '{cluster.get('extracted_case_name', 'N/A')}'")
                    print(f"  Extracted Date: '{cluster.get('extracted_date', 'N/A')}'")
                    print(f"  Citations Count: {len(cluster.get('citations', []))}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_upload() 