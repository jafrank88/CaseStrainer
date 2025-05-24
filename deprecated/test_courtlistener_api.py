import requests
import json
import os

API_URL = "https://www.courtlistener.com/api/rest/v3/citation-lookup/"
CITATION = "534 F.3d 1290"
import_path = "config.json"
imported_key = None

# Try to load API key from config.json
try:
    with open(import_path, "r") as f:
        config = json.load(f)
        imported_key = config.get("COURTLISTENER_API_KEY") or config.get(
            "courtlistener_api_key"
        )
except Exception as e:
    print(f"Could not load config.json: {e}")

API_KEY = imported_key or os.environ.get("COURTLISTENER_API_KEY") or "YOUR_API_KEY_HERE"

if imported_key:
    print(
        f"Loaded CourtListener API key from config.json: {API_KEY[:6]}... (truncated)"
    )
elif os.environ.get("COURTLISTENER_API_KEY"):
    print(
        f"Loaded CourtListener API key from environment variable: {API_KEY[:6]}... (truncated)"
    )
else:
    print(
        "No valid CourtListener API key found! Please set it in config.json or as an environment variable."
    )

headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "CaseStrainer Citation Verifier (manual test)",
}
data = {"text": CITATION}

print(f"Testing CourtListener API with citation: {CITATION}")
print(f"POST {API_URL}")
print(f"Headers: {headers}")
print(f"Data: {data}")

response = requests.post(API_URL, headers=headers, json=data)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

try:
    resp_json = response.json()
    print(json.dumps(resp_json, indent=2))
except Exception as e:
    print(f"Failed to parse JSON: {e}")
