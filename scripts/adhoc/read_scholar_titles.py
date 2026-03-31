import re

# Read lines 5025-5075 (Google Scholar title extraction and result processing)
with open('/app/src/unified_verification_master.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines[5024:5075], start=5025):
    print(f"{i}: {line}", end='')
