import requests

try:
    response = requests.get("https://wolf.law.uw.edu/casestrainer/api/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
