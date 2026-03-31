import requests
import json

# Check the completed job result directly from Redis via API
task_id = "dd572a83-011e-4354-8c55-acce3555b0df"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

print(f"Checking final task status: {task_id}")
try:
    resp = requests.get(url, timeout=10)
    print(f"Status code: {resp.status_code}")
    data = resp.json()
    print(f"\nResponse keys: {list(data.keys())}")
    print(f"Status: {data.get('status')}")
    
    if data.get('status') == 'completed':
        result = data.get('result', {})
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        print(f"\n✅ SUCCESS!")
        print(f"Citations: {len(citations)}")
        print(f"Clusters: {len(clusters)}")
        print(f"\nFirst 5 citations:")
        for i, c in enumerate(citations[:5], 1):
            print(f"  {i}. {c.get('raw', 'N/A')} - {c.get('case_name', 'N/A')[:50]}")
    else:
        print(f"Result: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")
