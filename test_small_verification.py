#!/usr/bin/env python3
"""
Test verification on a small sample to understand what's happening.
"""

import json
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_small_verification():
    """Test verification on a small sample."""
    
    # Load a few citations
    with open('casehold_citations_1000.json', 'r', encoding='utf-8') as f:
        citations = json.load(f)
    
    # Take first 5 citations
    test_citations = citations[:5]
    
    verifier = EnhancedMultiSourceVerifier()
    
    for i, citation_data in enumerate(test_citations):
        citation_obj = citation_data['citation']
        case_name = citation_data.get('case_name', '')
        
        print(f"\n=== Test {i+1} ===")
        print(f"Original: {citation_obj}")
        print(f"Case name: {case_name}")
        
        # Extract plain citation string
        if isinstance(citation_obj, str):
            citation = citation_obj
        else:
            citation = str(citation_obj)
            # Try to extract from eyecite format
            import re
            full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation)
            if full_case_match:
                citation = full_case_match.group(1)
            else:
                short_case_match = re.search(r"ShortCaseCitation\('([^']+)'", citation)
                if short_case_match:
                    citation = short_case_match.group(1)
        
        print(f"Extracted citation: {citation}")
        
        try:
            result = verifier.verify_citation_unified_workflow(
                citation, 
                extracted_case_name=case_name
            )
            
            print(f"Verified: {result.get('verified', False)}")
            print(f"Method: {result.get('verification_method', 'unknown')}")
            print(f"Source: {result.get('source', '')}")
            print(f"URL: {result.get('url', '')}")
            print(f"Error: {result.get('error', '')}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_small_verification() 