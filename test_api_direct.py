#!/usr/bin/env python3
"""
Direct API test using simple text input
"""
import requests
import json

# Test with direct backend connection
BASE_URL = "http://127.0.0.1:5000/casestrainer/api"

print("=" * 80)
print("DIRECT API TEST")
print("=" * 80)
print()

# Simple text test
test_text = """
The court in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) held that...
"""

print(f"[1] Testing /analyze endpoint with simple text...")
print(f"    URL: {BASE_URL}/analyze")
print(f"    Text: {test_text.strip()}")
print()

payload = {
    "type": "text",
    "text": test_text
}

try:
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        timeout=30
    )
    
    print(f"[2] Response received:")
    print(f"    Status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print(f"[3] Response data:")
        print(json.dumps(data, indent=2))
        print()
        
        # Check what we got
        citations = data.get('citations', [])
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"[4] Analysis:")
        print(f"    Processing mode: {processing_mode}")
        print(f"    Citations found: {len(citations)}")
        
        if processing_mode == 'sync':
            print(f"    ✅ SYNC processing completed immediately")
            if citations:
                print(f"    ✅ Citations extracted successfully")
                for i, cit in enumerate(citations[:3], 1):
                    print(f"       {i}. {cit.get('citation_text', 'N/A')}")
            else:
                print(f"    ⚠️  No citations found (might be normal for this text)")
        elif processing_mode == 'queued':
            task_id = data.get('metadata', {}).get('job_id')
            print(f"    ⚠️  ASYNC processing - job queued")
            print(f"    Task ID: {task_id}")
            print(f"    Note: This means workers will process it")
        
        print()
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
    else:
        print(f"[ERROR] Request failed:")
        print(f"    Status: {response.status_code}")
        print(f"    Response: {response.text}")
        
except Exception as e:
    print(f"[ERROR] Exception occurred:")
    print(f"    {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
