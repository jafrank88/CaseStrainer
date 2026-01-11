"""
Test to check what CourtListener actually returns for F.2d, F.3d, F.4th citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("COURTLISTENER API TEST FOR F.2d, F.3d, F.4th")
print("=" * 60)

import requests
import json

# Test citations from the web interface
test_citations = [
    ("585 F.3d 1061", "Bond v. Utreras"),
    ("146 F.4th 165", "Giuffre v. Maxwell"),
    ("710 F.2d 1165", "Brown & Williamson Tobacco Corp. v. F.T.C"),
]

base_url = "https://www.courtlistener.com/api/rest/v3/search/"

for citation, expected_case in test_citations:
    print(f"\nTesting: {citation}")
    print(f"Expected: {expected_case}")
    print("-" * 50)
    
    # Search for the citation
    params = {
        "citation": citation,
        "page_size": 1
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("count") > 0:
                result = data["results"][0]
                print(f"  ✅ Found on CourtListener")
                print(f"  Case Name: {result.get('case_name', 'N/A')}")
                print(f"  Date Filed: {result.get('date_filed', 'N/A')}")
                print(f"  Date Argued: {result.get('date_argued', 'N/A')}")
                print(f"  Citation: {result.get('citation', 'N/A')}")
                print(f"  URL: https://courtlistener.com{result.get('absolute_url', 'N/A')}")
            else:
                print(f"  ❌ Not found on CourtListener")
        else:
            print(f"  ❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Request failed: {str(e)}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("If CourtListener returns wrong dates, the year mismatch")
print("rejection logic is preventing verification of valid citations")
print("=" * 60)
