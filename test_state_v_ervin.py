"""
Test script to verify State v. Ervin extraction
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from src.citation_extractor import CitationExtractor

def test_state_v_ervin():
    """Test extraction of State v. Ervin citation."""
    text = """
    We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023).
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335.
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
    Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
    legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820.
    """
    
    extractor = CitationExtractor()
    
    # Extract citations
    citations = extractor.extract_citations(text)
    
    # Find State v. Ervin in the results
    state_v_ervin = None
    for citation in citations:
        if "169 Wn.2d 815" in citation.citation:
            state_v_ervin = citation
            break
    
    print("\nTest Results:" + "="*50)
    if state_v_ervin:
        print(f"✅ Found State v. Ervin citation: {state_v_ervin.citation}")
        if state_v_ervin.extracted_case_name:
            print(f"✅ Extracted case name: {state_v_ervin.extracted_case_name}")
        else:
            print("❌ No case name extracted")
    else:
        print("❌ State v. Ervin not found in citations")
    
    # Print all found citations for debugging
    print("\nAll found citations:")
    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation.citation} - {citation.extracted_case_name or 'No name'}")

if __name__ == "__main__":
    test_state_v_ervin()
