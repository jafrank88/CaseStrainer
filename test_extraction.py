#!/usr/bin/env python3
"""
Test script to verify extracted name, extracted date, and hinted extraction functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from enhanced_citation_extractor import EnhancedCitationExtractor

def test_extraction_workflow():
    """Test the extraction workflow with a known citation."""
    print("Testing extraction workflow...")
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test with the user-provided citation and extracted/hinted names
    citation = "199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    extracted_name = "John Doe P v. Thurston County"
    hinted_name = "Thurston County"
    
    print(f"Citation: {citation}")
    print(f"Extracted name: {extracted_name}")
    print(f"Hinted name: {hinted_name}")
    print("-" * 50)
    
    # Run the verification workflow
    result = verifier.verify_citation_unified_workflow(
        citation, 
        extracted_case_name=extracted_name, 
        hinted_case_name=hinted_name
    )
    
    # Display results
    print("RESULTS:")
    print(f"Verified: {result.get('verified')}")
    print(f"Extracted case name: {result.get('extracted_case_name')}")
    print(f"Hinted case name: {result.get('hinted_case_name')}")
    print(f"Final case name: {result.get('case_name')}")
    print(f"Canonical name: {result.get('canonical_name')}")
    print(f"Canonical date: {result.get('canonical_date')}")
    print(f"URL: {result.get('url')}")
    print(f"Source: {result.get('source')}")
    print(f"Verification method: {result.get('verification_method')}")
    
    # Check if extraction is working
    print("\nEXTRACTION STATUS:")
    if result.get('extracted_case_name') == extracted_name:
        print("✅ Extracted name is preserved")
    else:
        print("❌ Extracted name is missing or incorrect")
        
    if result.get('hinted_case_name') == hinted_name:
        print("✅ Hinted name is preserved")
    else:
        print("❌ Hinted name is missing or incorrect")
        
    if result.get('canonical_date'):
        print("✅ Canonical date is extracted")
    else:
        print("❌ Canonical date is missing")
        
    if result.get('case_name') and result.get('case_name') != "Unknown Case":
        print("✅ Final case name is properly set")
    else:
        print("❌ Final case name is missing or incorrect")

def test_extraction():
    extractor = EnhancedCitationExtractor()
    
    # Test with the Washington Supreme Court citation
    test_text = "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)"
    
    print("Testing citation extraction...")
    print(f"Input text: {test_text}")
    
    citations = extractor.extract_complex_citations(test_text)
    
    print(f"\nFound {len(citations)} citations:")
    
    for i, citation in enumerate(citations):
        print(f"\nCitation {i+1}:")
        print(f"  Case Name: {citation.case_name}")
        print(f"  Primary Citation: {citation.primary_citation}")
        print(f"  Parallel Citations: {citation.parallel_citations}")
        print(f"  Is Complex: {len(citation.parallel_citations) > 1 or len(citation.case_history) > 0}")
    
    # Test with a more complex citation that should have parallels
    complex_text = "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716, 8 Media L. Rep. (BNA) 1041 (1982)"
    
    print(f"\n\nTesting complex citation extraction...")
    print(f"Input text: {complex_text}")
    
    complex_citations = extractor.extract_complex_citations(complex_text)
    
    print(f"\nFound {len(complex_citations)} citations:")
    
    for i, citation in enumerate(complex_citations):
        print(f"\nCitation {i+1}:")
        print(f"  Case Name: {citation.case_name}")
        print(f"  Primary Citation: {citation.primary_citation}")
        print(f"  Parallel Citations: {citation.parallel_citations}")
        print(f"  Is Complex: {len(citation.parallel_citations) > 1 or len(citation.case_history) > 0}")

if __name__ == "__main__":
    test_extraction_workflow()
    test_extraction() 