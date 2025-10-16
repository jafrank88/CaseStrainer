#!/usr/bin/env python3
import re

# Define the new abbreviation-aware pattern
legal_abbrev = r'(?:U\.S\.|Sec\'y|Gov\'t|Dep\'t|Att\'y|Dist\.|Comm\'r|Ass\'n|Bd\.|Comm\'n|Div\.|Sch\.|Univ\.|Coll\.)'
word_component = r'(?:' + legal_abbrev + r'|[A-Z][a-z]+(?:\'[a-z]+)?|[A-Z]\.(?:[A-Z]\.)*|of|for|the|and|&)'
party_pattern = word_component + r'(?:\s+' + word_component + r')*'

pattern = f'({party_pattern})\\s+v\\.\\s+({party_pattern})(?=\\s*,?\\s*(?:\\d|\\[|\\(|$))'

test_cases = [
    "Department of Education v. California, 123 U.S. 456",
    "E. Palo Alto v. U.S. Dep't of Health, 789 F.3d 012",
    "Tootle v. Sec'y of Navy, 456 P.2d 789",
    "Franklin v. Massachusetts, 505 U.S. 788"
]

compiled = re.compile(pattern, re.IGNORECASE)

print("Testing new abbreviation-aware pattern:\n")
for test in test_cases:
    match = compiled.search(test)
    if match:
        print(f"✓ '{test}'")
        print(f"  Plaintiff: '{match.group(1)}'")
        print(f"  Defendant: '{match.group(2)}'")
    else:
        print(f"✗ '{test}' - NO MATCH")
    print()
