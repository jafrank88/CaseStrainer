#!/usr/bin/env python3
"""Quick test to see if fallback verification is working"""
import requests
import time

# Small text to process quickly
text = """
In Bostain v. Food Express, Inc., 159 Wn.2d 700, 153 P.3d 846 (2007), the court held that...
"""

print("\n🧪 Testing Fallback Verification")
print("=" * 60)

# Submit
response = requests.post(
    "https://wolf.law.uw.edu/casestrainer/api/analyze",
    data={'text': text, 'type': 'text'}
)

if response.status_code != 200:
    print(f"❌ Failed: {response.status_code}")
    exit(1)

task_id = response.json().get('task_id')
print(f"✅ Submitted: {task_id}")
print("\n⏳ Waiting for results...")

# Poll for completion
for i in range(60):
    time.sleep(2)
    status = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}")
    data = status.json()
    
    if data.get('status') == 'completed':
        citations = data.get('citations', [])
        verified = [c for c in citations if c.get('verified')]
        fallback_verified = [c for c in verified if c.get('verification_source') and 'courtlistener' not in c['verification_source'].lower()]
        
        print(f"\n✅ COMPLETED")
        print(f"   Citations: {len(citations)}")
        print(f"   Verified: {len(verified)}")
        print(f"   Fallback Verified: {len(fallback_verified)}")
        
        if fallback_verified:
            print(f"\n🎉 FALLBACK WORKING!")
            for c in fallback_verified:
                print(f"   {c['citation']} via {c['verification_source']}")
        else:
            print(f"\n⚠️  No fallback verifications (all from CourtListener or none verified)")
        
        break
    elif data.get('status') in ['error', 'failed']:
        print(f"\n❌ Failed: {data.get('error')}")
        break
else:
    print(f"\n⏱️  Timeout")

print("\n💡 Check worker logs for 'FALLBACK_VERIFY: Starting' messages")
