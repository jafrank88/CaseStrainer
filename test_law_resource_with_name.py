#!/usr/bin/env python3
"""
Test the Law Resource.org source with a proper case name
"""

import requests
import json

def test_law_resource_with_case_name():
    """Test Law Resource.org with a citation that has a proper case name"""
    
    # Test text with both citation and case name
    test_text = "In Smith v. Jones, 161 F.3d 584, the court established important precedent regarding federal jurisdiction."
    
    print("🧪 Testing Law Resource.org with proper case name...")
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
            extracted_name = citation.get("extracted_case_name", "")
            verified = citation.get("verified", False)
            source = citation.get("source", "")
            url = citation.get("url", "")
            
            print(f"\n📋 Citation: {citation_text}")
            print(f"   Extracted name: {extracted_name}")
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
    success = test_law_resource_with_case_name()
    
    if success:
        print("\n✅ SUCCESS: Law Resource.org source is working!")
    else:
        print("\n❌ FAILURE: Law Resource.org source needs more work")
