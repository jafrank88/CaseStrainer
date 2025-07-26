#!/usr/bin/env python3
"""
Analyze citations in a specific PDF file.
"""

import re
import fitz  # PyMuPDF
import json
from typing import List, Dict, Optional

def extract_citations_with_context(pdf_path: str) -> List[Dict]:
    """Extract citations with surrounding context from a PDF."""
    doc = fitz.open(pdf_path)
    results = []
    
    # Focus specifically on 195 Wn.2d with more flexible matching
    citation_patterns = [
        r'195\s+Wn\.?\s*2d\s+\d+',  # Specifically 195 Wn.2d with page number
    ]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Use 'text' mode with layout preservation for better text extraction
        text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
        
        for pattern in citation_patterns:
            for match in re.finditer(pattern, text):
                # Get more context around the citation (500 chars before, 200 after)
                start = max(0, match.start() - 500)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                # Try to extract case name from more preceding text
                preceding_text = text[max(0, match.start() - 1000):match.start()]
                case_name = extract_case_name(preceding_text, match.group(0))
                
                results.append({
                    'citation': match.group(0),
                    'page': page_num + 1,
                    'context': context,
                    'case_name': case_name,
                    'preceding_text': preceding_text[-150:],  # Last 150 chars before citation
                })
    
    doc.close()
    return results

def extract_case_name(text: str, citation: str) -> str:
    """Extract case name from text preceding a citation.
    
    Handles various case name formats including:
    - Standard: Party1 v. Party2, 123 Wn.2d 456
    - With ampersands: Lakehaven Water & Sewer Dist. v. City of Fed. Way
    - Multiple v.: State v. Defendant, 123 Wn.2d 456
    - In re: In re Something, 123 Wn.2d 456
    - Multiple parties: Party1, Party2 & Party3 v. Defendant, 123 Wn.2d 456
    """
    # Escape the citation for regex, handling special characters
    escaped_citation = re.escape(citation)
    
    # Define party patterns
    word = r'[A-Za-z0-9\-\.\&\']+'
    party = rf'(?:{word}(?:\s+{word})*)'  # One or more words with allowed characters
    
    # Define patterns in order of specificity
    patterns = [
        # Standard case with comma: Party1 v. Party2, 123 Wn.2d 456
        rf'({party}\sv\.\s{party})\s*,\s*{escaped_citation}',
        
        # Case with ampersand: Party1 & Party2 v. Party3, 123 Wn.2d 456
        rf'({party}(?:\s*&\s*{party})+\sv\.\s{party})\s*,\s*{escaped_citation}',
        
        # Case with "In re": In re Something, 123 Wn.2d 456
        rf'(In\s+re\s+{party})\s*,\s*{escaped_citation}',
        
        # Case with "State v.": State v. Defendant, 123 Wn.2d 456
        rf'(State\s+v\.\s+{party})\s*,\s*{escaped_citation}',
        
        # Case without comma: Party1 v. Party2 123 Wn.2d 456
        rf'({party}\sv\.\s{party})\s+{escaped_citation}',
        
        # Case with multiple v.: State v. Defendant v. Another, 123 Wn.2d 456
        rf'({party}(?:\sv\.\s{party})+)\s*,\s*{escaped_citation}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return ""

def main():
    pdf_path = r"D:\dev\casestrainer\wa_briefs\60179-6.25.pdf"
    print(f"Analyzing citations in: {pdf_path}")
    
    try:
        results = extract_citations_with_context(pdf_path)
        
        # Print results in a readable format
        print(f"\nFound {len(results)} citations in the document:")
        for i, result in enumerate(results[:20]):  # Limit to first 20 for brevity
            print(f"\n=== Citation {i+1} ===")
            print(f"Citation: {result['citation']}")
            print(f"Page: {result['page']}")
            print(f"Case Name: {result['case_name'] or 'Not found'}")
            print("\nContext:")
            print(result['context'])
            print("-" * 80)
        
        # Save full results to file
        with open('citation_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved detailed analysis to citation_analysis.json")
        
    except Exception as e:
        print(f"Error analyzing PDF: {str(e)}")

if __name__ == "__main__":
    main()
