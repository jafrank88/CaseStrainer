import requests
import json
import time

def test_frontend_progress():
    """Test what the frontend actually receives for progress tracking."""
    
    print("🔍 TESTING FRONTEND PROGRESS INTEGRATION")
    print("=" * 60)
    
    # Test with a small text that should trigger sync processing
    small_text = "Brown v. Board, 347 U.S. 483 (1954). Miranda v. Arizona, 384 U.S. 436 (1966)."
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': small_text}
    
    try:
        print(f"📤 Testing sync processing with: {len(small_text)} characters")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            print("📊 Full Response Structure:")
            print(json.dumps(response_data, indent=2))
            
            print("\n🔍 PROGRESS DATA ANALYSIS:")
            
            # Check top level
            if 'progress_data' in response_data:
                print("✅ Found progress_data at TOP LEVEL")
                progress_data = response_data['progress_data']
                print(f"   Overall progress: {progress_data.get('overall_progress', 'N/A')}%")
                print(f"   Elapsed time: {progress_data.get('elapsed_time', 'N/A')}s")
                print(f"   Current step: {progress_data.get('current_message', 'N/A')}")
            else:
                print("❌ No progress_data at top level")
            
            # Check in result
            if 'result' in response_data and 'progress_data' in response_data['result']:
                print("✅ Found progress_data in RESULT")
                progress_data = response_data['result']['progress_data']
                print(f"   Overall progress: {progress_data.get('overall_progress', 'N/A')}%")
                print(f"   Elapsed time: {progress_data.get('elapsed_time', 'N/A')}s")
                print(f"   Current step: {progress_data.get('current_message', 'N/A')}")
                print(f"   Steps: {len(progress_data.get('steps', []))}")
                
                # Show step details
                for i, step in enumerate(progress_data.get('steps', []), 1):
                    print(f"     Step {i}: {step.get('name')} - {step.get('status')} - {step.get('progress', 0)}%")
            else:
                print("❌ No progress_data in result")
            
            # Check in metadata
            if 'metadata' in response_data and 'progress_data' in response_data['metadata']:
                print("✅ Found progress_data in METADATA")
                progress_data = response_data['metadata']['progress_data']
                print(f"   Overall progress: {progress_data.get('overall_progress', 'N/A')}%")
            else:
                print("❌ No progress_data in metadata")
            
            # Save for detailed analysis
            with open('frontend_progress_test.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Full response saved to frontend_progress_test.json")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_progress()
