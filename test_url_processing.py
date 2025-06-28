#!/usr/bin/env python3
"""
Test script to process a URL and verify citations using the enhanced multi-source verifier
"""

import sys
import os
import logging
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from src.enhanced_validator_production import extract_text_from_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_url_processing(url):
    """Test processing a URL and verifying citations found in it."""
    print(f"Testing URL: {url}")
    print("=" * 60)
    
    # Step 1: Extract text from URL
    print("Step 1: Extracting text from URL...")
    try:
        text_result = extract_text_from_url(url)
        if text_result.get('status') != 'success':
            print(f"Error extracting text: {text_result.get('error')}")
            return
        
        extracted_text = text_result.get('text', '')
        print(f"Successfully extracted {len(extracted_text)} characters of text")
        print(f"First 200 characters: {extracted_text[:200]}...")
    except Exception as e:
        print(f"Error extracting text: {e}")
        return
    
    # Step 2: Extract citations
    print("Step 2: Extracting citations...")
    try:
        from src.citation_extractor import extract_all_citations
        citations = extract_all_citations(extracted_text, logger=logger)
        
        print(f"Found {len(citations)} citations:")
        for i, citation_info in enumerate(citations[:10], 1):
            citation = citation_info['citation']
            source = citation_info.get('source', 'unknown')
            print(f"  {i}. {citation} (source: {source})")
        
        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
        
        # Convert to list of strings for verification
        citation_strings = [citation_info['citation'] for citation_info in citations]
        
    except Exception as e:
        logger.error(f"Error extracting citations: {e}")
        return
    
    # Step 3: Verify citations
    print("Step 3: Verifying citations...")
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Verify citations in batch
        batch_results = verifier.verify_citations_batch_courtlistener(citation_strings)
        
        # Process results
        results = []
        for i, result in enumerate(batch_results):
            citation_text = result.get('citation', 'unknown')
            citation_info = citations[i] if i < len(citations) else {}
            
            print(f"\nCitation {i+1}/{len(batch_results)}: {citation_text}")
            print(f"  Result: {result.get('verification_status', 'UNKNOWN')}")
            print(f"  Source: {result.get('source', 'Unknown')}")
            if result.get('canonical_name') and result.get('canonical_name') != 'N/A':
                print(f"  Case name: {result['canonical_name']}")
            elif result.get('case_name') and result.get('case_name') != 'N/A':
                print(f"  Case name: {result['case_name']}")
            if result.get('canonical_url') and result.get('canonical_url') != 'N/A':
                print(f"  URL: {result['canonical_url']}")
            
            results.append(result)
        
    except Exception as e:
        logger.error(f"Error verifying citations: {e}")
        return
    
    # Step 4: Summary
    print(f"\nStep 4: Summary")
    print("=" * 60)
    verified = [r for r in results if r.get('verification_status') == 'VERIFIED' or r.get('verified') == True]
    invalid = [r for r in results if r.get('verification_status') == 'INVALID' or (r.get('verified') == False and r.get('verification_status') != 'VERIFIED')]
    errors = [r for r in results if 'error' in r]
    
    print(f"Total citations processed: {len(results)}")
    print(f"Verified: {len(verified)}")
    print(f"Invalid: {len(invalid)}")
    print(f"Errors: {len(errors)}")
    
    # Report citation paths
    print(f"\nCitation verification paths:")
    verifier.report_citation_paths()
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_url_processing.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    test_url_processing(url) 