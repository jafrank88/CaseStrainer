#!/usr/bin/env python3
"""
Test the exact response structure to debug the "No Citations" issue.
"""

import requests
import json

def test_response_structure():
    """Test the exact response structure from the API."""
    
    print("🔍 Testing API Response Structure")
    print("=" * 50)
    
    # Simple test with obvious citation
    test_text = "The case State v. Johnson, 160 Wn.2d 500 (2007) is important."
    
    try:
        print(f"📤 Submitting test text: {test_text}")
        
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=30
        )
        
        print(f"\n📊 Response Analysis:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        print(f"   Response Size: {len(response.text)} characters")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response Text: {response.text}")
            return False
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Raw Response: {response.text[:500]}...")
            return False
        
        print(f"\n🔍 Response Structure Analysis:")
        print(f"   Top-level keys: {list(data.keys())}")
        
        # Check for citations at different levels
        citations_top = data.get('citations', [])
        citations_result = data.get('result', {}).get('citations', []) if 'result' in data else []
        
        print(f"\n📋 Citations Analysis:")
        print(f"   Citations at top level: {len(citations_top)}")
        print(f"   Citations in result: {len(citations_result)}")
        
        if len(citations_top) > 0:
            print(f"   ✅ Citations found at top level:")
            for i, citation in enumerate(citations_top[:3], 1):
                print(f"     {i}. {citation.get('citation', 'N/A')}")
        
        if len(citations_result) > 0:
            print(f"   ⚠️ Citations found in nested result:")
            for i, citation in enumerate(citations_result[:3], 1):
                print(f"     {i}. {citation.get('citation', 'N/A')}")
        
        if len(citations_top) == 0 and len(citations_result) == 0:
            print(f"   ❌ No citations found at any level")
            
            # Debug: Check if there's any citation data anywhere
            print(f"\n🔍 Deep Structure Analysis:")
            def find_citations_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_path = f"{path}.{key}" if path else key
                        if key == 'citations' and isinstance(value, list):
                            print(f"     Found citations at: {new_path} (length: {len(value)})")
                        find_citations_recursive(value, new_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_citations_recursive(item, f"{path}[{i}]")
            
            find_citations_recursive(data)
        
        # Check success status
        success = data.get('success', False)
        print(f"\n📊 Processing Status:")
        print(f"   Success: {success}")
        print(f"   Message: {data.get('message', 'N/A')}")
        print(f"   Processing Mode: {data.get('metadata', {}).get('processing_mode', 'N/A')}")
        
        # Check for errors
        if 'error' in data:
            print(f"   ❌ Error: {data['error']}")
        
        # Print full response for debugging (truncated)
        print(f"\n📄 Full Response (first 1000 chars):")
        print(json.dumps(data, indent=2)[:1000] + "...")
        
        return len(citations_top) > 0 or len(citations_result) > 0
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_input_methods():
    """Test different ways of submitting input to see if that affects results."""
    
    print(f"\n🔄 Testing Different Input Methods")
    print("=" * 50)
    
    test_citation = "State v. Johnson, 160 Wn.2d 500 (2007)"
    
    test_methods = [
        {
            "name": "JSON with text field",
            "data": {"text": f"The case {test_citation} is important.", "type": "text"}
        },
        {
            "name": "JSON with different text",
            "data": {"text": f"Legal precedent: {test_citation}.", "type": "text"}
        }
    ]
    
    for method in test_methods:
        print(f"\n📝 Testing: {method['name']}")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json=method['data'],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get('citations', [])
                success = data.get('success', False)
                
                print(f"   Status: {response.status_code}")
                print(f"   Success: {success}")
                print(f"   Citations: {len(citations)}")
                
                if len(citations) > 0:
                    print(f"   ✅ Found: {citations[0].get('citation', 'N/A')}")
                else:
                    print(f"   ❌ No citations found")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")

def main():
    """Run response structure debugging."""
    
    print("🚀 Debugging API Response Structure")
    print("=" * 60)
    
    structure_ok = test_response_structure()
    test_different_input_methods()
    
    print("\n" + "=" * 60)
    print("📋 RESPONSE STRUCTURE DEBUG RESULTS")
    print("=" * 60)
    
    if structure_ok:
        print("✅ Citations are being returned by the API")
        print("🔍 If you're seeing 'No Citations' in the frontend:")
        print("   - Check browser console for JavaScript errors")
        print("   - Verify frontend is reading response.citations correctly")
        print("   - Check network tab to see actual API responses")
    else:
        print("❌ Citations are NOT being returned by the API")
        print("🔍 Issue is in the backend processing pipeline:")
        print("   - Citation extraction may be failing")
        print("   - Response structure may be incorrect")
        print("   - Processing pipeline may have errors")
    
    return structure_ok

if __name__ == "__main__":
    main()
