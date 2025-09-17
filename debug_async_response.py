import requests
import json

def debug_async_response():
    """Debug what the async response actually contains."""
    
    print("🔍 DEBUGGING ASYNC RESPONSE")
    print("=" * 50)
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'url', 'url': test_url}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            print("📊 Full Response Structure:")
            print(json.dumps(response_data, indent=2))
            
            # Save for analysis
            with open('debug_async_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Response saved to debug_async_response.json")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_async_response()
