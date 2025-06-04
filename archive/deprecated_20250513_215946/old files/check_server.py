import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try to connect to localhost
try:
    response = requests.get("https://localhost:5000", verify=False)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")  # Print first 200 chars of response
except Exception as e:
    print(f"Error connecting to localhost:5000: {e}")

# Try to connect to wolf.law.uw.edu
try:
    response = requests.get("https://wolf.law.uw.edu:5000", verify=False)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")  # Print first 200 chars of response
except Exception as e:
    print(f"Error connecting to wolf.law.uw.edu:5000: {e}")
