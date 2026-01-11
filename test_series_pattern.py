"""
Test the regex pattern
"""

import re

# Test the text before the second citation
text_before = "Doe v. City of New York, 2022 WL 15153410, "

# Pattern from our fix
prev_citation_pattern = r'\d{4}\s+WL\s+\d+|\d+\s+F\.?(?:2d|3d|Supp\.?)\s+\d+|\d+\s+U\.S\.\s+\d+'

print("Testing pattern:", prev_citation_pattern)
print("Text:", text_before)
print()

match = re.search(prev_citation_pattern, text_before)
if match:
    print(f"✅ Pattern matched: '{match.group()}'")
    print("This should trigger the series citation fix!")
else:
    print("❌ Pattern did not match")
    print("This explains why the fix isn't working")
    
    # Let's test individual parts
    patterns = [
        r'\d{4}\s+WL\s+\d+',
        r'\d+\s+F\.?(?:2d|3d|Supp\.?)\s+\d+',
        r'\d+\s+U\.S\.\s+\d+'
    ]
    
    print("\nTesting individual patterns:")
    for p in patterns:
        if re.search(p, text_before):
            print(f"  ✅ {p} matched")
        else:
            print(f"  ❌ {p} did not match")
