"""
Test the WL proprietary format fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING WL PROPRIETARY FORMAT FIX")
print("=" * 60)

# Test text with WL citation
text = """Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025)"""

print("Processing WL citation...")
citations = extract_citations_clean(text)

for cit in citations:
    if "WL" in cit.citation:
        print(f"\nWL Citation: {cit.citation}")
        print(f"  extracted_case_name: {cit.extracted_case_name}")
        print(f"  verified: {cit.verified}")
        print(f"  verification_status: {getattr(cit, 'verification_status', 'N/A')}")
        print(f"  verification_error: {getattr(cit, 'verification_error', 'N/A')}")
        
        # Check if it was marked
        if hasattr(cit, 'verification_status') and cit.verification_status == "proprietary_format":
            print("  ✅ SUCCESS: Marked as 'Unverified due to proprietary format'")
        else:
            print("  ❌ FAILED: Not marked as proprietary format")

# Test with multiple WL citations
print("\n" + "=" * 60)
print("TESTING MULTIPLE WL CITATIONS:")
print("-" * 50)

text2 = """See Smith v. Jones, 2021 WL 123456, at 2 and Doe v. Roe, 2022 WL 789012, at 5. Also see Brown v. Board, 2023 WL 345678."""
citations2 = extract_citations_clean(text2)

wl_count = 0
for cit in citations2:
    if "WL" in cit.citation:
        wl_count += 1
        print(f"\nWL Citation #{wl_count}: {cit.citation}")
        print(f"  verification_error: {getattr(cit, 'verification_error', 'N/A')}")

print(f"\nTotal WL citations found: {wl_count}")
print(f"All should be marked as 'Unverified due to proprietary format'")
