#!/usr/bin/env python3
"""
Test the case name bleeding fix with the live API
"""

import requests
import json

def test_bleeding_fix():
    """Test if the case name bleeding bug is fixed in production"""
    
    # Test text that was causing bleeding
    test_text = """
    In the case of Young v. Pierce County, 120 Wn. App. 175, 188, 84 P.3d 927 (2004), 
    the court held that proper notice was required. However, in Berst v. Snohomish County, 
    114 Wn. App. 245, 57 P.3d 273 (2002), the decision was different.
    """
    
    print("🧪 Testing case name bleeding fix with live API...")
    print(f"📝 Test text: {test_text.strip()}")
    
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
        
        # Check the problematic citations
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
                elif "Berst v. Snohomish County" in extracted_name or "Berst" in extracted_name:
                    print("   ✅ GOOD: Correct case name extracted")
                else:
                    print(f"   ⚠️  UNEXPECTED: Different case name extracted")
        
        print("\n🎉 Test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_bleeding_fix()
    
    if success:
        print("\n✅ SUCCESS: Case name bleeding bug appears to be fixed!")
    else:
        print("\n❌ FAILURE: Case name bleeding bug still present")
