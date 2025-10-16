import re

# Test the neutral citation pattern
text = "Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977 (2016)"

patterns = [
    r'\b20\d{2}-(?:NM|NMCA)-\d{1,5}\b',  # New Mexico (hyphenated)
    r'\b\d+\s+P\.3d\s+\d+',  # P.3d citations
]

print(f"Testing text: {text}\n")

for i, pattern in enumerate(patterns):
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    print(f"Pattern {i+1}: {pattern}")
    if matches:
        for match in matches:
            print(f"  Found: '{match.group()}' at position {match.start()}-{match.end()}")
    else:
        print(f"  No matches")
    print()

# Now test the context isolator logic
print("=" * 60)
print("Testing Context Isolation:")
print("=" * 60)

# Simulate what the context isolator should do
citation_positions = []
for pattern in patterns:
    for match in re.finditer(pattern, text, re.IGNORECASE):
        citation_positions.append((match.start(), match.end(), match.group()))

citation_positions.sort(key=lambda x: x[0])

print(f"\nAll citations found (sorted by position):")
for start, end, cit_text in citation_positions:
    print(f"  {start:3d}-{end:3d}: {cit_text}")

# For "388 P.3d 977", find the previous citation boundary
target_citation = "388 P.3d 977"
target_start = text.find(target_citation)
target_end = target_start + len(target_citation)

print(f"\nTarget citation: '{target_citation}' at {target_start}-{target_end}")

# Find previous citation
previous_citation_end = 0
for cit_start, cit_end, cit_text in citation_positions:
    if cit_end < target_start:
        previous_citation_end = max(previous_citation_end, cit_end)
        print(f"  Previous citation: '{cit_text}' ends at {cit_end}")
    elif cit_start >= target_start:
        break

# Extract context
context_start = previous_citation_end + 1
context = text[context_start:target_start].strip()

print(f"\nContext boundaries: {context_start} to {target_start}")
print(f"Extracted context: '{context}'")
print(f"\nThis should be the case name WITHOUT '2017-NM-007'")
