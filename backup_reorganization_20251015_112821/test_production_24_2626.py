"""
Test Production Deployment with 24-2626.pdf
Tests if the clean pipeline is working in production
"""
import requests
import json
from pathlib import Path

# Find the PDF
pdf_path = Path("24-2626.pdf")
if not pdf_path.exists():
    # Try in test_documents
    pdf_path = Path("test_documents/24-2626.pdf")
if not pdf_path.exists():
    print("❌ Cannot find 24-2626.pdf")
    exit(1)

print("=" * 100)
print("TESTING PRODUCTION DEPLOYMENT WITH 24-2626.pdf")
print("=" * 100)

# Upload the document to production endpoint
url = "http://localhost:5000/api/extract_citations_distributed"

with open(pdf_path, 'rb') as f:
    files = {'file': (pdf_path.name, f, 'application/pdf')}
    
    print(f"\n📤 Uploading {pdf_path.name} to production endpoint...")
    print(f"   URL: {url}")
    
    response = requests.post(url, files=files)
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Request failed!")
        print(f"Response: {response.text}")
        exit(1)
    
    result = response.json()
    
    # Get task ID
    task_id = result.get('task_id')
    
    if not task_id:
        print("❌ No task_id in response")
        print(json.dumps(result, indent=2))
        exit(1)
    
    print(f"✅ Task created: {task_id}")
    print(f"\n⏳ Waiting for task to complete...")
    
    # Poll for results
    import time
    max_wait = 120  # 2 minutes max
    waited = 0
    
    while waited < max_wait:
        time.sleep(2)
        waited += 2
        
        # Get task status
        status_url = f"http://localhost:5000/api/task_status/{task_id}"
        status_response = requests.get(status_url)
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.status_code}")
            continue
        
        status_data = status_response.json()
        task_status = status_data.get('status', 'unknown')
        
        if task_status == 'completed':
            print(f"\n✅ Task completed after {waited}s")
            break
        elif task_status == 'failed':
            print(f"\n❌ Task failed!")
            print(json.dumps(status_data, indent=2))
            exit(1)
        else:
            progress = status_data.get('progress_data', {}).get('current_step', 0)
            message = status_data.get('progress_data', {}).get('current_message', 'Processing...')
            print(f"   {progress}% - {message}")
    
    if waited >= max_wait:
        print(f"\n❌ Timeout after {max_wait}s")
        exit(1)
    
    # Get final results
    print(f"\n📊 RESULTS ANALYSIS")
    print("=" * 100)
    
    result_url = f"http://localhost:5000/api/task_result/{task_id}"
    result_response = requests.get(result_url)
    
    if result_response.status_code != 200:
        print(f"❌ Could not get results: {result_response.status_code}")
        exit(1)
    
    final_result = result_response.json()
    citations = final_result.get('citations', [])
    
    print(f"\n📈 Total Citations: {len(citations)}")
    
    # Analyze extraction quality
    with_case_names = 0
    with_dates = 0
    methods = {}
    
    print(f"\n📝 SAMPLE CITATIONS (first 5):")
    print("-" * 100)
    
    for i, citation in enumerate(citations[:5]):
        cit_text = citation.get('citation', 'N/A')
        case_name = citation.get('extracted_case_name') or citation.get('case_name')
        date = citation.get('extracted_date')
        method = citation.get('method', 'unknown')
        confidence = citation.get('confidence', 0)
        
        if case_name:
            with_case_names += 1
        if date:
            with_dates += 1
        
        methods[method] = methods.get(method, 0) + 1
        
        status = "✅" if case_name else "❌"
        print(f"{status} {i+1}. {cit_text}")
        print(f"   Case Name: {case_name or 'NULL'}")
        print(f"   Date: {date or 'NULL'}")
        print(f"   Method: {method}")
        print(f"   Confidence: {confidence}")
        print()
    
    # Count all citations
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
    if with_case_names >= len(citations) * 0.87:  # 87% threshold
        print("✅ SUCCESS! Clean pipeline is working (87%+ accuracy)")
        print(f"   Achieved: {100*with_case_names/len(citations):.1f}% case name extraction")
    elif 'fallback_regex' in methods:
        print("❌ FAILURE! System is using fallback_regex (broken)")
        print("   The clean pipeline is NOT integrated properly")
    elif with_case_names >= len(citations) * 0.5:
        print("⚠️  PARTIAL SUCCESS - Some extraction working but below target")
        print(f"   Achieved: {100*with_case_names/len(citations):.1f}% (target: 87%+)")
    else:
        print("❌ FAILURE! Poor extraction quality")
        print(f"   Only {100*with_case_names/len(citations):.1f}% case names extracted")
    
    print("=" * 100)
