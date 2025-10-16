"""Quick test of production extraction"""
import requests
import json

print("Testing production with simple text...")

# Test with small text snippet containing known citations
text = """
The court in Erie Railroad Co. v. Tompkins, 304 U.S. 64 (1938), held that 
federal courts must apply state substantive law. In Burnham v. Superior Court, 
495 U.S. 604 (1990), the Court addressed personal jurisdiction.
"""

url = "http://localhost:5000/casestrainer/api/analyze"
data = {'text': text, 'enable_verification': False}

print(f"Sending request to {url}...")
response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=30)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    
    print(f"\nFound {len(citations)} citations:")
    for i, cit in enumerate(citations):
        cit_text = cit.get('citation', 'N/A')
        case_name = cit.get('extracted_case_name') or cit.get('case_name')
        method = cit.get('method', 'unknown')
        
        status = "✅" if case_name else "❌"
        print(f"{status} {i+1}. {cit_text}")
        print(f"   Case: {case_name or 'NULL'}")
        print(f"   Method: {method}")
    
    # Check if using fallback
    methods = [c.get('method', 'unknown') for c in citations]
    if 'fallback_regex' in methods:
        print("\n❌ BROKEN: Using fallback_regex (clean pipeline not integrated)")
    elif any('clean_pipeline' in str(m) for m in methods):
        print("\n✅ SUCCESS: Using clean pipeline!")
    else:
        print(f"\n⚠️  Using methods: {set(methods)}")
else:
    print(f"Error: {response.text[:200]}")
