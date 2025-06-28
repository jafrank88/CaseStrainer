#!/usr/bin/env python3
"""
Test citation verification with cleaned citations for web search
"""

import sys
import os
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cleaned_citations():
    """Test citation verification with cleaned citations"""
    
    # Read cleaned citations
    cleaned_citations = []
    try:
        with open('cleaned_citations_for_websearch.txt', 'r', encoding='utf-8') as f:
            for line in f:
                citation = line.strip()
                if citation:
                    cleaned_citations.append(citation)
    except FileNotFoundError:
        print("Error: cleaned_citations_for_websearch.txt not found")
        return
    
    print(f"Loaded {len(cleaned_citations)} cleaned citations for verification")
    print("Sample citations:")
    for i, citation in enumerate(cleaned_citations[:5]):
        print(f"  {i+1}. {citation}")
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Run batch verification
    print(f"\nStarting batch verification for {len(cleaned_citations)} citations...")
    results = verifier.verify_citations_batch_courtlistener(cleaned_citations)
    
    # Analyze results
    verified = [r for r in results if r.get('verified')]
    unverified = [r for r in results if not r.get('verified')]
    
    print(f"\n=== VERIFICATION RESULTS ===")
    print(f"Total citations processed: {len(results)}")
    print(f"Verified by CourtListener: {len(verified)}")
    print(f"Not found (need web search): {len(unverified)}")
    print(f"Verification rate: {len(verified)/len(results)*100:.1f}%")
    
    # Save unverified citations for web search
    unverified_citations = []
    for result in unverified:
        citation = result.get('citation', '')
        if citation:
            unverified_citations.append(citation)
    
    # Write unverified citations to file
    with open('citations_for_websearch.txt', 'w', encoding='utf-8') as f:
        for citation in unverified_citations:
            f.write(f"{citation}\n")
    
    print(f"\nSaved {len(unverified_citations)} unverified citations to citations_for_websearch.txt")
    
    # Show some examples of unverified citations
    if unverified_citations:
        print("\nSample unverified citations:")
        for i, citation in enumerate(unverified_citations[:10]):
            print(f"  {i+1}. {citation}")
    
    # Show some examples of verified citations
    if verified:
        print("\nSample verified citations:")
        for i, result in enumerate(verified[:5]):
            citation = result.get('citation', '')
            case_name = result.get('canonical_name', 'N/A')
            url = result.get('canonical_url', 'N/A')
            print(f"  {i+1}. {citation}")
            print(f"     Case: {case_name}")
            print(f"     URL: {url}")

if __name__ == "__main__":
    test_cleaned_citations() 