import requests
import json

# Test production
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "type": "text", 
    "text": "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
}

print("Testing production...")
response = requests.post(url, json=data, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    try:
        result = response.json()
        print(f"Status: {result.get('status')}")
        print(f"Citations: {len(result.get('citations', []))}")
        print(f"Message: {result.get('message', 'No message')}")
        
        # Show first 300 chars of response
        print(f"Response preview: {response.text[:300]}...")
        
        if result.get('citations'):
            for i, citation in enumerate(result['citations']):
                print(f"Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"  Extracted name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"  Extracted date: {citation.get('extracted_date', 'N/A')}")
        
    except:
        print("Could not parse JSON")
        print(f"Raw response: {response.text}")
else:
    print(f"Error: {response.text}") 