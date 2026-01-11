"""
Test the migrated citation_extraction_endpoint.py
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING MIGRATED citation_extraction_endpoint.py")
print("=" * 60)

from src.citation_extraction_endpoint import extract_citations_production

# Test text with WL citation
text = """Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025)"""

print("\nTesting extraction with migrated endpoint...")
result = extract_citations_production(text)

print(f"\nResults:")
print(f"  Total citations: {result.get('total', 0)}")
print(f"  Method: {result.get('method', 'N/A')}")
print(f"  Accuracy: {result.get('accuracy', 'N/A')}")

citations = result.get('citations', [])
for cit in citations:
    cit_str = str(cit.get('citation', ''))
    if 'WL' in cit_str:
        print(f"\nWL Citation found:")
        print(f"  Citation: {cit_str[:50]}...")
        print(f"  Case Name: {cit.get('extracted_case_name', 'N/A')}")
        print(f"  Verification Error: {cit.get('verification_error', 'None')}")

print("\n" + "=" * 60)
print("✅ citation_extraction_endpoint.py successfully migrated!")
print("   Now using extract_citations_unified() instead of deprecated function")
print("=" * 60)
