import requests

task_id = "676edb67-29cf-4aaa-806f-575d3fbbf3cf"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Error: {data.get('error')}")
        if 'error' in data:
            print(f"Full error: {data['error']}")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
