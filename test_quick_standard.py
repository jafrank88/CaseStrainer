#!/usr/bin/env python3
"""
Quick test with shorter timeout for standard citations
"""

import requests
import json

def test_quick_standard():
    """Test with shorter timeout"""
    print("⚡ Quick Test - Standard Citations")
    print("=" * 40)
    
    # Standard test text with multiple citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    test_data = {
        "text": test_text,
        "source_type": "text"
    }
    
    try:
        print("Sending request to local API (15 second timeout)...")
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response Successful!")
            
            citations = result.get('citations', [])
            metadata = result.get('metadata', {})
            
            print(f"\n📚 Found {len(citations)} citations:")
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. Citation: {citation.get('citation')}")
                print(f"     Extracted case name: {citation.get('extracted_case_name')}")
                print(f"     Extracted date: {citation.get('extracted_date')}")
                print(f"     Verified: {citation.get('verified')}")
                print(f"     Source: {citation.get('source')}")
                print()
            
            print(f"⏱️  Processing time: {metadata.get('processing_time', 'N/A')} seconds")
            print(f"🔧 Processor: {metadata.get('processor_used', 'N/A')}")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 15 seconds")
        print("This suggests the verification process is taking too long")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_quick_standard() 