"""
Test the parallel citation fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING PARALLEL CITATION FIX")
print("=" * 60)

# Test cases
test_cases = [
    ("Parallel citations (same case)", "Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789 (9th Cir. 2020)."),
    ("Series citations (different cases)", "Smith v. Jones, 123 F.3d 456; Doe v. Roe, 789 F.2d 123 (9th Cir. 2020)."),
    ("Mixed case", "See Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789; Doe v. Roe, 987 F.3d 456 (2020)."),
    ("Supreme Court parallel", "Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954)."),
    ("Multiple series", "See Smith v. Jones, 123 F.3d 456, 789 F.2d 123, 2023 WL 456789 (9th Cir. 2023).")
]

for desc, text in test_cases:
    print(f"\n{desc}:")
    print("-" * 40)
    print(f"Text: {text}")
    print()
    
    citations = extract_citations_clean(text)
    
    print("Results:")
    for i, cit in enumerate(citations):
        print(f"{i+1}. {cit.citation}: '{cit.extracted_case_name}'")
        
        if hasattr(cit, 'metadata') and cit.metadata:
            if cit.metadata.get('is_parallel_citation'):
                print("   *** PARALLEL CITATION ***")
            elif cit.metadata.get('is_series_citation'):
                print("   *** SERIES CITATION ***")
    
    print("\n" + "=" * 60)

print("\nEXPECTED RESULTS:")
print("-" * 40)
print("✅ Parallel citations should have the SAME case name")
print("✅ Series citations should have 'N/A' for subsequent citations")
print("✅ Mixed cases should handle both correctly")
