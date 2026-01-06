"""
Check if citations are getting canonical data from verification
"""

import requests
import json

print("=" * 80)
print("CHECKING CANONICAL DATA IN CITATIONS")
print("=" * 80)

# Process motion.pdf and check for canonical data
with open('D:/dev/casestrainer/motion.pdf', 'rb') as f:
    files = {'file': ('motion.pdf', f, 'application/pdf')}
    response = requests.post(
        'http://localhost:5000/casestrainer/api/analyze',
        files=files
    )
    
    if response.status_code == 200:
        data = response.json()
        citations = data.get('citations', [])
        
        print(f"\nTotal citations: {len(citations)}")
        
        # Check first few citations for canonical data
        print("\nChecking first 5 citations for canonical data:")
        print("-" * 40)
        
        for i, c in enumerate(citations[:5], 1):
            print(f"\n{i}. {c['citation']}")
            print(f"   Verified: {c.get('verified')}")
            print(f"   Has canonical_name: {bool(c.get('canonical_name'))}")
            print(f"   Has canonical_date: {bool(c.get('canonical_date'))}")
            print(f"   Has canonical_url: {bool(c.get('canonical_url'))}")
            print(f"   Source: {c.get('source', 'N/A')}")
            
            # Check if it has any canonical data
            has_any = any([
                c.get('canonical_name'),
                c.get('canonical_date'),
                c.get('canonical_url')
            ])
            
            if has_any:
                print("   ✅ Has some canonical data")
            else:
                print("   ❌ No canonical data found")
        
        # Count how many have canonical data
        with_canonical = sum(1 for c in citations if c.get('canonical_name'))
        print(f"\n\nSUMMARY:")
        print(f"Citations with canonical_name: {with_canonical}/{len(citations)}")
        
        if with_canonical == 0:
            print("\n⚠️  NO citations have canonical data!")
            print("This means verification is not returning any results.")
            print("The issue is likely in the verification methods themselves.")
            
    else:
        print(f"Error: {response.status_code}")

print("\n" + "=" * 80)
print("NEXT STEP:")
print("-" * 40)
print("If no citations have canonical data, the verification methods")
print("are not successfully retrieving data from CourtListener.")
print("Need to check the verification implementation.")
print("=" * 80)
