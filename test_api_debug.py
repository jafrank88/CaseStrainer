#!/usr/bin/env python3
"""
Debug test that calls the actual API endpoint
"""

import requests
import json

def test_api_debug():
    """Test the API endpoint with debug info"""
    print("🔍 Debug API Endpoint")
    print("=" * 40)
    
    # Test with simple text first
    simple_text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    
    print(f"Testing simple text ({len(simple_text)} chars, {len(simple_text.split())} words):")
    print(f"Text: {simple_text}")
    
    test_data = {
        "text": simple_text,
        "source_type": "text"
    }
    
    try:
        print("\nSending request...")
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
            print(f"Processor used: {metadata.get('processor_used', 'N/A')}")
            print(f"Task type: {metadata.get('task_type', 'N/A')}")
            print(f"Text length: {metadata.get('text_length', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    
    # Test with standard text
    standard_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"Testing standard text ({len(standard_text)} chars, {len(standard_text.split())} words):")
    print(f"Text preview: {standard_text[:100]}...")
    
    test_data = {
        "text": standard_text,
        "source_type": "text"
    }
    
    try:
        print("\nSending request (5 second timeout)...")
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('metadata', {})
            print(f"✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
            print(f"Processor used: {metadata.get('processor_used', 'N/A')}")
            print(f"Task type: {metadata.get('task_type', 'N/A')}")
            print(f"Text length: {metadata.get('text_length', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 5 seconds")
        print("This confirms the text is not being processed immediately")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_api_debug() 