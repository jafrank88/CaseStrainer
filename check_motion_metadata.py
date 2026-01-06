"""
Process motion.pdf again and check the response metadata carefully
"""

import requests
import json

print("=" * 80)
print("PROCESSING MOTION.PDF AND CHECKING METADATA")
print("=" * 80)

# Process motion.pdf fresh
with open('D:/dev/casestrainer/motion.pdf', 'rb') as f:
    files = {'file': ('motion.pdf', f, 'application/pdf')}
    print("Sending motion.pdf to API...")
    response = requests.post(
        'http://localhost:5000/casestrainer/api/analyze',
        files=files
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\nMETADATA:")
        print("-" * 40)
        metadata = data.get('metadata', {})
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        
        print("\nPROCESSING DETAILS:")
        print("-" * 40)
        print(f"   Processing mode: {metadata.get('processing_mode', 'unknown')}")
        print(f"   Processing strategy: {metadata.get('processing_strategy', 'unknown')}")
        print(f"   Input type: {metadata.get('input_type', 'unknown')}")
        print(f"   Source: {metadata.get('source', 'unknown')}")
        
        # Check if there's a request_id (indicates async)
        if 'request_id' in data:
            print(f"\n   Request ID: {data['request_id']}")
            if data['request_id'].startswith('api_'):
                print("   ✅ This looks like immediate processing (api_ prefix)")
            else:
                print("   ⚠️  This might be async processing")
        
        # Check verification status
        citations = data.get('citations', [])
        verified = sum(1 for c in citations if c.get('verified', False))
        print(f"\nVERIFICATION SUMMARY:")
        print(f"   Total citations: {len(citations)}")
        print(f"   Verified: {verified}")
        print(f"   With canonical data: {sum(1 for c in citations if c.get('canonical_name'))}")
        
        # Show first citation details
        if citations:
            c = citations[0]
            print(f"\nFIRST CITATION DETAILS:")
            print(f"   Citation: {c.get('citation')}")
            print(f"   Verified: {c.get('verified')}")
            print(f"   Processing stages: {c.get('processing_stages', [])}")
            if 'verification' not in c.get('processing_stages', []):
                print("   ⚠️  'verification' stage not in processing_stages!")
                
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

print("\n" + "=" * 80)
