"""
Test to find the exact error when calling clean pipeline from process_text
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Try the exact same code as process_text
try:
    from src.clean_extraction_pipeline import extract_citations_clean
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    document_primary_case_name = None
    
    print("Calling extract_citations_clean...")
    citations = extract_citations_clean(test_text, document_primary_case_name=document_primary_case_name)
    print(f"Success! Got {len(citations)} citations")
    
except Exception as e:
    print(f"Error occurred: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
