"""
Test the WestLaw pattern fix
"""

import re

print("TESTING WESTLAW PATTERNS")
print("=" * 60)

# Test cases
test_strings = [
    'Allegiant Travel Co. v. Kinzer, No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734',
    'Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166',
    'Nazar v. Harbor Freight Tools USA Inc., No. 2:18-CV-00348-SMJ, 2019 WL 2066127'
]

# Current pattern
current_pattern = r"([A-Za-z][\w\s&\-\.',]*v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[^,]+,\s*)?\d{4}\s+WL\s+\d+"

# Improved pattern that handles multi-word plaintiffs better
improved_pattern = r"([A-Za-z][\w\s&\-\.',]*?(?:[A-Za-z][\w\s&\-\']*\.?\s*)*v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[^,]+,\s*)?\d{4}\s+WL\s+\d+"

print("Testing current pattern:")
print("-" * 40)
for test in test_strings:
    match = re.search(current_pattern, test)
    if match:
        print(f"'{match.group(1)}'")
    else:
        print("No match")

print("\nTesting improved pattern:")
print("-" * 40)
for test in test_strings:
    match = re.search(improved_pattern, test)
    if match:
        print(f"'{match.group(1)}'")
    else:
        print("No match")

print("\n" + "=" * 60)
print("The issue is that the pattern starts matching from the first capital letter,")
print("but it should match the full case name including multi-word plaintiffs.")
