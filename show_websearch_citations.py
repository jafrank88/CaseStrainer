#!/usr/bin/env python3
"""
Script to show all citations that would be passed to web search
"""

import sys
import logging
from src.enhanced_validator_production import extract_text_from_url
from src.citation_extractor import extract_all_citations, count_washington_citations
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_websearch_citations(url):
    """Show citations that would be passed to web search."""
    print(f"Analyzing citations for web search from: {url}")
    print("=" * 80)
    
    # Step 1: Extract text from URL
    print("Step 1: Extracting text from URL...")
    try:
        text_result = extract_text_from_url(url)
        if text_result.get('status') != 'success':
            print(f"Error extracting text: {text_result.get('error', 'Unknown error')}")
            return
        text = text_result.get('text', '')
        print(f"Extracted {len(text)} characters of text")
    except Exception as e:
        print(f"Error extracting text: {e}")
        return
    
    # Step 2: Extract citations
    print("\nStep 2: Extracting citations...")
    try:
        citations = extract_all_citations(text, logger=logger)
        print(f"Found {len(citations)} total citations")
        
        # Get Washington citations
        washington_citations = [c for c in citations if 'Wash.' in c['citation'] or 'Wn.' in c['citation']]
        washington_citation_strings = [c['citation'] for c in washington_citations]
        
        # Count Washington citations manually
        regex_count = len([c for c in citations if c.get('source') == 'regex' and ('Wash.' in c['citation'] or 'Wn.' in c['citation'])])
        eyecite_count = len([c for c in citations if c.get('source') == 'eyecite' and ('Wash.' in c['citation'] or 'Wn.' in c['citation'])])
        
        print(f"Washington citations: {len(washington_citations)}")
        print(f"  From regex: {regex_count}")
        print(f"  From eyecite: {eyecite_count}")
        
    except Exception as e:
        print(f"Error extracting citations: {e}")
        return
    
    # Step 3: Test CourtListener verification
    print("\nStep 3: Testing CourtListener verification...")
    try:
        verifier = EnhancedMultiSourceVerifier()
        
        # Verify citations in batch
        batch_results = verifier.verify_citations_batch_courtlistener(washington_citation_strings)
        
        # Separate verified and unverified
        verified = []
        unverified = []
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
                unverified.append(citation_text)
        
        # Write unverified citations to file
        with open('citations_for_websearch.txt', 'w', encoding='utf-8') as f:
            for citation in unverified:
                f.write(f"{citation}\n")
        print(f"\nWrote {len(unverified)} citations to 'citations_for_websearch.txt'")
        
        # Summary
        print(f"\nVerification Results:")
        print("=" * 80)
        print(f"Total Washington citations tested: {len(washington_citation_strings)}")
        print(f"Verified by CourtListener: {len(verified)}")
        print(f"Would go to web search: {len(unverified)}")
        print(f"Errors: {len(errors)}")
        print(f"Verification rate: {len(verified)/len(washington_citation_strings)*100:.1f}%")
        
        # Show verified citations
        print(f"\nVerified by CourtListener ({len(verified)}):")
        print("-" * 80)
        for i, citation_info in enumerate(verified, 1):
            print(f"  {i:2d}. {citation_info['citation']}")
            if citation_info.get('canonical_name') and citation_info['canonical_name'] != 'N/A':
                print(f"       Case: {citation_info['canonical_name']}")
        
        # Show citations that would go to web search
        print(f"\nCitations that would go to web search ({len(unverified)}):")
        print("-" * 80)
        for i, citation in enumerate(unverified, 1):
            print(f"  {i:2d}. {citation}")
        
        # Show errors
        if errors:
            print(f"\nErrors encountered ({len(errors)}):")
            print("-" * 80)
            for i, error_info in enumerate(errors, 1):
                print(f"  {i:2d}. {error_info['citation']}")
                print(f"       Error: {error_info['error']}")
        
        # Summary statistics
        print(f"\nSummary:")
        print("=" * 80)
        print(f"Citations saved from web search: {len(verified)}")
        print(f"Citations needing web search: {len(unverified)}")
        print(f"Efficiency gain: {len(verified)/len(washington_citation_strings)*100:.1f}% of citations verified by CourtListener")
        
        return {
            'verified': verified,
            'unverified': unverified,
            'errors': errors,
            'total': len(washington_citation_strings)
        }
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python show_websearch_citations.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    show_websearch_citations(url) 