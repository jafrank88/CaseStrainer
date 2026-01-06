"""
Check if motion.pdf is being processed asynchronously via RQ
"""

import requests
import json
import time

print("=" * 80)
print("CHECKING IF FILE UPLOADS GO THROUGH ASYNC PROCESSING")
print("=" * 80)

# Test with a very small text to see the difference
print("\n1. TESTING TEXT INPUT (should be immediate):")
start_time = time.time()
response = requests.post(
    'http://localhost:5000/casestrainer/api/analyze',
    json={'text': 'See 578 U.S. 5 (2016).'}
)
elapsed = time.time() - start_time
print(f"   Response time: {elapsed:.2f} seconds")
print(f"   Processing mode: {response.json().get('metadata', {}).get('processing_mode', 'unknown')}")

# Test with a small file
print("\n2. TESTING SMALL FILE UPLOAD:")
import tempfile
import os

# Create a small test file with the same citation
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('See 963 F.3d 130 (2020) for details.')
    temp_file = f.name

try:
    start_time = time.time()
    with open(temp_file, 'rb') as f:
        files = {'file': ('test.txt', f, 'text/plain')}
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            files=files
        )
    elapsed = time.time() - start_time
    print(f"   Response time: {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Processing mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")
        print(f"   Request ID: {data.get('request_id', 'none')}")
        
        # Check if it has async indicators
        if 'request_id' in data and data.get('metadata', {}).get('processing_mode') == 'async':
            print("   ⚠️  File is being processed ASYNCHRONOUSLY!")
            print("   This explains why verification fixes aren't applied")
        else:
            print("   ✅ File is being processed synchronously")
            
finally:
    os.unlink(temp_file)

print("\n3. CHECKING MOTION.PDF METADATA:")
# Check what processing mode motion.pdf had
with open('D:/dev/casestrainer/motion_analysis_results.json', 'r', encoding='utf-8') as f:
    try:
        data = json.load(f)
        print(f"   Processing mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")
        print(f"   Request ID: {data.get('request_id', 'none')}")
        print(f"   Processing strategy: {data.get('metadata', {}).get('processing_strategy', 'unknown')}")
    except:
        print("   Could not read previous results")

print("\n" + "=" * 80)
print("FINDINGS:")
print("-" * 40)
print("If file uploads are going through async processing (RQ),")
print("the verification fixes need to be applied to rq_worker.py")
print("or the async pipeline, not just the sync code paths.")
print("=" * 80)
