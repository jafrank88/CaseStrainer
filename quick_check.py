import requests

task_id = "4153917f-7164-477c-bd61-8afbd5511d55"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Progress: {data.get('progress_percent')}%")
        print(f"Citations: {len(data.get('citations', []))}")
        
        if data.get('citations'):
            print("Sample citations:")
            for i, cit in enumerate(data.get('citations', [])[:3]):
                print(f"  {i+1}. {cit.get('citation')} - {cit.get('case_name')}")
    else:
        print(f"Task not found or error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
