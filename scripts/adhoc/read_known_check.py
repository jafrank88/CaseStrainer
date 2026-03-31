import re

# Read around line 390 to see how known_citations is checked
with open('/app/src/verification_manager.py', 'r') as f:
    lines = f.readlines()

# Print lines 385-420
for i, line in enumerate(lines[384:420], start=385):
    print(f"{i}: {line}", end='')
