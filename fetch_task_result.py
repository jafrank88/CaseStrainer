"""
Fetch the task result using the task_id
"""
import requests
import json
import time

task_id = "12c0573a-39e6-432e-8d41-b575064323ae"
STATUS_URL = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

print(f"🔍 Fetching results for task: {task_id}")
print(f"Status URL: {STATUS_URL}")
print("")

# Task should be complete by now
print("📡 Fetching results...")

try:
    response = requests.get(STATUS_URL, verify=False, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        
        # Save result
        with open('fetched_task_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("✅ Results saved to: fetched_task_result.json")
        print("")
        print("📊 SUMMARY:")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Total Citations: {result.get('statistics', {}).get('total_citations', 0)}")
        print(f"   Total Clusters: {result.get('statistics', {}).get('total_clusters', 0)}")
        print(f"   Verified Citations: {result.get('statistics', {}).get('verified_citations', 0)}")
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

