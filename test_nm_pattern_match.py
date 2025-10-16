import re

text = "Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977 (2016)"

# Test the exact pattern from the code
pattern = re.compile(r'\b(20\d{2})-NM(?:CA)?-(\d{1,5})\b', re.IGNORECASE)

print(f"Text: {text}\n")
print(f"Pattern: {pattern.pattern}\n")

matches = list(pattern.finditer(text))
print(f"Number of matches: {len(matches)}")

if matches:
    for match in matches:
        print(f"\nMatch found:")
        print(f"  Full match: '{match.group()}'")
        print(f"  Position: {match.start()}-{match.end()}")
        print(f"  Group 1 (year): '{match.group(1)}'")
        print(f"  Group 2 (number): '{match.group(2)}'")
else:
    print("\n❌ NO MATCHES FOUND")
    
    # Try variations
    print("\nTrying variations:")
    
    variations = [
        r'20\d{2}-NM-\d{1,5}',  # Without word boundaries
        r'\b20\d{2}-NM-\d{1,5}\b',  # With word boundaries
        r'2017-NM-007',  # Literal
    ]
    
    for i, var_pattern in enumerate(variations, 1):
        var_re = re.compile(var_pattern, re.IGNORECASE)
        var_matches = list(var_re.finditer(text))
        print(f"  Variation {i} ({var_pattern}): {len(var_matches)} matches")
        if var_matches:
            print(f"    Found: {[m.group() for m in var_matches]}")
