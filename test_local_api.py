#!/usr/bin/env python3
"""
Test the local API with the fixes
"""

import requests
import json

def test_local_api():
    """Test the local API"""
    print("🧪 Testing Local API")
    print("=" * 30)
    
    # Test data
    test_data = {
        "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    }
    
    try:
        # Send request to local API
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response:")
            print(json.dumps(result, indent=2))
            
            # Check for citations
            if 'citations' in result:
                citations = result['citations']
                print(f"\n📚 Found {len(citations)} citations:")
                
                for i, citation in enumerate(citations, 1):
                    print(f"  {i}. Citation: {citation.get('citation', 'N/A')}")
                    print(f"     Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"     Extracted date: {citation.get('extracted_date', 'N/A')}")
                    print(f"     Verified: {citation.get('verified', 'N/A')}")
                    print()
            
            return True
        else:
            print(f"❌ API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_local_api() 