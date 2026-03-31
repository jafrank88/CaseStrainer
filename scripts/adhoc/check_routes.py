import requests

try:
    response = requests.get("https://wolf.law.uw.edu/casestrainer/api/routes")
    print(response.text[:1000])
except Exception as e:
    print(f"Error: {e}")
