"""Test citation extraction from eyecite objects"""
import re

# Simulate eyecite object string representation
test_citations = [
    "FullCaseCitation('146 F.4th 165', groups={'volume': '146', 'reporter': 'F.4th', 'page': '165'}, metadata=...)",
    "FullCaseCitation('346 F.R.D. 102', groups={'volume': '346', 'reporter': 'F.R.D.', 'page': '102'}, metadata=...)",
    "IdCitation('Id.', metadata=IdCitation.Metadata(parenthetical=None, pin_cite=None))",
]

patterns = [
    r"^[A-Za-z]+Citation\('([^']+)'",  # FullCaseCitation('146 F.4th 165', ...)
    r"^[A-Za-z]+Citation\(\"([^\"]+)\"",  # FullCaseCitation("146 F.4th 165", ...)
    r"Citation\('([^']+)'",  # More lenient - just find Citation('...')
]

for citation_str in test_citations:
    print(f"\nTesting: {citation_str[:80]}...")
    extracted = None
    for pattern in patterns:
        match = re.search(pattern, citation_str)
        if match:
            extracted = match.group(1)
            print(f"  ✓ Extracted: '{extracted}' using pattern: {pattern}")
            break
    if not extracted:
        print(f"  ✗ Failed to extract")
