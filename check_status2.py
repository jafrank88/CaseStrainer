import requests
import json

task_id = "69a09c23-7127-4287-9e9f-a4754c7aac1d"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
