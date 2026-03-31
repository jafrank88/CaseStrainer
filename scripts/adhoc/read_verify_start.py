import re

# Read the verify_citation method around line 839
with open('/app/src/unified_verification_master.py', 'r') as f:
    lines = f.readlines()

# Print lines 839-900 (verify_citation method start)
for i, line in enumerate(lines[838:900], start=839):
    print(f"{i}: {line}", end='')
