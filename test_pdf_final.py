"""
Final test: PDF vs Text with proper async handling
"""
import requests
import time

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
print("FINAL TEST: PDF vs TEXT (with async handling)")
print("=" * 80)

# Test 1: Text file
print("\n1. Testing with text file...")
with open('1033940_extracted.txt', 'r', encoding='utf-8') as f:
    text_content = f.read()

text_payload = {"type": "text", "text": text_content}
response = requests.post(api_url, json=text_payload, timeout=10)
text_data = response.json()

task_id = text_data.get('task_id') or text_data.get('metadata', {}).get('job_id')
if task_id:
    print(f"   Async processing (task_id: {task_id[:8]}...)")
    text_data = wait_for_async(task_id)

if text_data:
    text_citations = len(text_data.get('citations', []))
    text_clusters = len(text_data.get('clusters', []))
    print(f"   ✅ Citations: {text_citations}")
    print(f"   ✅ Clusters: {text_clusters}")
else:
    text_citations = 0
    text_clusters = 0
    print(f"   ❌ Failed")

# Test 2: PDF URL
print("\n2. Testing with PDF URL...")
pdf_payload = {"type": "url", "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"}
response = requests.post(api_url, json=pdf_payload, timeout=10)
pdf_data = response.json()

task_id = pdf_data.get('task_id') or pdf_data.get('metadata', {}).get('job_id')
if task_id:
    print(f"   Async processing (task_id: {task_id[:8]}...)")
    pdf_data = wait_for_async(task_id)

if pdf_data:
    pdf_citations = len(pdf_data.get('citations', []))
    pdf_clusters = len(pdf_data.get('clusters', []))
    print(f"   ✅ Citations: {pdf_citations}")
    print(f"   ✅ Clusters: {pdf_clusters}")
else:
    pdf_citations = 0
    pdf_clusters = 0
    print(f"   ❌ Failed")

# Comparison
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)
print(f"\nText file:  {text_citations} citations, {text_clusters} clusters")
print(f"PDF URL:    {pdf_citations} citations, {pdf_clusters} clusters")

if text_citations > 0 and pdf_citations > 0:
    if abs(text_citations - pdf_citations) <= 5:  # Allow small variance
        print("\n✅ SUCCESS: PDF and text return similar results!")
    else:
        print(f"\n⚠️  MISMATCH: {abs(text_citations - pdf_citations)} citation difference")
elif text_citations > 0 and pdf_citations == 0:
    print("\n❌ ISSUE: PDF extraction not working (text works)")
elif text_citations == 0 and pdf_citations == 0:
    print("\n❌ ISSUE: Neither text nor PDF extraction working")
else:
    print("\n⚠️  Unexpected result pattern")

print("\n" + "=" * 80)
