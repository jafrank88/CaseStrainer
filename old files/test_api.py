import json
import requests
import os
import sys

# Load API key from config.json
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
api_key = None

try:
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            api_key = config.get('courtlistener_api_key')
            print(f"Loaded CourtListener API key from config.json: {api_key[:5]}...")
except Exception as e:
    print(f"Error loading config.json: {e}")
    sys.exit(1)

if not api_key:
    print("No API key found in config.json")
    sys.exit(1)

# CourtListener API URL
api_url = 'https://www.courtlistener.com/api/rest/v3/citation-lookup/'

# Test text with citations
test_text = """
This is a test document with some citations.
The Supreme Court's decision in Brown v. Board of Education, 347 U.S. 483 (1954), was a landmark case.
Another important case is Roe v. Wade, 410 U.S. 113 (1973).
"""

print(f"Testing API with text: {test_text}")

# Set up headers and data
headers = {
    'Authorization': f'Token {api_key}',
    'Content-Type': 'application/json'
}

data = {
    'text': test_text
}

# Make the request
print("Sending request to CourtListener API...")
response = requests.post(api_url, headers=headers, json=data)

print(f"Response status code: {response.status_code}")
print(f"Response headers: {response.headers}")

if response.status_code == 200:
    try:
        response_json = response.json()
        print("Response is valid JSON")
        print(f"Response keys: {list(response_json.keys()) if isinstance(response_json, dict) else 'Not a dictionary'}")
        print("Full response content:")
        print(json.dumps(response_json, indent=2))
        
        # Save response to file
        with open('test_api_response.json', 'w') as f:
            json.dump(response_json, f, indent=2)
        print("Full response saved to test_api_response.json")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print(f"Response text: {response.text}")
else:
    print(f"API request failed with status code: {response.status_code}")
    print(f"Response text: {response.text}")
