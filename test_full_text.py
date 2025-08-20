#!/usr/bin/env python3
"""
Test script to test the full text with all 6 expected citations
"""

import requests
import json

def test_full_text():
    """Test the API with the full text that should have 6 citations"""
    
    # Full test text that should have 6 citations
    test_text = """We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"""
    
    print("🔍 Testing Full Text API")
    print("=" * 40)
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
            
            # Show all citations
            citations = result.get('result', {}).get('citations', [])
            for i, citation in enumerate(citations, 1):
                print(f"\nCitation {i}:")
                print(f"  Text: {citation.get('citation', 'N/A')}")
                print(f"  Case: {citation.get('case_name', 'N/A')}")
                print(f"  Pattern: {citation.get('pattern', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'N/A')}")
                
            # Expected citations
            expected_citations = [
                "136 Wn. App. 104",
                "147 P.3d 641", 
                "69 Wn. App. 621",
                "850 P.2d 527",
                "93 Wn. App. 442",
                "969 P.2d 501"
            ]
            
            print(f"\n📋 Expected citations ({len(expected_citations)}):")
            for citation in expected_citations:
                print(f"  - {citation}")
                
            # Check if all expected citations were found
            found_citations = [c.get('citation', '') for c in citations]
            missing = [c for c in expected_citations if c not in found_citations]
            extra = [c for c in found_citations if c not in expected_citations]
            
            print(f"\n🔍 Analysis:")
            if missing:
                print(f"❌ Missing citations: {missing}")
            else:
                print("✅ All expected citations found!")
                
            if extra:
                print(f"➕ Extra citations found: {extra}")
                
            print(f"\n📈 Success rate: {len([c for c in expected_citations if c in found_citations])}/{len(expected_citations)} = {(len([c for c in expected_citations if c in found_citations])/len(expected_citations)*100):.1f}%")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_text()
