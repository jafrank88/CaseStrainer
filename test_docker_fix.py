#!/usr/bin/env python3
"""
Test script to verify that the latest code with context boundary fixes
is working in the Docker containers.
"""

import requests
import json
import time

def test_case_name_bleeding_fix():
    """Test that City of Bellevue v. Lorang bleeding bug is fixed"""
    
    # Test text with the problematic citation cluster
    test_text = """
    In the case of Young v. Pierce County, 120 Wn. App. 175, 188, 84 P.3d 927 (2004), 
    the court held that proper notice was required. However, in Berst v. Snohomish County, 
    114 Wn. App. 245, 57 P.3d 273 (2002), the decision was different.
    """
    
    print("🧪 Testing case name bleeding fix...")
    print(f"📝 Test text: {test_text.strip()}")
    
    # Send to API
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        citations = result.get("citations", [])
        
        print(f"\n📊 Found {len(citations)} citations")
        
        for citation in citations:
            citation_text = citation.get("citation", "")
            extracted_name = citation.get("extracted_case_name", "")
            canonical_name = citation.get("canonical_name", "")
            
            print(f"\n📋 Citation: {citation_text}")
            print(f"   Extracted: {extracted_name}")
            print(f"   Canonical: {canonical_name}")
            
            # Check for the bleeding bug
            if citation_text in ["114 Wn. App. 245", "57 P.3d 273"]:
                if "City of Bellevue v. Lorang" in extracted_name:
                    print("   ❌ BUG DETECTED: City of Bellevue bleeding!")
                    return False
                elif "Berst v. Snohomish County" in extracted_name or "Berst v. Snohomish County" in canonical_name:
                    print("   ✅ GOOD: Correct case name extracted")
                else:
                    print("   ⚠️  UNEXPECTED: Different case name extracted")
            
            elif citation_text in ["120 Wn. App. 175", "84 P.3d 927"]:
                if "Young v. Pierce County" in extracted_name:
                    print("   ✅ GOOD: Correct case name extracted")
                else:
                    print("   ❌ WRONG: Expected 'Young v. Pierce County'")
        
        print("\n🎉 Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 TESTING IF LATEST CODE IS IN DOCKER CONTAINERS")
    print("=" * 60)
    
    success = test_case_name_bleeding_fix()
    
    if success:
        print("\n✅ SUCCESS: Latest code appears to be working!")
    else:
        print("\n❌ FAILURE: Old code still running in containers")
