#!/usr/bin/env python3

import re

def clean_extracted_case_name(case_name: str) -> str:
    """Test the current cleaner function."""
    if not case_name:
        return case_name

    name = case_name

    # Remove leading punctuation and whitespace
    name = re.sub(r'^[\s\.,;:]+', '', name)
    # Remove trailing punctuation and whitespace
    name = re.sub(r'[\s\.,;:]+$', '', name)

    # Remove obvious prose/sentence starters before a case name
    cleanup_patterns = [
        r'^(?:that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*',
        # FIXED: Only remove non-alpha characters at the start, not entire words
        r'^[^A-Za-z]*',
    ]
    for pattern in cleanup_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)

    # If the core "X v. Y" is present, trim around it to avoid extra prose
    v_match = re.search(r'([A-Z][A-Za-z0-9&\.\'\s-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\.\'\s-]+)', name)
    if v_match:
        print(f"V match found:")
        print(f"  Group 1 (plaintiff): '{v_match.group(1)}'")
        print(f"  Group 2 (defendant): '{v_match.group(2)}'")
        name = f"{v_match.group(1).strip()} v. {v_match.group(2).strip()}"
    else:
        print("No V match found")

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    return name

# Test with the problematic case name
test_cases = [
    "Statutory interpretation is also an issue of law we review de novo. Spokane County v. Dep't of Fish & Wildlife",
    "Spokane County v. Dep't of Fish & Wildlife",
    "Dep't of Fish & Wildlife"
]

for test_case in test_cases:
    print(f"\nTesting: '{test_case}'")
    result = clean_extracted_case_name(test_case)
    print(f"Result: '{result}'")

# Test the regex pattern directly
print(f"\n" + "="*60)
print("Testing the regex pattern directly:")
pattern = r'([A-Z][A-Za-z0-9&\.\'\s-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\.\'\s-]+)'
test_text = "Spokane County v. Dep't of Fish & Wildlife"

match = re.search(pattern, test_text)
if match:
    print(f"Match found:")
    print(f"  Full: '{match.group(0)}'")
    print(f"  Group 1: '{match.group(1)}'")
    print(f"  Group 2: '{match.group(2)}'")
else:
    print("No match found")

# Test with a simpler pattern
print(f"\nTesting with simpler pattern:")
simple_pattern = r'([A-Z][^v]+?)\s+v\.\s+([A-Z][^,]+)'
match2 = re.search(simple_pattern, test_text)
if match2:
    print(f"Simple match found:")
    print(f"  Full: '{match2.group(0)}'")
    print(f"  Group 1: '{match2.group(1)}'")
    print(f"  Group 2: '{match2.group(2)}'")
else:
    print("No simple match found")
