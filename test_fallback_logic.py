"""
Test and fix the fallback logic for standalone citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING FALLBACK LOGIC FOR STANDALONE CITATIONS")
print("=" * 60)

# Test cases that currently return N/A
test_cases = [
    ("28 F.4th 292", "Unknown Case, 28 F.4th 292"),
    ("732 F.2d 1302", "Unknown Case, 732 F.2d 1302"),
    ("855 F.2d 569", "Unknown Case, 855 F.2d 569"),
]

for original_citation, suggested_fix in test_cases:
    print(f"\nTesting: {original_citation}")
    print("-" * 40)
    
    citations = extract_citations_clean(original_citation)
    
    if citations:
        cit = citations[0]
        print(f"Current result: '{cit.extracted_case_name}'")
        
        if cit.extracted_case_name == "N/A":
            print(f"Suggested fix: '{suggested_fix}'")
            print("This provides more information than just N/A")
            
            # Check if we have any metadata
            if cit.metadata:
                print(f"Metadata available: {list(cit.metadata.keys())}")

print("\n" + "=" * 60)
print("PROPOSED SOLUTION:")
print("-" * 60)
print("For citations with no extractable case name:")
print("1. Use 'Unknown Case' instead of 'N/A'")
print("2. Include the citation text for reference")
print("3. This preserves the citation information while indicating")
print("   that the case name couldn't be extracted")
