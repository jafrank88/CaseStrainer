import re

# Read around line 5050-5100 (Google Scholar result creation)
with open('/app/src/unified_verification_master.py', 'r') as f:
    lines = f.readlines()

# Print lines 5050-5100
for i, line in enumerate(lines[5049:5100], start=5050):
    if 'scholar' in line.lower() or 'return' in line or 'VerificationResult' in line:
        print(f"{i}: {line}", end='')
