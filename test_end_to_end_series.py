"""
Test to verify series citation fix works end-to-end
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.unified_citation_processor_v2 import extract_citations_unified

print("=" * 80)
print("TESTING SERIES CITATION FIX END-TO-END")
print("=" * 80)

# Test the exact text that had the issue
test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."

print(f"\nTest text: {test_text}")
print("\nProcessing with extract_citations_unified...")

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
    
    # Check what's before this citation
    if cit.start_index:
        look_behind = test_text[max(0, cit.start_index - 100):cit.start_index]
        print(f"   Text before: '{look_behind}'")

print("\n" + "=" * 40)
print("EXPECTED BEHAVIOR:")
print("- 2022 WL 15153410 should have case name: 'Doe v. City of New York'")
print("- 855 F.2d 569 should have case name: 'N/A' (series citation fix)")
print("=" * 40)
