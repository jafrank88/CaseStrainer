import requests
import json

task_id = "3ed97bdd-f48d-43da-b069-2ed2709524c3"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
