"""
Final test with 24-2626.pdf to verify clean pipeline is working in production.
Run directly: python -m tests.unit.test_24_2626_final (with 24-2626.pdf in cwd).
"""
import requests
import json
import time
from pathlib import Path
import PyPDF2


def _run_production_test():
    """Run the 24-2626 production test (called when script is run directly)."""
    print("=" * 100)
    print("FINAL PRODUCTION TEST WITH 24-2626.pdf")
    print("=" * 100)

    # Find the PDF
    pdf_path = Path("24-2626.pdf")
    if not pdf_path.exists():
        print("❌ Cannot find 24-2626.pdf")
        exit(1)

    print(f"\n1️⃣  Extracting text from {pdf_path.name}...")
    with open(pdf_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

    print(f"   📄 Extracted {len(text)} characters")

    # Send to analyze endpoint
    print(f"\n2️⃣  Sending to production API...")
    url = "http://localhost:5000/casestrainer/api/analyze"

    data = {
        'text': text,
        'enable_verification': False  # Disable for speed
    }

    response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=60)

    print(f"   📥 Response Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ❌ Request failed!")
        print(f"   Response: {response.text[:500]}")
        exit(1)

    result = response.json()

    # Check if it's async
    if 'task_id' in result:
        print(f"\n3️⃣  Task created: {result['task_id']}")
        print(f"   ⏳ Polling for results...")
        task_id = result['task_id']
        max_wait = 180  # 3 minutes
        waited = 0
        while waited < max_wait:
            time.sleep(3)
            waited += 3
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
                    print(f"   [{waited}s] {progress}% - {message}")
        if waited >= max_wait:
            print(f"\n   ❌ Timeout after {max_wait}s")
            exit(1)
    else:
        print(f"\n3️⃣  Sync response received")

    # Analyze results
    print(f"\n" + "=" * 100)
    print("📊 RESULTS ANALYSIS")
    print("=" * 100)

    citations = result.get('citations', [])
    print(f"\n📈 Total Citations: {len(citations)}")

    if len(citations) == 0:
        print("❌ NO CITATIONS FOUND!")
        print(f"\nFull response keys: {result.keys()}")
        exit(1)

    # Analyze quality
    with_case_names = 0
    with_dates = 0
    methods = {}
    null_case_names = []

    print(f"\n📝 SAMPLE CITATIONS (first 15):")
    print("-" * 100)

    for i, citation in enumerate(citations[:15]):
        cit_text = citation.get('citation', 'N/A')
        case_name = citation.get('extracted_case_name') or citation.get('case_name')
        date = citation.get('extracted_date')
        method = citation.get('method', 'unknown')
        confidence = citation.get('confidence', 0)
        if case_name:
            with_case_names += 1
        else:
            null_case_names.append(cit_text)
        if date:
            with_dates += 1
        methods[method] = methods.get(method, 0) + 1
        status = "✅" if case_name else "❌"
        print(f"{status} {i+1}. {cit_text}")
        print(f"   Case: {case_name or 'NULL'}")
        print(f"   Date: {date or 'NULL'}")
        print(f"   Method: {method}")
        print(f"   Confidence: {confidence}")
        print()

    # Count all
    with_case_names = 0
    with_dates = 0
    methods = {}
    null_case_names = []

    for citation in citations:
        case_name = citation.get('extracted_case_name') or citation.get('case_name')
        date = citation.get('extracted_date')
        method = citation.get('method', 'unknown')
        if case_name:
            with_case_names += 1
        else:
            null_case_names.append(citation.get('citation', 'N/A'))
        if date:
            with_dates += 1
        methods[method] = methods.get(method, 0) + 1

    print("=" * 100)
    print("📊 EXTRACTION QUALITY METRICS")
    print("=" * 100)
    print(f"Total Citations: {len(citations)}")
    print(f"With Case Names: {with_case_names} ({100*with_case_names/len(citations) if citations else 0:.1f}%)")
    print(f"With NULL Case Names: {len(null_case_names)} ({100*len(null_case_names)/len(citations) if citations else 0:.1f}%)")
    print(f"With Dates: {with_dates} ({100*with_dates/len(citations) if citations else 0:.1f}%)")
    print(f"\nExtraction Methods Used:")
    for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {method}: {count} citations ({100*count/len(citations):.1f}%)")

    if null_case_names:
        print(f"\n❌ NULL Case Names (showing first 10):")
        for cit in null_case_names[:10]:
            print(f"   - {cit}")

    print("\n" + "=" * 100)

    # Determine success
    accuracy = 100*with_case_names/len(citations) if citations else 0

    if 'fallback_regex' in methods:
        print("❌ CRITICAL FAILURE!")
        print("   System is using 'fallback_regex' - clean pipeline NOT working")
        print("   This is the same broken state as before")
    elif 'clean_pipeline_v1' in methods and accuracy >= 87:
        print(f"✅ SUCCESS! Clean pipeline is working in production!")
        print(f"   Achieved: {accuracy:.1f}% case name extraction")
        print(f"   Target: 87%+ (PASSED ✅)")
        print(f"   Method: clean_pipeline_v1")
    elif 'clean_pipeline_v1' in methods:
        print(f"⚠️  PARTIAL SUCCESS - Clean pipeline is running")
        print(f"   Achieved: {accuracy:.1f}% case name extraction")
        print(f"   Target: 87%+ (below target)")
        print(f"   Method: clean_pipeline_v1")
    else:
        print(f"❌ FAILURE!")
        print(f"   Accuracy: {accuracy:.1f}%")
        print(f"   Methods: {list(methods.keys())}")
        print(f"   Clean pipeline not detected")

    print("=" * 100)


if __name__ == "__main__":
    _run_production_test()
