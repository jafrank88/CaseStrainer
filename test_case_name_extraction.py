#!/usr/bin/env python3
"""
Test script to verify case name extraction and verification
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.citation_processor import CitationProcessor
from src.citation_verification import CitationVerifier

def test_case_name_extraction():
    """Test case name extraction and verification"""
    
    # Test text with citations and case names
    test_text = """
    In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court held that 
    racial segregation in public schools was unconstitutional. The case involved 
    multiple plaintiffs, including Oliver Brown, whose daughter was denied admission 
    to a white school in Topeka, Kansas.
    
    Similarly, in Miranda v. Arizona, 384 U.S. 436 (1966), the Court established 
    the requirement that police inform suspects of their rights before interrogation.
    
    The Washington Supreme Court in State v. Smith, 181 Wn.2d 412 (2014), addressed 
    similar constitutional issues in the state context.
    """
    
    print("Testing case name extraction and verification...")
    print("=" * 60)
    
    # Step 1: Extract citations with case names
    processor = CitationProcessor()
    enhanced_citations = processor.extract_citations(test_text, extract_case_names=True)
    
    print(f"Extracted {len(enhanced_citations)} citations:")
    for i, citation_data in enumerate(enhanced_citations, 1):
        print(f"  {i}. Citation: {citation_data['citation']}")
        print(f"     Extracted case name: {citation_data.get('case_name', 'None')}")
        print()
    
    # Step 2: Verify citations with case names
    verifier = CitationVerifier()
    verified_citations = []
    
    print("Verifying citations with case names...")
    print("-" * 40)
    
    for citation_data in enhanced_citations:
        citation_text = citation_data['citation']
        extracted_case_name = citation_data.get('case_name')
        
        print(f"Verifying: {citation_text}")
        print(f"Extracted case name: {extracted_case_name}")
        
        # Verify citation with extracted case name
        result = verifier.verify_citation(
            citation_text, 
            context=test_text, 
            extracted_case_name=extracted_case_name
        )
        
        # Add the extracted case name to the result
        result['extracted_case_name'] = extracted_case_name
        
        print(f"Verification result:")
        print(f"  Found: {result.get('found', False)}")
        print(f"  Verified case name: {result.get('case_name_verified', 'None')}")
        print(f"  Extracted case name: {result.get('extracted_case_name', 'None')}")
        print(f"  Name similarity: {result.get('name_similarity', 'None')}")
        print(f"  Highlight: {result.get('highlight', False)}")
        print()
        
        verified_citations.append(result)
    
    print("=" * 60)
    print("Summary:")
    print(f"Total citations processed: {len(verified_citations)}")
    
    # Count citations with extracted case names
    with_extracted_names = sum(1 for c in verified_citations if c.get('extracted_case_name'))
    print(f"Citations with extracted case names: {with_extracted_names}")
    
    # Count citations with verified case names
    with_verified_names = sum(1 for c in verified_citations if c.get('case_name_verified'))
    print(f"Citations with verified case names: {with_verified_names}")
    
    # Count highlighted (mismatched) citations
    highlighted = sum(1 for c in verified_citations if c.get('highlight'))
    print(f"Citations with case name mismatches: {highlighted}")
    
    return verified_citations

if __name__ == "__main__":
    test_case_name_extraction() 