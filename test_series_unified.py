"""
Simple test to check series citation processing
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.unified_citation_processor_v2 import extract_citations_unified

print("=" * 80)
print("TESTING SERIES CITATION WITH UNIFIED PROCESSOR")
print("=" * 80)

# Test the exact text that had the issue
test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."

print(f"\nTest text: {test_text}")

# Process citations
citations = extract_citations_unified(test_text)

print(f"\nResults:")
print(f"  Citations found: {len(citations)}")

# Check citations
print("\nCitations after processing:")
for i, cit in enumerate(citations):
    print(f"\n{i+1}. Citation: {cit.citation}")
    print(f"   Method: {cit.method}")
    print(f"   Extracted case name: {cit.extracted_case_name}")
    print(f"   Start index: {cit.start_index}")
    if hasattr(cit, 'metadata') and cit.metadata:
        print(f"   Metadata: {cit.metadata}")

print("\n" + "=" * 40)
print("EXPECTED BEHAVIOR:")
print("- 2022 WL 15153410 should have case name: 'Doe v. City of New York'")
print("- 855 F.2d 569 should have case name: 'N/A' (series citation fix)")
print("=" * 40)
