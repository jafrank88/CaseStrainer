"""
Test local PDF file processing
"""
import requests
import time
import base64

api_url = "http://localhost:5000/casestrainer/api/analyze"

def wait_for_async(task_id, timeout=120):
    """Wait for async task to complete"""
    status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(2)
        try:
            response = requests.get(status_url, timeout=5)
            data = response.json()
            
            status = data.get('status')
            if status in ['completed', 'failed']:
                return data
        except:
            pass
    
    return None

print("=" * 80)
print("TESTING LOCAL PDF FILE")
print("=" * 80)

# Try to upload the local PDF file
print("\n1. Reading local PDF file...")
with open('1033940.pdf', 'rb') as f:
    pdf_content = f.read()

print(f"   PDF size: {len(pdf_content)} bytes")

# Try sending as file upload
files = {'file': ('1033940.pdf', pdf_content, 'application/pdf')}
data_payload = {'type': 'file'}

print("\n2. Uploading to backend...")
try:
    response = requests.post(api_url, files=files, data=data_payload, timeout=30)
    result = response.json()
    
    print(f"   Status: {response.status_code}")
    print(f"   Success: {result.get('success')}")
    
    task_id = result.get('task_id') or result.get('metadata', {}).get('job_id')
    if task_id:
        print(f"   Task ID: {task_id}")
        print(f"   Waiting for processing...")
        result = wait_for_async(task_id)
        
        if result:
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            print(f"\n   ✅ Citations: {len(citations)}")
            print(f"   ✅ Clusters: {len(clusters)}")
            
            print(f"\n   First 10 citations:")
            for i, cit in enumerate(citations[:10], 1):
                print(f"     {i}. {cit.get('citation')}")
    else:
        citations = result.get('citations', [])
        print(f"   Citations: {len(citations)}")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 80)
print("COMPARISON WITH PDF URL")
print("=" * 80)

# Compare with PDF URL result
print("\nPDF URL result: 55 citations")
print("Local PDF result: (see above)")

print("\n" + "=" * 80)
