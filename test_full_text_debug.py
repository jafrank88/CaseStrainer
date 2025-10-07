"""
Debug test for full text file
"""
import requests

api_url = "http://localhost:5000/casestrainer/api/analyze"

# Read the full text
with open('1033940_extracted.txt', 'r', encoding='utf-8') as f:
    text_content = f.read()

print(f"Text length: {len(text_content)} characters")
print(f"Text length: {len(text_content.encode('utf-8'))} bytes")

# Count potential citations in the text
import re
wn2d_matches = re.findall(r'\d+\s+Wn\.2d\s+\d+', text_content)
p3d_matches = re.findall(r'\d+\s+P\.3d\s+\d+', text_content)
p2d_matches = re.findall(r'\d+\s+P\.2d\s+\d+', text_content)

print(f"\nPotential citations in text:")
print(f"  Wn.2d: {len(wn2d_matches)}")
print(f"  P.3d: {len(p3d_matches)}")
print(f"  P.2d: {len(p2d_matches)}")
print(f"  Total: {len(wn2d_matches) + len(p3d_matches) + len(p2d_matches)}")

# Send to API
payload = {
    "type": "text",
    "text": text_content
}

print(f"\nSending to API...")
response = requests.post(api_url, json=payload, timeout=120)
data = response.json()

print(f"Status: {response.status_code}")
print(f"Success: {data.get('success')}")
print(f"Citations found: {len(data.get('citations', []))}")
print(f"Clusters found: {len(data.get('clusters', []))}")

# Check if there's an error
if 'error' in data:
    print(f"Error: {data['error']}")

# Check metadata
if 'metadata' in data:
    print(f"\nMetadata:")
    for key, value in data['metadata'].items():
        print(f"  {key}: {value}")

# Show first few citations if any
citations = data.get('citations', [])
if citations:
    print(f"\nFirst 5 citations:")
    for i, cit in enumerate(citations[:5], 1):
        print(f"  {i}. {cit.get('citation')} - {cit.get('extracted_case_name', 'N/A')}")
else:
    print("\n❌ No citations extracted!")
    print("\nChecking if text is being processed...")
    print(f"First 200 chars: {text_content[:200]}")
