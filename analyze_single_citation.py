#!/usr/bin/env python3
"""
Analyze a single citation in a PDF file with detailed context and pattern matching.
"""

import re
import fitz  # PyMuPDF
import json
from typing import List, Dict, Optional

def extract_text_with_context(pdf_path: str, target_citation: str) -> List[Dict]:
    """Extract text with context around a specific citation."""
    doc = fitz.open(pdf_path)
    results = []
    
    # Escape special regex characters from the citation
    escaped_citation = re.escape(target_citation)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Get text with layout preservation
        text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | 
                                          fitz.TEXT_PRESERVE_WHITESPACE |
                                          fitz.TEXT_DEHYPHENATE)
        
        # Look for the citation pattern
        for match in re.finditer(escaped_citation, text):
            # Get more context around the match
            start = max(0, match.start() - 500)
            end = min(len(text), match.end() + 500)
            context = text[start:end]
            
            # Get preceding text for case name extraction
            preceding_text = text[max(0, match.start() - 1000):match.start()]
            
            results.append({
                'page': page_num + 1,
                'context': context,
                'preceding_text': preceding_text,
                'match_position': (match.start(), match.end())
            })
    
    doc.close()
    return results

def find_case_name(text: str, citation: str) -> Dict:
    """Find the case name preceding a citation."""
    # Try multiple patterns in order of specificity
    patterns = [
        # Pattern: Case Name v. Another Name, 123 Wn.2d 456
        r'([A-Z][A-Za-z0-9&\-\s\.]+v\.\s+[A-Z][A-Za-z0-9&\-\s\.]+?)\s*,\s*' + re.escape(citation),
        
        # Pattern with ampersand: Name & Name v. Another, 123 Wn.2d 456
        r'([A-Z][A-Za-z0-9&\-\s\.]+&[A-Za-z0-9&\-\s\.]+v\.\s+[A-Z][A-Za-z0-9&\-\s\.]+?)\s*,\s*' + re.escape(citation),
        
        # More permissive pattern
        r'([A-Z][A-Za-z0-9&\-\s\.]+?)\s*,\s*' + re.escape(citation),
        
        # Pattern without comma: Case Name v. Another 123 Wn.2d 456
        r'([A-Z][A-Za-z0-9&\-\s\.]+v\.\s+[A-Z][A-Za-z0-9&\-\s\.]+?)\s+' + re.escape(citation),
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            case_name = match.group(1).strip()
            # Clean up the case name
            case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
            return {
                'case_name': case_name,
                'pattern_used': pattern,
                'match_position': (match.start(), match.end())
            }
    
    return {'case_name': None, 'reason': 'No matching pattern found'}

def main():
    pdf_path = r"D:\dev\casestrainer\wa_briefs\60179-6.25.pdf"
    target_citation = "195 Wn.2d 742"
    
    print(f"Analyzing citations in: {pdf_path}")
    print(f"Looking for citation: {target_citation}\n")
    
    try:
        # Extract text with context around the citation
        results = extract_text_with_context(pdf_path, target_citation)
        
        if not results:
            print(f"Citation '{target_citation}' not found in the document.")
            return
        
        # Analyze each occurrence of the citation
        for i, result in enumerate(results):
            print(f"\n=== Occurrence {i+1} ===")
            print(f"Page: {result['page']}")
            
            # Try to find the case name
            analysis = find_case_name(result['preceding_text'], target_citation)
            
            if analysis['case_name']:
                print(f"Case Name: {analysis['case_name']}")
                print(f"Pattern Used: {analysis['pattern_used']}")
            else:
                print("Case Name: Not found")
                print(f"Reason: {analysis.get('reason', 'Unknown')}")
            
            # Show the context around the citation
            print("\nContext:")
            print("-" * 80)
            print(result['context'])
            print("-" * 80)
            
            # Show the specific match if found
            if 'match_position' in analysis:
                start, end = analysis['match_position']
                match_text = result['preceding_text'][max(0, start-50):end+50]
                print("\nMatching Text:")
                print("..." + match_text + "...")
            
            print("\n" + "="*100 + "\n")
        
        # Save full results to file
        with open('citation_analysis_detailed.json', 'w', encoding='utf-8') as f:
            json.dump({
                'pdf_path': pdf_path,
                'target_citation': target_citation,
                'results': results,
                'analysis': [find_case_name(r['preceding_text'], target_citation) for r in results]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved detailed analysis to citation_analysis_detailed.json")
        
    except Exception as e:
        print(f"Error analyzing PDF: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
