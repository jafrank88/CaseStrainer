#!/usr/bin/env python3
import requests
import json
import time

def test_health_direct():
    """Test health endpoint directly"""
    print("=== TESTING HEALTH ENDPOINT ===")
    try:
        response = requests.get('http://localhost:5000/casestrainer/api/health', timeout=5)
        print(f"✅ Health endpoint responds - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Health data: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_analyze_text_direct():
    """Test text analysis endpoint directly"""
    print("\n=== TESTING TEXT ANALYSIS ENDPOINT ===")
    
    test_data = {
        "text": "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)",
        "type": "text"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            json=test_data,
            timeout=30
        )
        
        print(f"✅ Text analysis responds - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if it's async or immediate
            if data.get('status') == 'processing' and data.get('task_id'):
                print(f"🔄 Async processing - Task ID: {data['task_id']}")
                return test_task_status(data['task_id'])
            else:
                print("✅ Immediate response")
                return True
        else:
            print(f"❌ Text analysis failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Text analysis error: {e}")
        return False

def test_file_upload_direct():
    """Test file upload endpoint directly"""
    print("\n=== TESTING FILE UPLOAD ENDPOINT ===")
    
    # Create a simple text file for testing
    test_content = "This is a test document with citation: Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)"
    
    try:
        files = {'file': ('test.txt', test_content, 'text/plain')}
        
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            files=files,
            timeout=30
        )
        
        print(f"✅ File upload responds - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if it's async or immediate
            if data.get('status') == 'processing' and data.get('task_id'):
                print(f"🔄 Async processing - Task ID: {data['task_id']}")
                return test_task_status(data['task_id'])
            else:
                print("✅ Immediate response")
                return True
        else:
            print(f"❌ File upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return False

def test_url_upload_direct():
    """Test URL upload endpoint directly"""
    print("\n=== TESTING URL UPLOAD ENDPOINT ===")
    
    test_data = {
        "url": "https://example.com/test.pdf",
        "type": "url"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            json=test_data,
            timeout=30
        )
        
        print(f"✅ URL upload responds - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if it's async or immediate
            if data.get('status') == 'processing' and data.get('task_id'):
                print(f"🔄 Async processing - Task ID: {data['task_id']}")
                return test_task_status(data['task_id'])
            else:
                print("✅ Immediate response")
                return True
        else:
            print(f"❌ URL upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ URL upload error: {e}")
        return False

def test_task_status(task_id):
    """Test task status endpoint"""
    print(f"\n=== TESTING TASK STATUS FOR {task_id} ===")
    
    max_wait = 60  # 1 minute max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f'http://localhost:5000/casestrainer/api/task_status/{task_id}',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                print(f"Task status: {status}")
                
                if status == 'completed':
                    print("✅ Task completed successfully!")
                    print(f"Results: {json.dumps(data.get('results', []), indent=2)}")
                    return True
                elif status == 'failed':
                    print(f"❌ Task failed: {data.get('error', 'Unknown error')}")
                    return False
                elif status == 'processing':
                    print("⏳ Task still processing...")
                else:
                    print(f"⚠️ Unknown status: {status}")
            else:
                print(f"❌ Status check failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
        
        time.sleep(2)  # Wait 2 seconds before next check
    
    print(f"❌ Task polling timed out after {max_wait} seconds")
    return False

def main():
    """Main test function"""
    print("🔍 DIRECT ENDPOINT TESTING")
    print("=" * 40)
    
    # Test each endpoint
    tests = [
        ("Health Check", test_health_direct),
        ("Text Analysis", test_analyze_text_direct),
        ("File Upload", test_file_upload_direct),
        ("URL Upload", test_url_upload_direct)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                print(f"✅ {test_name}: SUCCESS")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 TEST SUMMARY")
    print("=" * 40)
    
    for test_name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    working_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nOverall: {working_count}/{total_count} endpoints working")
    
    if working_count == 0:
        print("\n💡 All endpoints are failing - check server configuration")
    elif working_count == total_count:
        print("\n🎉 All endpoints are working correctly!")
    else:
        print("\n⚠️ Some endpoints need attention")

if __name__ == "__main__":
    main() 