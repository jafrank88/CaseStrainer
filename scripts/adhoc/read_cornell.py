import redis, os, json, sys, re
sys.path.insert(0, '/app')

# Read the unified_verification_master.py file around line 4776 (Cornell LII)
with open('/app/src/unified_verification_master.py', 'r') as f:
    lines = f.readlines()
    
# Print lines 4775-4850 (around _verify_with_cornell_lii)
for i, line in enumerate(lines[4774:4850], start=4775):
    print(f"{i}: {line}", end='')
