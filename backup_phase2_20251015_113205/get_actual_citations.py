"""
Get actual citation data from the last test
"""
import requests
import json

# Get the last completed task
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
}

print("Fetching citation data...")
response = requests.post(url, json=payload, verify=False, timeout=30)
result = response.json()

task_id = result.get('task_id') or result.get('request_id')
print(f"Task ID: {task_id}")

# Wait for completion
import time
status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

for i in range(30):
    time.sleep(2)
    status_response = requests.get(status_url, verify=False, timeout=10)
    status_data = status_response.json()
    
    if status_data.get('status') in ['completed', 'failed']:
        break

# Get citations
result_data = status_data.get('result', {})
citations = result_data.get('citations', [])
clusters = result_data.get('clusters', [])

print(f"\nTotal Citations: {len(citations)}")
print(f"Total Clusters: {len(clusters)}")

# Show first 15 citations with full details
print(f"\n{'='*80}")
print("FIRST 15 CITATIONS - DETAILED VIEW")
print(f"{'='*80}")

for i, cit in enumerate(citations[:15], 1):
    print(f"\n{i}. {cit.get('citation', 'N/A')}")
    print(f"   extracted_case_name: '{cit.get('extracted_case_name', 'N/A')}'")
    print(f"   extracted_date: '{cit.get('extracted_date', 'N/A')}'")
    print(f"   canonical_name: '{cit.get('canonical_name', 'N/A')}'")
    print(f"   canonical_date: '{cit.get('canonical_date', 'N/A')}'")
    print(f"   verified: {cit.get('verified', False)}")
    print(f"   verification_status: '{cit.get('verification_status', 'N/A')}'")
    print(f"   cluster_id: '{cit.get('cluster_id', 'N/A')}'")
    print(f"   is_in_cluster: {cit.get('is_in_cluster', False)}")

# Save full data
with open('last_test_citations.json', 'w') as f:
    json.dump({
        'citations': citations,
        'clusters': clusters,
        'metadata': result_data.get('metadata', {})
    }, f, indent=2)

print(f"\n{'='*80}")
print(f"Full data saved to: last_test_citations.json")
print(f"{'='*80}")
