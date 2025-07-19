import requests
import json
import time

def test_file_upload():
    """Test file upload to the API with async processing"""
    url = "http://localhost:5001/casestrainer/api/analyze"
    
    with open("test_pdf.pdf", "rb") as f:
        files = {"file": ("test_pdf.pdf", f, "application/pdf")}
        
        print("Uploading file...")
        response = requests.post(url, files=files, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 202:  # Accepted for async processing
            data = response.json()
            task_id = data.get('task_id')
            print(f"✅ File queued successfully! Task ID: {task_id}")
            
            # Poll for results
            return poll_task_status(task_id)
        else:
            print(f"Error: {response.text}")
            return None

def test_url_upload():
    """Test URL upload to the API with async processing"""
    url = "http://localhost:5001/casestrainer/api/analyze"
    
    data = {
        "url": "https://www.courts.wa.gov/opinions/pdf/1029101.pdf",
        "type": "url"
    }
    
    print("Testing URL upload...")
    response = requests.post(url, json=data, timeout=30)  # Reduced timeout since we expect immediate response
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 202:  # Accepted for async processing
        data = response.json()
        task_id = data.get('task_id')
        print(f"✅ URL queued successfully! Task ID: {task_id}")
        
        # Poll for results
        return poll_task_status(task_id)
    else:
        print(f"Error: {response.text}")
        return None

def poll_task_status(task_id, max_wait_time=300):
    """Poll for task status and return results when complete"""
    status_url = f"http://localhost:5001/casestrainer/api/task_status/{task_id}"
    
    print(f"🔄 Polling for task status: {task_id}")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                print(f"📊 Task status: {status}")
                
                if status == 'completed':
                    print("✅ Task completed successfully!")
                    print(f"📋 Citations found: {len(data.get('citations', []))}")
                    print(f"📊 Statistics: {data.get('statistics', {})}")
                    return data
                
                elif status == 'failed':
                    print(f"❌ Task failed: {data.get('error', 'Unknown error')}")
                    return None
                
                elif status in ['queued', 'processing']:
                    print(f"⏳ Task {status}... waiting 5 seconds")
                    time.sleep(5)
                    continue
                
                else:
                    print(f"❓ Unknown status: {status}")
                    time.sleep(5)
                    continue
                    
            else:
                print(f"❌ Status check failed: {response.status_code} - {response.text}")
                time.sleep(5)
                continue
                
        except requests.exceptions.Timeout:
            print("⏰ Status check timed out, retrying...")
            time.sleep(5)
            continue
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            time.sleep(5)
            continue
    
    print(f"⏰ Task polling timed out after {max_wait_time} seconds")
    return None

if __name__ == "__main__":
    print("=== Testing File Upload (Async) ===")
    test_file_upload()
    
    print("\n=== Testing URL Upload (Async) ===")
    test_url_upload() 