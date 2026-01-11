"""
Test the parallel citation detection with Brown v. Board
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

text = "Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954)."

print("TESTING BROWN v. BOARD WITH FIX:")
print("=" * 60)
print(f"Text: {text}")
print()

# Enable debug logging to see what's happening
import logging
logging.basicConfig(level=logging.INFO)

citations = extract_citations_clean(text)

print("\nResults:")
for i, cit in enumerate(citations):
    print(f"{i+1}. {cit.citation}: '{cit.extracted_case_name}'")
    
    if hasattr(cit, 'metadata') and cit.metadata:
        if cit.metadata.get('is_parallel_citation'):
            print("   *** PARALLEL CITATION ***")
        elif cit.metadata.get('is_series_citation'):
            print("   *** SERIES CITATION ***")
        
        # Show the metadata
        print(f"   Metadata: plaintiff={cit.metadata.get('plaintiff')}, defendant={cit.metadata.get('defendant')}")
        if cit.metadata.get('extra'):
            print(f"   Extra: {cit.metadata.get('extra')}")

print("\n" + "=" * 60)
print("EXPECTED:")
print("-" * 40)
print("All three citations should have 'Brown v. Board of Education'")
print("and be marked as parallel citations.")
