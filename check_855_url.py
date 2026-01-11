"""Check if 855 F.2d 569 is now verified with correct URL"""
import requests
import json

response = requests.post(
    'http://localhost:5000/casestrainer/api/analyze',
    files={'file': open('motion.pdf', 'rb')},
    data={'force_mode': 'sync'},
    timeout=300
)

data = response.json()

found = False

# Find 855 F.2d 569 in clusters
for cluster in data.get('clusters', []):
    for citation in cluster.get('citations', []):
        if '855 F.2d 569' in str(citation.get('citation', '')):
            found = True
            print(f"\n✅ Found 855 F.2d 569 in cluster:")
            print(f"   Citation: {citation.get('citation')}")
            print(f"   Verified: {citation.get('verified')}")
            print(f"   Canonical Name: {citation.get('canonical_name')}")
            print(f"   Canonical URL: {citation.get('canonical_url')}")
            print(f"   Source: {citation.get('source')}")
            
            # Check if URL contains opinion 8971994
            url = citation.get('canonical_url', '')
            if '8971994' in url:
                print(f"\n✅ SUCCESS: URL contains opinion 8971994!")
            elif url:
                print(f"\n⚠️  WARNING: URL doesn't contain 8971994: {url}")
            else:
                print(f"\n❌ ERROR: No URL found")
            
            break
    if found:
        break

# Also check main citations list
if not found:
    for citation in data.get('citations', []):
        if '855 F.2d 569' in str(citation.get('citation_text', '')):
            found = True
            print(f"\n✅ Found 855 F.2d 569 in main citations list:")
            print(f"   Citation: {citation.get('citation_text')}")
            print(f"   Verified: {citation.get('verified')}")
            print(f"   Canonical Name: {citation.get('canonical_name')}")
            print(f"   URL: {citation.get('url')}")
            
            url = citation.get('url', '')
            if '8971994' in url:
                print(f"\n✅ SUCCESS: URL contains opinion 8971994!")
            elif url:
                print(f"\n⚠️  WARNING: URL doesn't contain 8971994: {url}")
            else:
                print(f"\n❌ ERROR: No URL found")
            break

if not found:
    print("\n❌ ERROR: 855 F.2d 569 not found in response")
    print(f"\nTotal clusters: {len(data.get('clusters', []))}")
    print(f"Total citations: {len(data.get('citations', []))}")
    
    # Show all citations to debug
    print("\nAll citations found:")
    for i, cit in enumerate(data.get('citations', [])[:10]):
        print(f"  {i+1}. {cit.get('citation_text', 'N/A')}")
