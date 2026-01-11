"""
Test clean pipeline exactly as process_text calls it
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."

print("Testing clean pipeline with document_primary_case_name=None:")
try:
    citations = extract_citations_clean(test_text, document_primary_case_name=None)
    print(f"Success! Extracted {len(citations)} citations:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
        if hasattr(cit, 'metadata') and cit.metadata:
            print(f"     metadata: {cit.metadata}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Testing clean pipeline without document_primary_case_name:")
try:
    citations = extract_citations_clean(test_text)
    print(f"Success! Extracted {len(citations)} citations:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
        if hasattr(cit, 'metadata') and cit.metadata:
            print(f"     metadata: {cit.metadata}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
