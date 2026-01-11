"""
Test WL citations when they appear close together
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING WL CITATIONS IN PROXIMITY")
print("=" * 60)

# Test with multiple WL citations close together (as they might appear in the document)
text = """Doe v. Columbia Univ., 2024 WL 4149252. Mastriano v. Gregory, 2024 WL 4003343. 
Doe v. Teachers Council, Inc., 2024 WL 1232082. Travel Co. v. Kinzer, 2022 WL 2819734."""

print(f"Text: {text}")
print()

citations = extract_citations_clean(text)

print("\nResults:")
for i, cit in enumerate(citations):
    print(f"\n{i+1}. {cit.citation}")
    print(f"   Case name: '{cit.extracted_case_name}'")
    print(f"   Start: {cit.start_index}, End: {cit.end_index}")
    
    if hasattr(cit, 'metadata') and cit.metadata:
        if cit.metadata.get('is_series_citation'):
            print("   ⚠️  Marked as SERIES citation")
        elif cit.metadata.get('is_parallel_citation'):
            print("   ✓ Marked as PARALLEL citation")
        print(f"   Plaintiff: {cit.metadata.get('plaintiff')}")
        print(f"   Defendant: {cit.metadata.get('defendant')}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 60)
print("The issue is likely that our series citation detection is too aggressive.")
print("It's marking citations as 'series' when they're actually independent")
print("citations that just happen to be near each other.")
