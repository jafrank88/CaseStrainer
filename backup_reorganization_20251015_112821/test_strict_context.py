"""
Test strict context isolation to prevent case name bleeding.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_strict_context_for_citation,
    extract_case_name_from_strict_context
)

# Test text simulating the 24-2626.pdf issue
test_text = """
We agree with other circuits that orders denying anti-SLAPP motions 
under California's statute are not immediately appealable because such 
orders do not resolve issues "completely separate from the merits of the 
action" and do not render the decision "effectively unreviewable on appeal 
from a final judgment." Will v. Hallock, 546 U.S. 345, 349 (2006) (quoting 
P.R. Aqueduct & Sewer Auth. v. Metcalf & Eddy, Inc., 506 U.S. 139, 144 (1993)).
The appellant's argument relies heavily on Manzari v. Associated Newspapers Ltd., 
830 F.3d 881, 886 (9th Cir. 2016). Anti-SLAPP statutes have been passed in 
various states.
"""

print("=" * 80)
print("STRICT CONTEXT ISOLATION TEST")
print("=" * 80)
print()

# Find all citations
positions = find_all_citation_positions(test_text)
print(f"Found {len(positions)} citations:")
for start, end, cit_text in positions:
    print(f"  - {cit_text} at position {start}-{end}")
print()

# Test each citation
test_cases = [
    {
        'citation': '546 U.S. 345',
        'expected': 'Will v. Hallock'
    },
    {
        'citation': '506 U.S. 139',
        'expected': 'P.R. Aqueduct & Sewer Auth. v. Metcalf & Eddy, Inc.'
    },
    {
        'citation': '830 F.3d 881',
        'expected': 'Manzari v. Associated Newspapers Ltd.'
    }
]

print("=" * 80)
print("EXTRACTION TESTS")
print("=" * 80)
print()

for test_case in test_cases:
    citation = test_case['citation']
    expected = test_case['expected']
    
    # Find the citation position
    cit_start = test_text.find(citation)
    if cit_start == -1:
        print(f"❌ SKIP: Citation '{citation}' not found in text")
        continue
    
    cit_end = cit_start + len(citation)
    
    # Get strict context
    strict_context = get_strict_context_for_citation(
        test_text, cit_start, cit_end, positions, max_lookback=200
    )
    
    # Extract case name
    extracted = extract_case_name_from_strict_context(strict_context, citation)
    
    # Check result
    success = expected.lower() in (extracted or "").lower() if extracted else False
    status = "✅ PASS" if success else "❌ FAIL"
    
    print(f"{status}: {citation}")
    print(f"  Expected: {expected}")
    print(f"  Extracted: {extracted or 'None'}")
    print(f"  Context: '...{strict_context[-100:]}'")
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
