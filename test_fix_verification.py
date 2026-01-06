import requests
import json
from datetime import datetime

print("=" * 80)
print("TESTING VERIFICATION FIX")
print("=" * 80)
print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Process the motion.pdf file again
with open('D:/dev/casestrainer/motion.pdf', 'rb') as f:
    files = {'file': ('motion.pdf', f, 'application/pdf')}
    print("Sending motion.pdf to API for processing...")
    response = requests.post('http://localhost:5000/casestrainer/api/analyze', files=files)
    
    if response.status_code == 200:
        data = response.json()
        citations = data['citations']
        
        print("RESULTS AFTER FIX:")
        print("-" * 40)
        print(f"Total Citations: {len(citations)}")
        
        # Count verified citations
        verified_count = sum(1 for c in citations if c.get('verified', False))
        print(f"Verified Citations: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
        
        # Count citations with canonical data
        with_canonical = sum(1 for c in citations if c.get('canonical_name'))
        print(f"With Canonical Data: {with_canonical}/{len(citations)} ({with_canonical/len(citations)*100:.1f}%)")
        
        # Show some examples
        print("\nSAMPLE CITATIONS:")
        print("-" * 40)
        for i, c in enumerate(citations[:5], 1):
            print(f"\n{i}. {c['citation']}")
            print(f"   Case Name: {c.get('extracted_case_name', 'N/A')}")
            print(f"   Verified: {c.get('verified', False)}")
            if c.get('canonical_name'):
                print(f"   Canonical: {c['canonical_name']}")
            if c.get('canonical_date'):
                print(f"   Canonical Date: {c['canonical_date']}")
        
        if verified_count > 0:
            print("\n✅ SUCCESS: Verification is now working!")
        else:
            print("\n⚠️  Verification still not working - may need to restart the service")
            
    else:
        print(f"❌ Error: API returned status code {response.status_code}")
        print(response.text)

print("\n" + "=" * 80)
