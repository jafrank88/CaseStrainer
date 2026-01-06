"""
Deep dive into why verification is still not working after restart
"""

import logging
import requests
import json

print("=" * 80)
print("DEEP DEBUGGING - VERIFICATION STILL NOT WORKING")
print("=" * 80)

# First, let's test a known citation that should verify
print("\n1. TESTING A SIMPLE CITATION:")
test_text = "See 578 U.S. 5 (2016) for details."
response = requests.post(
    'http://localhost:5000/casestrainer/api/analyze',
    json={'text': test_text}
)

if response.status_code == 200:
    data = response.json()
    citations = data.get('citations', [])
    if citations:
        c = citations[0]
        print(f"   Citation: {c.get('citation')}")
        print(f"   Verified: {c.get('verified')}")
        print(f"   Processing stages: {c.get('processing_stages', [])}")
        print(f"   Source: {c.get('source', 'N/A')}")
else:
    print(f"   Error: {response.status_code}")

# Now check what's happening with file uploads
print("\n2. CHECKING PROCESSING MODE FOR FILES:")
print("   The motion.pdf might be taking a different path...")

# Let's check the logs for verification attempts
import os
print("\n3. SCANNING LOGS FOR VERIFICATION MESSAGES:")

log_files = [
    'D:/dev/casestrainer/logs/casestrainer.log',
    'D:/dev/casestrainer/logs/docker_daemon_monitor.log'
]

keywords = ['enable_verification', 'Phase 4.75', 'verification', '578 U.S.', '963 F.3d']

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\n   Checking {os.path.basename(log_file)} (last 50 lines):")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                if any(keyword.lower() in line.lower() for keyword in keywords):
                    print(f"   {line.strip()}")

print("\n" + "=" * 80)
print("POSSIBLE ISSUES:")
print("-" * 40)
print("1. File upload might be using a different code path entirely")
print("2. There could be another processor instance cached somewhere")
print("3. The file processing might be going through async queue")
print("4. Docker might not have rebuilt with the changes")

print("\nLet's check if file uploads are going through async processing...")
print("=" * 80)
