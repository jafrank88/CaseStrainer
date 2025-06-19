#!/usr/bin/env python3
"""
Test script to verify the full pipeline with improved case name extraction
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.citation_processor import CitationProcessor
from src.citation_verification import CitationVerifier

def test_full_pipeline():
    """Test the full pipeline with case name extraction"""
    
    # Test text with citations
    test_text = """
    In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court held that 
    racial segregation in public schools was unconstitutional. The case involved 
    multiple plaintiffs, including Oliver Brown, whose daughter was denied admission 
    to a white school.
    
    The Washington Supreme Court in State v. Smith, 123 Wn.2d 456, addressed similar 
    issues regarding search and seizure procedures. This case established important 
    precedent for law enforcement practices.
    
    Another important case is Terhune v. A. H. Robins Co., 90 Wn.2d 9, which 
    established important precedent for product liability cases.
    """
    
    print("=== Testing Full Pipeline with Case Name Extraction ===\n")
    
    # Step 1: Extract citations with case names
    processor = CitationProcessor()
    citations = processor.extract_citations(test_text, extract_case_names=True)
    
    print(f"Extracted {len(citations)} citations:")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. Citation: {citation['citation']}")
        print(f"     Extracted Case Name: {citation.get('case_name', 'None')}")
        print()
    
    # Step 2: Verify citations with extracted case names
    verifier = CitationVerifier()
    print("Verification Results:")
    print("-" * 80)
    
    for i, citation in enumerate(citations, 1):
        citation_text = citation['citation']
        extracted_case_name = citation.get('case_name')
        
        print(f"Citation {i}: {citation_text}")
        print(f"Extracted Case Name: {extracted_case_name}")
        
        # Verify the citation
        result = verifier.verify_citation(citation_text, extracted_case_name=extracted_case_name)
        
        print(f"Verified: {result.get('found', False)}")
        print(f"Verified Case Name: {result.get('case_name', 'None')}")
        print(f"Case Name Extracted: {result.get('case_name_extracted', 'None')}")
        print(f"Case Name Verified: {result.get('case_name_verified', 'None')}")
        print(f"Name Similarity: {result.get('name_similarity', 'N/A')}")
        print(f"Highlight: {result.get('highlight', False)}")
        print("-" * 80)

if __name__ == "__main__":
    test_full_pipeline() 