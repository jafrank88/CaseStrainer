#!/usr/bin/env python3
"""
Test the actual API request with detailed response analysis.
"""

import requests
import json

def test_actual_api_request():
    """Test the actual API request and analyze the response in detail."""
    
    # Test document - same as our successful simulation
    test_text = """
    Legal Document for Actual API Test
    
    Important cases:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    """ + "\n\nAdditional content. " * 1000
    
    print("🌐 Testing Actual API Request")
    print("=" * 60)
    print(f"📄 Document size: {len(test_text)} characters ({len(test_text)/1024:.1f} KB)")
    print("📝 Expected: Should find 9 citations with sync_fallback mode")
    print()
    
    try:
        print("📤 Making actual HTTP request...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text},
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print(f"📊 Response Size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n📋 Response Analysis:")
                print(f"  Response type: {type(data)}")
                print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                if isinstance(data, dict):
                    print(f"  Success: {data.get('success')}")
                    print(f"  Message: {data.get('message')}")
                    print(f"  Has task_id: {'task_id' in data}")
                    print(f"  Has citations: {'citations' in data}")
                    print(f"  Citations count: {len(data.get('citations', []))}")
                    print(f"  Has clusters: {'clusters' in data}")
                    print(f"  Clusters count: {len(data.get('clusters', []))}")
                    print(f"  Has metadata: {'metadata' in data}")
                    print(f"  Has progress_data: {'progress_data' in data}")
                    
                    if 'metadata' in data:
                        metadata = data['metadata']
                        processing_mode = metadata.get('processing_mode', 'N/A')
                        print(f"  Processing mode: {processing_mode}")
                        print(f"  Source: {metadata.get('source', 'N/A')}")
                        print(f"  Fallback reason: {metadata.get('fallback_reason', 'N/A')}")
                    
                    if 'progress_data' in data:
                        progress = data['progress_data']
                        print(f"  Progress status: {progress.get('status', 'N/A')}")
                        print(f"  Progress message: {progress.get('current_message', 'N/A')}")
                    
                    # Check citations
                    citations = data.get('citations', [])
                    if len(citations) > 0:
                        print(f"\n✅ SUCCESS: {len(citations)} citations found!")
                        print("📋 Sample citations:")
                        for i, citation in enumerate(citations[:3]):
                            citation_text = citation.get('citation', 'N/A')
                            case_name = citation.get('extracted_case_name', 'N/A')
                            print(f"  {i+1}. {citation_text} - {case_name}")
                        return True
                    else:
                        print(f"\n❌ FAILURE: No citations found")
                        
                        # Debug why no citations
                        print("\n🔍 Debugging why no citations found:")
                        print(f"  Raw response data: {json.dumps(data, indent=2)[:500]}...")
                        return False
                else:
                    print(f"❌ Response is not a dictionary: {data}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return False
        else:
            print(f"❌ HTTP request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the actual API test."""
    success = test_actual_api_request()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Actual API request test")
    return success

if __name__ == "__main__":
    main()
