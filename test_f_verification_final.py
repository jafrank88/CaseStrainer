"""
Test F.2d, F.3d, F.4th verification fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING F.2d, F.3d, F.4th VERIFICATION FIX")
print("=" * 60)

# Test with multiple F.2d, F.3d, F.4th citations
test_text = """
Bond v. Utreras, 585 F.3d 1061 (2009). This is a test citation.
Giuffre v. Maxwell, 146 F.4th 165 (2025). Another test.
Brown & Williamson Tobacco Corp. v. F.T.C, 710 F.2d 1165 (1983). Final test.
"""

print("\nTest text:")
print(test_text)

from src.citation_extraction_endpoint import extract_citations_production

result = extract_citations_production(test_text)

print(f"\nResults:")
print(f"  Total citations: {result.get('total', 0)}")

citations = result.get('citations', [])
f_count = 0
for cit in citations:
    cit_str = str(cit.get('citation', ''))
    if any(x in cit_str for x in ['F.2d', 'F.3d', 'F.4th']):
        f_count += 1
        print(f"\n  Citation {f_count}: {cit_str}")
        print(f"    Case Name: {cit.get('extracted_case_name', 'N/A')}")
        print(f"    Verified: {cit.get('verified', False)}")
        print(f"    Verification Status: {cit.get('verification_status', 'N/A')}")
        print(f"    Verification Error: {cit.get('verification_error', 'None')}")

print(f"\nSUMMARY:")
print(f"  Total F.2d/F.3d/F.4th citations: {f_count}")
print(f"  Expected: All should be verified (year comparison skipped)")
print("=" * 60)
