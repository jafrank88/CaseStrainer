import re

# Read around line 540 (create_possible_match year validation)
with open('/app/src/unified_verification_master.py', 'r') as f:
    lines = f.readlines()

# Print lines 540-570 (year validation in create_possible_match)
for i, line in enumerate(lines[539:570], start=540):
    print(f"{i}: {line}", end='')
