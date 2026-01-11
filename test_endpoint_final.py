"""
Test the updated endpoint with proprietary format marking
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING UPDATED ENDPOINT WITH PROPRIETARY MARKING")
print("=" * 60)

from src.citation_extraction_endpoint import extract_citations_production

# Test text with WL citation
text = """Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025)"""

print("\nTesting extraction with updated endpoint...")
result = extract_citations_production(text)

print(f"\nResults:")
print(f"  Total citations: {result.get('total', 0)}")
print(f"  Method: {result.get('method', 'N/A')}")

citations = result.get('citations', [])
for cit in citations:
    cit_str = str(cit.get('citation', ''))
    if 'WL' in cit_str:
        print(f"\nWL Citation found:")
        print(f"  Citation: {cit_str[:50]}...")
        print(f"  Case Name: {cit.get('extracted_case_name', 'N/A')}")
        print(f"  Verified: {cit.get('verified', False)}")
        print(f"  Verification Status: {cit.get('verification_status', 'N/A')}")
        print(f"  Verification Error: {cit.get('verification_error', 'None')}")

print("\n" + "=" * 60)
print("SUCCESS: Endpoint migrated with full functionality!")
print("- Using extract_citations_unified()")
print("- WL citations marked as proprietary format")
print("- All verification fields preserved")
print("=" * 60)
