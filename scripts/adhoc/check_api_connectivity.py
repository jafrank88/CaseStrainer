"""
Check if verification APIs are working
"""

import requests
import os
from dotenv import load_dotenv

print("=" * 80)
print("CHECKING VERIFICATION API CONNECTIVITY")
print("=" * 80)

# Load environment variables
load_dotenv('D:/dev/casestrainer/.env')
api_key = os.getenv('COURTLISTENER_API_KEY', '***REDACTED_COURTLISTENER_KEY***')

print(f"\n1. COURTLISTENER API KEY:")
print(f"   Key: {api_key[:10]}...{api_key[-10:]}")

# Test CourtListener API
print("\n2. TESTING COURTLISTENER API:")
base_url = "https://www.courtlistener.com/api/rest/v4"

# Test a known citation
test_citation = "963 F.3d 130"
search_url = f"{base_url}/search/?citation={test_citation}"

try:
    response = requests.get(search_url, headers={'Authorization': f'Token {api_key}'})
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', 0)
        print(f"   Results found: {count}")
        
        if count > 0:
            result = data['results'][0]
            print(f"   Case name: {result.get('case_name', 'N/A')}")
            print(f"   Citation: {result.get('citation', 'N/A')}")
            print(f"   URL: {result.get('absolute_url', 'N/A')}")
        else:
            print("   ⚠️  No results found for citation")
    else:
        print(f"   Error: {response.text}")
        
except Exception as e:
    print(f"   Exception: {e}")

# Test CaseMine
print("\n3. TESTING CASEMINE (for WL citations):")
print("   CaseMine doesn't have a public API, uses web scraping")
print("   Recent WL citations like 2024 WL xxxxx won't verify anyway")

# Check verification sources configuration
print("\n4. CHECKING VERIFICATION SOURCES CONFIG:")
with open('D:/dev/casestrainer/src/enhanced_fallback_verifier.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    # Look for the search_sources list
    if 'search_sources = [' in content:
        start = content.find('search_sources = [')
        end = content.find(']', start) + 1
        sources_section = content[start:end]
        print("   Configured sources:")
        for line in sources_section.split('\n'):
            if '#' not in line and '(' in line:
                print(f"   {line.strip()}")

print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("-" * 40)
print("If CourtListener API is working but citations still don't verify,")
print("the issue might be:")
print("1. Citation format mismatch")
print("2. Verification logic error")
print("3. Results not being applied correctly")
print("=" * 80)
