"""
Check WL citation verification status in clean pipeline
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("CHECKING WL CITATION IN CLEAN PIPELINE")
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
        
        # Check if it should be marked as proprietary
        import re
        is_wl = re.search(r"\d{4}\s+WL\s+\d+", cit.citation)
        print(f"\n  Should be marked as proprietary: {bool(is_wl and not cit.verified)}")
        
        if is_wl and not cit.verified:
            print("  ✅ Should have 'Unverified due to proprietary format'")
            # Add the proprietary marking manually to test
            cit.verification_status = "proprietary_format"
            cit.verification_error = "Unverified due to proprietary format"
            print(f"  After manual marking - verification_error: {cit.verification_error}")

print("\n" + "=" * 60)
print("The issue is that the proprietary format marking happens in")
print("unified_citation_processor_v2.py, but clean_extraction_pipeline.py")
print("doesn't call that code. The clean pipeline returns citations")
print("without the proprietary format marking.")
