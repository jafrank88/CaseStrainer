"""
Simple citation extraction test
"""
import re
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from src.citation_extractor import CitationExtractor

text = """
In determining the plain meaning of a statute, we look to the text of the statute, 
as well as its broader context and the statutory scheme as a whole. 
State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010).
"""

print("Testing extraction of 'State v. Ervin' citation...")
extractor = CitationExtractor()
citations = extractor.extract_citations(text)

print("\nFound citations:")
for i, citation in enumerate(citations, 1):
    print(f"{i}. {citation.citation}")
    if hasattr(citation, 'extracted_case_name') and citation.extracted_case_name:
        print(f"   Extracted name: {citation.extracted_case_name}")
    else:
        print("   No case name extracted")
