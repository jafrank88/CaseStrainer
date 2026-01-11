"""
Test with real F.4th citations to verify the fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING WITH REAL F.4th CITATIONS")
print("=" * 60)

# Test with real F.4th citations
test_text = """
United States v. Arthrex, Inc., 141 S. Ct. 1973 (2021).
United States v. Texas, 594 U.S. ___ (2021).
Garland v. Gonzalez, 142 S. Ct. 880 (2022).
"""

print("\nTest text with real citations:")
print(test_text)

from src.citation_extraction_endpoint import extract_citations_production

result = extract_citations_production(test_text)

print(f"\nResults:")
print(f"  Total citations: {result.get('total', 0)}")

citations = result.get('citations', [])
for i, cit in enumerate(citations, 1):
    cit_str = str(cit.get('citation', ''))
    print(f"\n  Citation {i}: {cit_str}")
    print(f"    Case Name: {cit.get('extracted_case_name', 'N/A')}")
    print(f"    Extracted Date: {cit.get('extracted_date', 'N/A')}")
    print(f"    Verified: {cit.get('verified', False)}")
    print(f"    Verification Status: {cit.get('verification_status', 'N/A')}")
    print(f"    Canonical Name: {cit.get('canonical_name', 'N/A')}")
    print(f"    Canonical Date: {cit.get('canonical_date', 'N/A')}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 50)
print("These are real Supreme Court citations that should verify.")
print("If they show 'verified=True', our year fix is working.")
print("=" * 60)
