import re

# Read the verify_citation method to see where known_citations is checked
with open('/app/src/unified_verification_master.py', 'r') as f:
    content = f.read()

# Find where known_citations is checked
matches = list(re.finditer(r'known_citation', content, re.IGNORECASE))
print(f"Found {len(matches)} references to known_citation")

# Show context around each match
for i, match in enumerate(matches[:5]):
    start = max(0, match.start() - 200)
    end = min(len(content), match.end() + 200)
    lines = content[start:end].split('\n')
    print(f"\n--- Match {i+1} ---")
    for line in lines:
        if 'known' in line.lower():
            print(f">>> {line}")
        else:
            print(f"    {line}")
