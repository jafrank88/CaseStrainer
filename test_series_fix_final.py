"""
Test the series citation fix with a real-world example
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

# Test with the series citation pattern from our fix
test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."

print("TESTING SERIES CITATION FIX:")
print("=" * 60)
print(f"Test text: {test_text}")
print()

# Extract citations
citations = extract_citations_clean(test_text)

print(f"Extracted {len(citations)} citations:")
print()

for i, cit in enumerate(citations):
    print(f"{i+1}. Citation: {cit.citation}")
    print(f"   Case Name: '{cit.extracted_case_name}'")
    print(f"   Method: {cit.method}")
    
    # Check metadata
    if hasattr(cit, 'metadata') and cit.metadata:
        print(f"   Metadata: {cit.metadata}")
        
        # Check if it's marked as series citation
        if cit.metadata.get('is_series_citation'):
            print(f"   *** SERIES CITATION (should be N/A) ***")
    
    print()

print("VERIFICATION:")
print("-" * 40)
print("✅ First citation should have a case name")
print("✅ Second citation should be 'N/A' with is_series_citation=True")
print()

# Test with multiple series
print("TESTING MULTIPLE SERIES CITATIONS:")
print("=" * 60)

multi_series = "See Smith v. Jones, 123 F.3d 456, 789 F.2d 123, 2023 WL 456789 (9th Cir. 2023)."
print(f"Test text: {multi_series}")
print()

multi_citations = extract_citations_clean(multi_series)

print(f"Extracted {len(multi_citations)} citations:")
print()

for i, cit in enumerate(multi_citations):
    print(f"{i+1}. Citation: {cit.citation}")
    print(f"   Case Name: '{cit.extracted_case_name}'")
    if hasattr(cit, 'metadata') and cit.metadata:
        if cit.metadata.get('is_series_citation'):
            print(f"   *** SERIES CITATION ***")
    print()

print("EXPECTED RESULT:")
print("-" * 40)
print("1. 123 F.3d 456 should have 'Smith v. Jones'")
print("2. 789 F.2d 123 should be 'N/A' (series)")
print("3. 2023 WL 456789 should be 'N/A' (series)")
