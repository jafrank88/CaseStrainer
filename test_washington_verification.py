#!/usr/bin/env python3
"""
Test how many of the 130 normalized Washington citations are verified by CourtListener
"""

import sys
import logging
from src.enhanced_validator_production import extract_text_from_url
from src.citation_extractor import extract_all_citations, count_washington_citations
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_washington_verification(url):
    """Test Washington citation verification with CourtListener."""
    print(f"Testing Washington citation verification from: {url}")
    print("=" * 80)
    
    # Step 1: Extract text from URL
    print("Step 1: Extracting text from URL...")
    try:
        text_result = extract_text_from_url(url)
        if text_result.get('status') != 'success':
            print(f"Error extracting text: {text_result.get('error', 'Unknown error')}")
            return
        
        extracted_text = text_result.get('text', '')
        print(f"Extracted {len(extracted_text)} characters of text")
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        return
    
    # Step 2: Extract and normalize citations
    print("\nStep 2: Extracting and normalizing citations...")
    try:
        citations = extract_all_citations(extracted_text, logger=logger)
        washington_stats = count_washington_citations(citations)
        
        print(f"Found {washington_stats['total_washington']} unique Washington citations after normalization")
        print(f"  From regex: {washington_stats['regex_washington']}")
        print(f"  From eyecite: {washington_stats['eyecite_washington']}")
        
        # Extract just the citation strings for verification
        washington_citation_strings = [citation_info['citation'] for citation_info in washington_stats['washington_citations']]
        
    except Exception as e:
        print(f"Error extracting citations: {e}")
        return
    
    # Step 3: Test CourtListener verification (without web search)
    print(f"\nStep 3: Testing CourtListener verification for {len(washington_citation_strings)} Washington citations...")
    try:
        verifier = EnhancedMultiSourceVerifier()
        
        # Verify citations in batch
        batch_results = verifier.verify_citations_batch_courtlistener(washington_citation_strings)
        
        # Process results
        verified = []
        invalid = []
        errors = []
        
        for i, result in enumerate(batch_results):
            citation_text = result.get('citation', 'unknown')
            verification_status = result.get('verification_status', 'UNKNOWN')
            source = result.get('source', 'Unknown')
            
            if verification_status == 'VERIFIED':
                verified.append({
                    'citation': citation_text,
                    'canonical_name': result.get('canonical_name', 'N/A'),
                    'canonical_url': result.get('canonical_url', 'N/A'),
                    'source': source
                })
            elif 'error' in result:
                errors.append({
                    'citation': citation_text,
                    'error': result.get('error', 'Unknown error')
                })
            else:
                invalid.append(citation_text)
        
        # Summary
        print(f"\nVerification Results:")
        print("=" * 80)
        print(f"Total Washington citations tested: {len(washington_citation_strings)}")
        print(f"Verified by CourtListener: {len(verified)}")
        print(f"Invalid/Not found: {len(invalid)}")
        print(f"Errors: {len(errors)}")
        print(f"Verification rate: {len(verified)/len(washington_citation_strings)*100:.1f}%")
        
        # Show verified citations
        if verified:
            print(f"\nVerified Washington citations ({len(verified)}):")
            print("-" * 80)
            for i, citation_info in enumerate(verified, 1):
                citation = citation_info['citation']
                canonical_name = citation_info['canonical_name']
                canonical_url = citation_info['canonical_url']
                source = citation_info['source']
                
                print(f"{i:3d}. {citation}")
                if canonical_name and canonical_name != 'N/A':
                    print(f"     Case: {canonical_name}")
                if canonical_url and canonical_url != 'N/A':
                    print(f"     URL: {canonical_url}")
                print(f"     Source: {source}")
                print()
        
        # Show some invalid citations for analysis
        if invalid:
            print(f"\nSample of invalid citations ({len(invalid)} total):")
            print("-" * 80)
            for i, citation in enumerate(invalid[:10], 1):
                print(f"{i:3d}. {citation}")
            if len(invalid) > 10:
                print(f"  ... and {len(invalid) - 10} more")
        
        # Show errors if any
        if errors:
            print(f"\nErrors encountered:")
            print("-" * 80)
            for i, error_info in enumerate(errors[:5], 1):
                citation = error_info['citation']
                error = error_info['error']
                print(f"{i:3d}. {citation}: {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_washington_verification.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    test_washington_verification(url) 