"""
Test the new extract_citations_unified function
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.unified_case_extraction_master import extract_citations_unified

print("TESTING NEW extract_citations_unified FUNCTION")
print("=" * 60)

# Test text with multiple citations
text = """See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025) and 
Smith v. Jones, 123 F.3d 456 (9th Cir. 2021) and Brown v. Board, 345 U.S. 678 (1952)."""

print("Testing citation extraction...")
citations = extract_citations_unified(text)

print(f"\nFound {len(citations)} citations:")
for i, cit in enumerate(citations):
    print(f"\n{i+1}. Citation: {cit.citation}")
    print(f"   Case Name: {cit.extracted_case_name}")
    print(f"   Date: {cit.extracted_date}")
    print(f"   Method: {cit.method}")
    print(f"   Position: {cit.start_index}-{cit.end_index}")

print("\n" + "=" * 60)
print("Checking if WL citations have proprietary format marking...")

# Check WL citations specifically
for cit in citations:
    if "WL" in cit.citation:
        print(f"\nWL Citation: {cit.citation}")
        print(f"  verification_status: {getattr(cit, 'verification_status', 'N/A')}")
        print(f"  verification_error: {getattr(cit, 'verification_error', 'N/A')}")
        
        # The unified function doesn't add proprietary marking yet
        # That's still in clean_extraction_pipeline.py

print("\n" + "=" * 60)
print("NEXT STEP: Update clean_extraction_pipeline.py to use this function")
print("=" * 60)
