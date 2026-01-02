#!/usr/bin/env python3
"""
Count citations in the PDF file by extracting text and searching for citation patterns.
"""

import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.unified_text_extractor import extract_text_from_file_unified

def count_citations_in_text(text: str) -> dict:
    """Count citations using various patterns."""
    citations = []
    
    # Common citation patterns
    patterns = [
        # Federal reporters
        r'\b\d+\s+F\.(?:2d|3d|Supp\.(?:2d)?)\s+\d+',
        # State reporters (Wash., Cal., etc.)
        r'\b\d+\s+(?:Wn\.|Wash\.|Cal\.|Ill\.|Va\.|N\.C\.|Pa\.|S\.W\.|P\.|N\.E\.|A\.|F\.Supp\.)\s*(?:2d|3d)?\s+\d+',
        # WL citations
        r'\b\d{4}\s+WL\s+\d+',
        # App. D.C. citations
        r'\b\d+\s+App\.\s+D\.C\.\s+\d+',
        # Year-in-format citations (e.g., "2002 WY 183")
        r'\b\d{4}\s+WY\s+\d+',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            citation = match.group(0)
            start_pos = match.start()
            # Get context around citation (100 chars before and after)
            context_start = max(0, start_pos - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            citations.append({
                'citation': citation,
                'position': start_pos,
                'context': context
            })
    
    # Remove duplicates (same citation at same position)
    seen = set()
    unique_citations = []
    for cit in citations:
        key = (cit['citation'], cit['position'])
        if key not in seen:
            seen.add(key)
            unique_citations.append(cit)
    
    return {
        'total': len(unique_citations),
        'citations': unique_citations
    }

def main():
    pdf_path = r'D:\dev\casestrainer\1031351.pdf'
    
    print(f"Extracting text from: {pdf_path}")
    text, method = extract_text_from_file_unified(pdf_path, verbose=True)
    
    print(f"\nExtracted {len(text):,} characters using {method}")
    print(f"Text length: {len(text):,} chars")
    
    # Count citations
    result = count_citations_in_text(text)
    
    print(f"\n{'='*80}")
    print(f"CITATION COUNT RESULTS")
    print(f"{'='*80}")
    print(f"Total unique citations found: {result['total']}")
    print(f"\nCitations found:")
    print(f"{'-'*80}")
    
    # Group by citation type
    citation_types = {}
    for cit in result['citations']:
        citation_text = cit['citation']
        # Determine type
        if 'F.' in citation_text or 'F.Supp' in citation_text:
            cit_type = 'Federal'
        elif 'Wn.' in citation_text or 'Wash.' in citation_text:
            cit_type = 'Washington'
        elif 'WL' in citation_text:
            cit_type = 'Westlaw'
        elif 'App. D.C.' in citation_text:
            cit_type = 'D.C. Appeals'
        elif re.search(r'\d{4}\s+WY\s+\d+', citation_text):
            cit_type = 'Wyoming (year-in-format)'
        else:
            cit_type = 'Other State'
        
        if cit_type not in citation_types:
            citation_types[cit_type] = []
        citation_types[cit_type].append(citation_text)
    
    # Print by type
    for cit_type, citations in sorted(citation_types.items()):
        print(f"\n{cit_type} ({len(citations)} citations):")
        for i, cit in enumerate(sorted(set(citations)), 1):
            print(f"  {i:2d}. {cit}")
    
    # Print all citations with positions
    print(f"\n{'='*80}")
    print(f"ALL CITATIONS (with positions):")
    print(f"{'='*80}")
    for i, cit in enumerate(result['citations'], 1):
        print(f"\n{i:3d}. {cit['citation']}")
        print(f"     Position: {cit['position']:,}")
        print(f"     Context: ...{cit['context'][:150]}...")
    
    return result

if __name__ == '__main__':
    result = main()
    print(f"\n{'='*80}")
    print(f"SUMMARY: Found {result['total']} unique citations in the PDF")
    print(f"{'='*80}")

