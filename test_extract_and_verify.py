#!/usr/bin/env python3
"""
Test script to demonstrate proper citation extraction AND verification
"""

import sys
import os
import json
import logging

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor
# from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier  # Module does not exist

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extract_and_verify():
    """Test the complete pipeline: extract citations and then verify them."""
    
    # Sample text with the Washington citation
    sample_text = """
    John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), 
    modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished).
    """
    
    print("=" * 80)
    print("TESTING COMPLETE CITATION PIPELINE")
    print("=" * 80)
    print(f"Sample text: {sample_text.strip()}")
    print()
    
    # Step 1: Extract citations using CitationExtractor
    print("STEP 1: EXTRACTING CITATIONS")
    print("-" * 40)
    
    extractor = CitationExtractor(
        use_eyecite=True,
        use_regex=True,
        context_window=1000,
        deduplicate=True,
        extract_case_names=True
    )
    
    extracted_citations = extractor.extract(sample_text)
    print(f"Extracted {len(extracted_citations)} citations:")
    
    for i, citation_info in enumerate(extracted_citations, 1):
        print(f"  {i}. {citation_info['citation']}")
        print(f"     Method: {citation_info.get('method', 'unknown')}")
        print(f"     Pattern: {citation_info.get('pattern', 'unknown')}")
        print(f"     Source: {citation_info.get('source', 'unknown')}")
        print(f"     Verified: {citation_info.get('verified', False)}")
        print(f"     Case Name: {citation_info.get('case_name', 'N/A')}")
        print()
    
    # Step 2: Verify each extracted citation using EnhancedMultiSourceVerifier
    print("STEP 2: VERIFYING CITATIONS WITH ENHANCED MULTISOURCE VERIFIER")
    print("-" * 40)
    
    verifier = EnhancedMultiSourceVerifier()
    verified_results = []
    
    for citation_info in extracted_citations:
        citation_text = citation_info['citation']
        print(f"Verifying: {citation_text}")
        
        # Verify the citation
        verification_result = verifier.verify_citation_unified_workflow(
            citation_text, 
            use_cache=False, 
            use_database=False, 
            use_api=True, 
            force_refresh=True
        )
        
        # Merge extraction and verification results
        merged_result = {
            'original_extraction': citation_info,
            'verification_result': verification_result,
            'final_result': {
                'citation': citation_text,
                'extracted_case_name': citation_info.get('case_name', 'N/A'),
                'verified_case_name': verification_result.get('case_name', 'N/A'),
                'canonical_case_name': verification_result.get('case_name', 'N/A'),
                'canonical_date': verification_result.get('canonical_date', 'N/A'),
                'url': verification_result.get('url', 'N/A'),
                'court': verification_result.get('court', 'N/A'),
                'docket_number': verification_result.get('docket_number', 'N/A'),
                'verified': verification_result.get('verified', False),
                'source': verification_result.get('source', 'Unknown'),
                'confidence': verification_result.get('confidence', 0.0),
                'context': citation_info.get('context', '')
            }
        }
        
        verified_results.append(merged_result)
        
        print(f"  Verification result:")
        print(f"    Verified: {verification_result.get('verified', False)}")
        print(f"    Case Name: {verification_result.get('case_name', 'N/A')}")
        print(f"    URL: {verification_result.get('url', 'N/A')}")
        print(f"    Court: {verification_result.get('court', 'N/A')}")
        print(f"    Docket: {verification_result.get('docket_number', 'N/A')}")
        print(f"    Source: {verification_result.get('source', 'Unknown')}")
        print()
    
    # Step 3: Display final results
    print("STEP 3: FINAL RESULTS")
    print("-" * 40)
    
    for i, result in enumerate(verified_results, 1):
        final = result['final_result']
        print(f"Citation {i}: {final['citation']}")
        print(f"  Extracted Case Name: {final['extracted_case_name']}")
        print(f"  Verified Case Name: {final['verified_case_name']}")
        print(f"  Canonical Case Name: {final['canonical_case_name']}")
        print(f"  Canonical Date: {final['canonical_date']}")
        print(f"  URL: {final['url']}")
        print(f"  Court: {final['court']}")
        print(f"  Docket: {final['docket_number']}")
        print(f"  Verified: {final['verified']}")
        print(f"  Source: {final['source']}")
        print(f"  Confidence: {final['confidence']}")
        print()
    
    # Step 4: Summary
    print("STEP 4: SUMMARY")
    print("-" * 40)
    
    verified_count = sum(1 for r in verified_results if r['final_result']['verified'])
    total_count = len(verified_results)
    
    print(f"Total citations extracted: {total_count}")
    print(f"Citations successfully verified: {verified_count}")
    print(f"Success rate: {verified_count/total_count*100:.1f}%")
    
    if verified_count > 0:
        print("\nSuccessfully verified citations:")
        for result in verified_results:
            if result['final_result']['verified']:
                final = result['final_result']
                print(f"  ✓ {final['citation']} -> {final['canonical_case_name']} ({final['url']})")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("This demonstrates the proper pipeline:")
    print("1. Extract citations using CitationExtractor")
    print("2. Verify each citation using EnhancedMultiSourceVerifier")
    print("3. Merge results to get canonical metadata")
    print("\nThe key is that extraction alone doesn't provide verification -")
    print("you need both steps to get canonical case names and URLs.")

if __name__ == "__main__":
    test_extract_and_verify() 