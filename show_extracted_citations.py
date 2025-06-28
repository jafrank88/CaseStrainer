#!/usr/bin/env python3
"""
Simple script to extract and display citations from a URL
"""

import sys
import logging
from src.enhanced_validator_production import extract_text_from_url
from src.citation_extractor import extract_all_citations, count_washington_citations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_extracted_citations(url):
    """Extract and display citations from a URL."""
    print(f"Extracting citations from: {url}")
    print("=" * 60)
    
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
    
    # Step 2: Extract citations with normalization
    print("\nStep 2: Extracting citations (with Wn. -> Wash. normalization)...")
    try:
        citations = extract_all_citations(extracted_text, logger=logger)
        
        print(f"\nFound {len(citations)} total unique citations after normalization and deduplication")
        print("-" * 60)
        
        # Count Washington citations
        washington_stats = count_washington_citations(citations)
        
        print(f"\nWashington Citation Statistics:")
        print(f"  Total Washington citations: {washington_stats['total_washington']}")
        print(f"  From regex: {washington_stats['regex_washington']}")
        print(f"  From eyecite: {washington_stats['eyecite_washington']}")
        
        print(f"\nUnique Washington citations (normalized to Wash. format):")
        print("-" * 60)
        
        for i, citation_info in enumerate(washington_stats['washington_citations'], 1):
            citation = citation_info['citation']
            source = citation_info['source']
            original = citation_info.get('original')
            
            if original and original != citation:
                print(f"{i:3d}. {citation} (source: {source}, normalized from: {original})")
            else:
                print(f"{i:3d}. {citation} (source: {source})")
        
        # Show some non-Washington citations for comparison
        non_washington = [c for c in citations if 'Wash.' not in c['citation']]
        print(f"\nSample of non-Washington citations ({len(non_washington)} total):")
        print("-" * 60)
        for i, citation_info in enumerate(non_washington[:10], 1):
            citation = citation_info['citation']
            source = citation_info['source']
            print(f"{i:3d}. {citation} (source: {source})")
        
        if len(non_washington) > 10:
            print(f"  ... and {len(non_washington) - 10} more")
        
    except Exception as e:
        print(f"Error extracting citations: {e}")
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python show_extracted_citations.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    show_extracted_citations(url) 