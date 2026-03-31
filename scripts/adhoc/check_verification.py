import requests
import json

# Check the latest task status from the frontend logs
task_id = "54f1d90b-a74d-4cc9-985f-47abc3f8d7ca"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

print(f"Checking task status: {task_id}")
try:
    resp = requests.get(url, timeout=10)
    data = resp.json()
    
    print(f"Status: {data.get('status')}")
    print(f"Success: {data.get('success')}")
    
    # Check citations for verification status
    citations = data.get('citations', [])
    print(f"\nTotal citations: {len(citations)}")
    
    verified_count = sum(1 for c in citations if c.get('verified'))
    print(f"Verified: {verified_count}")
    print(f"Unverified: {len(citations) - verified_count}")
    
    # Show first few citations with their verification status
    print("\nFirst 5 citations verification status:")
    for i, c in enumerate(citations[:5], 1):
        print(f"  {i}. {c.get('raw', c.get('citation', 'N/A'))[:50]}...")
        print(f"     verified: {c.get('verified')}")
        print(f"     source: {c.get('verification_source', c.get('source', 'N/A'))}")
        print(f"     canonical_name: {c.get('canonical_name', 'N/A')}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
