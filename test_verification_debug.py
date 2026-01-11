"""
Test to check if verification is running for F.2d, F.3d, F.4th citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("VERIFICATION DEBUG FOR F.2d, F.3d, F.4th")
print("=" * 60)

# Test with a single F.3d citation
test_text = "Bond v. Utreras, 585 F.3d 1061 (2009)."

print(f"\nTest text: {test_text}")
print("-" * 50)

from src.citation_extraction_endpoint import extract_citations_production

result = extract_citations_production(test_text)

print(f"\nResults:")
print(f"  Total citations: {result.get('total', 0)}")

citations = result.get('citations', [])
for cit in citations:
    cit_str = str(cit.get('citation', ''))
    print(f"\n  Citation: {cit_str}")
    print(f"    Verified: {cit.get('verified', False)}")
    print(f"    Verification Status: {cit.get('verification_status', 'N/A')}")
    print(f"    Verification Error: {cit.get('verification_error', 'None')}")

print("\n" + "=" * 60)
print("Checking if verification sources support F.2d, F.3d, F.4th:")
print("-" * 50)

# Check the verification sources
from src.fast_verification_system import FastVerificationSystem

verifier = FastVerificationSystem()

# Test a known F.3d citation
test_citation = "585 F.3d 1061"
print(f"\nTesting citation: {test_citation}")

# Check each source
sources = [
    ('CourtListener API', verifier._verify_with_courtlistener),
    ('Justia', verifier._verify_with_justia),
    ('Google Scholar', verifier._verify_with_google_scholar),
    ('Leagle', verifier._verify_with_leagle),
    ('CaseMine', verifier._verify_with_casemine)
]

for name, verify_func in sources:
    try:
        result = verify_func(test_citation)
        if result and result.get('found'):
            print(f"  {name}: ✅ FOUND")
        else:
            print(f"  {name}: ❌ Not found")
    except Exception as e:
        print(f"  {name}: ❌ Error - {str(e)[:50]}")

print("\n" + "=" * 60)
print("NOTE: F.2d, F.3d, F.4th are Federal Appellate Reporter citations")
print("These should be available on CourtListener, Justia, and Google Scholar")
print("=" * 60)
