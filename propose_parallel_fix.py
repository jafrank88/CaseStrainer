"""
Proposed fix to properly handle parallel vs series citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

# Test the current behavior vs proposed fix
test_text = "Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789 (9th Cir. 2020)."

print("CURRENT BEHAVIOR:")
print("=" * 60)
print(f"Text: {test_text}")
print()

citations = extract_citations_clean(test_text)

print("Results:")
for i, cit in enumerate(citations):
    print(f"{i+1}. {cit.citation}: '{cit.extracted_case_name}'")
    if hasattr(cit, 'metadata') and cit.metadata.get('is_series_citation'):
        print("   *** Marked as series citation ***")

print("\nPROBLEM:")
print("-" * 60)
print("These are PARALLEL citations (same case), but the second one")
print("is incorrectly marked as 'N/A' because it's treated as a series citation.")

print("\n\nPROPOSED SOLUTION:")
print("=" * 60)
print("""
To fix this, we need to modify the series citation detection logic in clean_extraction_pipeline.py:

Instead of just checking if there's a previous citation within 100 chars, we should:

1. Check if the previous citation has the SAME plaintiff and defendant
   - If same → It's a parallel citation, use the same case name
   - If different → It's a series citation, use 'N/A'

2. Also check for semicolons which typically separate different cases

Modified logic would be:

```python
# Check if this is NOT the first citation in a series
if citation.start_index and citation.start_index > 0:
    # Look backwards to see if there's another citation within 100 characters
    look_behind = text[max(0, citation.start_index - 100):citation.start_index]
    prev_citation_pattern = r'\\d{4}\\s+WL\\s+\\d+|\\d+\\s+F\\.?(?:2d|3d|Supp\\.?)\\s+\\d+|\\d+\\s+U\\.S\\.\\s+\\d+'
    
    if re.search(prev_citation_pattern, look_behind):
        # Found a previous citation - check if it's the same case
        # Get the plaintiff and defendant from eyecite metadata
        current_plaintiff = getattr(citation.metadata, 'plaintiff', None)
        current_defendant = getattr(citation.metadata, 'defendant', None)
        
        # Find the previous citation and check its parties
        prev_citation = find_previous_citation(citations, citation)
        if prev_citation:
            prev_plaintiff = getattr(prev_citation.metadata, 'plaintiff', None)
            prev_defendant = getattr(prev_citation.metadata, 'defendant', None)
            
            # Check if same case (parallel citation)
            if (current_plaintiff == prev_plaintiff and 
                current_defendant == prev_defendant and 
                current_plaintiff is not None):
                # Same case - it's a parallel citation
                # Use the same case name
                citation.extracted_case_name = prev_citation.extracted_case_name
                citation.metadata["is_parallel_citation"] = True
            else:
                # Different case - it's a series citation
                citation.extracted_case_name = "N/A"
                citation.metadata["is_series_citation"] = True
```

This would ensure:
- Parallel citations get the same case name and cluster together
- Series citations get 'N/A' and don't incorrectly cluster
""")

print("\nTEST WITH PARALLEL CITATIONS:")
print("-" * 60)
parallel_tests = [
    "Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686 (1954).",
    "United States v. Nixon, 418 U.S. 683, 94 S. Ct. 2781 (1974).",
    "Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789 (9th Cir. 2020)."
]

for test in parallel_tests:
    print(f"\nText: {test}")
    cits = extract_citations_clean(test)
    for cit in cits:
        print(f"  {cit.citation}: '{cit.extracted_case_name}'")

print("\nTEST WITH SERIES CITATIONS:")
print("-" * 60)
series_tests = [
    "Smith v. Jones, 123 F.3d 456; Doe v. Roe, 789 F.2d 123 (2020).",
    "See Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789; Another case, 987 F.3d 456."
]

for test in series_tests:
    print(f"\nText: {test}")
    cits = extract_citations_clean(test)
    for cit in cits:
        print(f"  {cit.citation}: '{cit.extracted_case_name}'")
