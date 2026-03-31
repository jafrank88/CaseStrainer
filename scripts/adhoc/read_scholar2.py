import re

# Read around line 5050-5120 (date extraction and validation)
with open('/app/src/unified_verification_master.py', 'r') as f:
    lines = f.readlines()

# Print lines 5050-5120
for i, line in enumerate(lines[5049:5120], start=5050):
    print(f"{i}: {line}", end='')
