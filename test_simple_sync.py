import requests
import json

def test_simple_sync():
    """Test a simple sync request to see if progress tracking is working."""
    
    print("🔍 TESTING SIMPLE SYNC REQUEST")
    print("=" * 60)
    
    # Very small text that should definitely trigger sync processing
    small_text = "Brown v. Board, 347 U.S. 483 (1954)."
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer-Simple-Sync-Test/1.0'
    }
    data = {
        'type': 'text',
        'text': small_text
    }
    
    try:
        print(f"📤 Testing with text: '{small_text}' ({len(small_text)} characters)")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Response received")
            print(f"   Response keys: {list(response_data.keys())}")
            
            # Save response for analysis
            with open('simple_sync_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print(f"   📄 Response saved to simple_sync_response.json")
            
            # Check for progress data
            if 'progress_data' in response_data:
                print(f"   ✅ Progress data found!")
                progress_data = response_data['progress_data']
                print(f"   Status: {progress_data.get('status', 'unknown')}")
                print(f"   Progress: {progress_data.get('overall_progress', 0)}%")
            else:
                print(f"   ❌ No progress data in response")
            
            # Check for citations
            if 'result' in response_data:
                result = response_data['result']
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
            else:
                citations = response_data.get('citations', [])
                clusters = response_data.get('clusters', [])
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_simple_sync()
