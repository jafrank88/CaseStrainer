"""
Simple extraction test
"""
import sys
import re

# Test the pattern directly
text1 = "Spokeo, Inc. v. Robins, 578 U.S. 330"
text2 = "Raines v. Byrd, 521 U.S. 811"

pattern = r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)?)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]+?)(?:,\s*\d+)'

print("Testing Spokeo:")
match1 = re.search(pattern, text1)
if match1:
    print(f"  Plaintiff: '{match1.group(1)}'")
    print(f"  Defendant: '{match1.group(2)}'")
    print(f"  Full: '{match1.group(1)} v. {match1.group(2)}'")
else:
    print("  NO MATCH")
    "text": test_text
}

print("Testing simple citation extraction...")
print(f"Input: {test_text}\n")

response = requests.post(api_url, json=payload, timeout=10)
data = response.json()

print(f"Status: {response.status_code}")
print(f"Success: {data.get('success')}")
print(f"Citations found: {len(data.get('citations', []))}")

for i, cit in enumerate(data.get('citations', []), 1):
    print(f"\n  Citation {i}:")
    print(f"    Text: {cit.get('citation')}")
    print(f"    Case: {cit.get('extracted_case_name', 'N/A')}")
    print(f"    Pattern: {cit.get('pattern')}")
