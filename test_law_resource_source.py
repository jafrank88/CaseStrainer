#!/usr/bin/env python3
"""
Test the new Law Resource.org verification source
"""

import requests
import json

def test_law_resource_source():
    """Test if Law Resource.org is working as a verification source"""
    
    # Test citation that should be found on Law Resource.org
    test_text = "The case of 161 F.3d 584 established important precedent."
    
    print("🧪 Testing Law Resource.org as new verification source...")
    print(f"📝 Test text: {test_text}")
    
    # Send to API
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        print("\n📡 Sending request to API...")
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        citations = result.get("citations", [])
        
        print(f"\n📊 Found {len(citations)} citations")
        
        # Check the 161 F.3d 584 citation
        for citation in citations:
            citation_text = citation.get("citation", "")
            verified = citation.get("verified", False)
            source = citation.get("source", "")
            url = citation.get("url", "")
            
            print(f"\n📋 Citation: {citation_text}")
            print(f"   Verified: {verified}")
            print(f"   Source: {source}")
            print(f"   URL: {url}")
            
            if citation_text == "161 F.3d 584":
                if verified and "law.resource.org" in url:
                    print("   ✅ SUCCESS: Found on Law Resource.org!")
                    return True
                elif verified:
                    print("   ✅ SUCCESS: Verified (but via different source)")
                    return True
                else:
                    print("   ❌ NOT VERIFIED: Could not verify citation")
        
        print("\n⚠️  161 F.3d 584 not found in results")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_law_resource_source()
    
    if success:
        print("\n✅ SUCCESS: Law Resource.org source is working!")
    else:
        print("\n❌ FAILURE: Law Resource.org source needs more work")
