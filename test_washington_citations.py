#!/usr/bin/env python3
"""
Test Washington citation extraction and normalization
"""

import sys
import os
import logging
from src.citation_extractor import extract_all_citations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_washington_citations():
    """Test Washington citation extraction and normalization."""
    
    # Sample text with Washington citations
    sample_text = """
    The court cited State v. Smith, 123 Wn.2d 456 (1995) and Doe v. Roe, 456 Wn. App. 789 (2000).
    Other cases include Johnson v. State, 789 Wash. 2d 123 (1998) and Brown v. City, 321 Wash. App. 654 (1999).
    The Pacific Reporter citation is 980 P.2d 742 (1999).
    """
    
    print("Testing Washington citation extraction...")
    print("=" * 60)
    print(f"Sample text: {sample_text.strip()}")
    print()
    
    # Extract citations using unified extractor
    citations = extract_all_citations(sample_text, logger=logger)
    
    print(f"Found {len(citations)} citations:")
    for i, citation_info in enumerate(citations, 1):
        citation = citation_info['citation']
        source = citation_info.get('source', 'unknown')
        print(f"  {i}. {citation} (source: {source})")
    
    # Check for Washington citations specifically
    washington_citations = [c for c in citations if 'Wash.' in c['citation'] or 'Wn.' in c['citation']]
    print(f"\nWashington citations found: {len(washington_citations)}")
    for citation_info in washington_citations:
        print(f"  - {citation_info['citation']}")

if __name__ == "__main__":
    test_washington_citations() 