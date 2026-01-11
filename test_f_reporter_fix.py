"""
Test the F.2d, F.3d, F.4th year mismatch fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING F.2d, F.3d, F.4th YEAR MISMATCH FIX")
print("=" * 60)

# Test with a document containing F.2d, F.3d, F.4th citations
test_text = """
Bond v. Utreras, 585 F.3d 1061 (2009). This is a test citation.
Giuffre v. Maxwell, 146 F.4th 165 (2025). Another test.
Brown & Williamson Tobacco Corp. v. F.T.C, 710 F.2d 1165 (1983). Final test.
"""

print("\nTest text:")
print(test_text)

print("\nUsing production endpoint:")
print("-" * 50)

from src.citation_extraction_endpoint import extract_citations_production

result = extract_citations_production(test_text)

print(f"\nResults:")
print(f"  Total citations: {result.get('total', 0)}")

citations = result.get('citations', [])
for cit in citations:
    cit_str = str(cit.get('citation', ''))
    if any(x in cit_str for x in ['F.2d', 'F.3d', 'F.4th']):
        print(f"\n  Citation: {cit_str}")
        print(f"    Case Name: {cit.get('extracted_case_name', 'N/A')}")
        print(f"    Verified: {cit.get('verified', False)}")
        print(f"    Verification Status: {cit.get('verification_status', 'N/A')}")
        print(f"    Verification Error: {cit.get('verification_error', 'None')}")

print("\n" + "=" * 60)
print("EXPECTED RESULTS:")
print("- F.2d, F.3d, F.4th citations should now be verified")
print("- Even with year differences, they should be accepted")
print("- Check logs for 'FED-TOLERANCE' messages")
print("=" * 60)
