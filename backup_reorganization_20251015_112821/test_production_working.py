"""
Test Production with 24-2626.pdf using correct endpoint
"""
import requests
import json
import time
from pathlib import Path

print("=" * 100)
print("TESTING PRODUCTION WITH 24-2626.pdf")
print("=" * 100)

# Test health first
print("\n1️⃣  Testing health endpoint...")
health_response = requests.get("http://localhost:5000/casestrainer/api/health")
if health_response.status_code == 200:
    print("   ✅ Health check passed")
else:
    print(f"   ❌ Health check failed: {health_response.status_code}")
    exit(1)

# Find the PDF
pdf_path = Path("24-2626.pdf")
if not pdf_path.exists():
    print("❌ Cannot find 24-2626.pdf")
    exit(1)

# Read PDF as text (we'll extract text first)
import PyPDF2

print(f"\n2️⃣  Extracting text from {pdf_path.name}...")
with open(pdf_path, 'rb') as f:
    pdf_reader = PyPDF2.PdfReader(f)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"

print(f"   📄 Extracted {len(text)} characters")

# Send to analyze endpoint
print(f"\n3️⃣  Sending to production API...")
url = "http://localhost:5000/casestrainer/api/analyze"

data = {
    'text': text,
    'enable_verification': False  # Disable verification for speed
}

response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})

print(f"   📥 Response Status: {response.status_code}")

if response.status_code != 200:
    print(f"   ❌ Request failed!")
    print(f"   Response: {response.text[:500]}")
    exit(1)

result = response.json()

# Check if it's async or sync
if 'task_id' in result:
    print(f"\n4️⃣  Task created: {result['task_id']}")
    print(f"   ⏳ Polling for results...")
    
    task_id = result['task_id']
    max_wait = 120
    waited = 0
    
    while waited < max_wait:
        time.sleep(2)
        waited += 2
        
        status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
        status_response = requests.get(status_url)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            task_status = status_data.get('status', 'unknown')
            
            if task_status == 'completed':
                result = status_data
                print(f"\n   ✅ Task completed after {waited}s")
                break
            elif task_status == 'failed':
                print(f"\n   ❌ Task failed!")
                print(json.dumps(status_data, indent=2))
                exit(1)
            else:
                progress = status_data.get('progress_data', {}).get('current_step', 0)
                message = status_data.get('progress_data', {}).get('current_message', 'Processing...')
                print(f"   {progress}% - {message}")
        else:
            print(f"   ⚠️  Status check returned {status_response.status_code}")
    
    if waited >= max_wait:
        print(f"\n   ❌ Timeout after {max_wait}s")
        exit(1)
else:
    print(f"\n4️⃣  Sync response received")

# Analyze results
print(f"\n" + "=" * 100)
print("📊 RESULTS ANALYSIS")
print("=" * 100)

citations = result.get('citations', [])
print(f"\n📈 Total Citations: {len(citations)}")

if len(citations) == 0:
    print("❌ NO CITATIONS FOUND!")
    print(f"\nFull response:")
    print(json.dumps(result, indent=2))
    exit(1)

# Analyze quality
with_case_names = 0
with_dates = 0
methods = {}

print(f"\n📝 SAMPLE CITATIONS (first 10):")
print("-" * 100)

for i, citation in enumerate(citations[:10]):
    cit_text = citation.get('citation', 'N/A')
    case_name = citation.get('extracted_case_name') or citation.get('case_name')
    date = citation.get('extracted_date')
    method = citation.get('method', 'unknown')
    confidence = citation.get('confidence', 0)
    
    status = "✅" if case_name else "❌"
    print(f"{status} {i+1}. {cit_text}")
    print(f"   Case Name: {case_name or 'NULL'}")
    print(f"   Date: {date or 'NULL'}")
    print(f"   Method: {method}")
    print(f"   Confidence: {confidence}")
    print()

# Count all
with_case_names = 0
with_dates = 0
methods = {}

for citation in citations:
    case_name = citation.get('extracted_case_name') or citation.get('case_name')
    date = citation.get('extracted_date')
    method = citation.get('method', 'unknown')
    
    if case_name:
        with_case_names += 1
    if date:
        with_dates += 1
    
    methods[method] = methods.get(method, 0) + 1

print("=" * 100)
print("📊 EXTRACTION QUALITY METRICS")
print("=" * 100)
print(f"Total Citations: {len(citations)}")
print(f"With Case Names: {with_case_names} ({100*with_case_names/len(citations) if citations else 0:.1f}%)")
print(f"With Dates: {with_dates} ({100*with_dates/len(citations) if citations else 0:.1f}%)")
print(f"\nExtraction Methods Used:")
for method, count in methods.items():
    print(f"  - {method}: {count} citations ({100*count/len(citations):.1f}%)")

print("\n" + "=" * 100)

# Determine success
accuracy = 100*with_case_names/len(citations) if citations else 0

if 'fallback_regex' in methods:
    print("❌ CRITICAL FAILURE!")
    print("   System is using 'fallback_regex' - clean pipeline NOT integrated")
    print("   The UnifiedSyncProcessor or progress_manager failed")
elif accuracy >= 87:
    print(f"✅ SUCCESS! Clean pipeline is working")
    print(f"   Achieved: {accuracy:.1f}% case name extraction")
    print(f"   Target: 87%+ (PASSED)")
elif accuracy >= 50:
    print(f"⚠️  PARTIAL SUCCESS")
    print(f"   Achieved: {accuracy:.1f}% case name extraction")
    print(f"   Target: 87%+ (below target but working)")
else:
    print(f"❌ FAILURE!")
    print(f"   Only {accuracy:.1f}% case names extracted")
    print(f"   Target: 87%+")

print("=" * 100)
