#!/usr/bin/env python3
"""
Test script to debug the specific citation: John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from citation_extractor import CitationExtractor
from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from complex_citation_integration import ComplexCitationIntegrator
from citation_utils import clean_and_validate_citations

def test_specific_citation():
    """Test the specific citation that's not being verified properly."""
    
    # The specific citation from the user
    citation_text = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    
    print(f"Testing citation: {citation_text}")
    print("=" * 80)
    
    # Step 1: Test citation extraction
    print("\n1. Testing Citation Extraction:")
    print("-" * 40)
    
    extractor = CitationExtractor(use_eyecite=False, use_regex=True)
    extracted_citations = extractor.extract_citations(citation_text)
    
    print(f"Extracted {len(extracted_citations)} citations:")
    for i, citation in enumerate(extracted_citations, 1):
        print(f"  {i}. {citation['citation']}")
        print(f"     Method: {citation['method']}")
        print(f"     Pattern: {citation['pattern']}")
        print(f"     Confidence: {citation['confidence']}")
    
    # Step 2: Test citation validation
    print("\n2. Testing Citation Validation:")
    print("-" * 40)
    
    for citation in extracted_citations:
        citation_text = citation['citation']
        is_valid, reason = clean_and_validate_citations([citation_text])
        print(f"Citation: {citation_text}")
        print(f"Valid: {is_valid}")
        print(f"Reason: {reason}")
        print()
    
    # Step 3: Test CourtListener API verification
    print("\n3. Testing CourtListener API Verification:")
    print("-" * 40)
    
    verifier = EnhancedMultiSourceVerifier()
    
    for citation in extracted_citations:
        citation_text = citation['citation']
        print(f"Verifying: {citation_text}")
        
        try:
            # Test CourtListener citation lookup
            cl_result = verifier._verify_with_courtlistener(citation_text)
            print(f"  CourtListener result: {cl_result}")
            
            # Test web search fallback
            web_result = verifier._verify_with_web_search(citation_text)
            print(f"  Web search result: {web_result}")
            
        except Exception as e:
            print(f"  Error: {e}")
        print()
    
    # Step 4: Test complex citation integration
    print("\n4. Testing Complex Citation Integration:")
    print("-" * 40)
    
    integrator = ComplexCitationIntegrator()
    
    try:
        # Process with complex citation integration
        result = integrator.process_text_with_complex_citations_original(citation_text)
        print(f"Complex integration result: {result}")
        
        if 'citations' in result:
            print(f"Found {len(result['citations'])} citations:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"  {i}. {citation}")
        
    except Exception as e:
        print(f"Error in complex integration: {e}")
    
    # Step 5: Test full pipeline
    print("\n5. Testing Full Pipeline:")
    print("-" * 40)
    
    from document_processing import extract_and_verify_citations
    
    try:
        result = extract_and_verify_citations(citation_text)
        print(f"Full pipeline result: {result}")
        
        if 'results' in result:
            print(f"Found {len(result['results'])} results:")
            for i, citation in enumerate(result['results'], 1):
                print(f"  {i}. Citation: {citation.get('citation', 'N/A')}")
                print(f"     Verified: {citation.get('verified', 'N/A')}")
                print(f"     Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"     Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"     Source: {citation.get('source', 'N/A')}")
                print(f"     URL: {citation.get('url', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"Error in full pipeline: {e}")

if __name__ == "__main__":
    test_specific_citation() 