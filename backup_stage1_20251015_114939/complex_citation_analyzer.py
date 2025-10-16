#!/usr/bin/env python3
"""
Complex Citation Analyzer

This module analyzes complex citation strings to understand why they don't generate full data.
"""

import re
import json
from typing import Dict, List, Optional

def analyze_complex_citation(text: str) -> Dict:
    """
    Analyze a complex citation string to understand its structure.
    
    Args:
        text: The complex citation string to analyze
        
    Returns:
        Dict containing analysis results
    """
    
    analysis = {
        'original_text': text,
        'components': {},
        'issues': [],
        'recommendations': []
    }
    
    # Extract case name
    case_name_match = re.search(r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z])', text)
    if case_name_match:
        analysis['components']['case_name'] = case_name_match.group(1).strip()
    
    # Extract all citations
    citations = []
    
    # Washington App citations
    wn_app_matches = re.finditer(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', text)
    for match in wn_app_matches:
        citations.append({
            'type': 'Wn. App.',
            'volume': match.group(1),
            'page': match.group(2),
            'full': f"{match.group(1)} Wn. App. {match.group(2)}",
            'position': match.span()
        })
    
    # Pacific Reporter citations
    p3d_matches = re.finditer(r'\b(\d+)\s+P\.3d\s+(\d+)\b', text)
    for match in p3d_matches:
        citations.append({
            'type': 'P.3d',
            'volume': match.group(1),
            'page': match.group(2),
            'full': f"{match.group(1)} P.3d {match.group(2)}",
            'position': match.span()
        })
    
    analysis['components']['citations'] = citations
    
    # Extract pinpoint pages
    pinpoint_matches = re.findall(r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)', text)
    analysis['components']['pinpoint_pages'] = [p for p in pinpoint_matches if p.isdigit()]
    
    # Extract docket numbers
    docket_matches = re.findall(r'No\.\s*([0-9\-]+)', text)
    analysis['components']['docket_numbers'] = docket_matches
    
    # Extract case history
    history_matches = re.findall(r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)', text)
    analysis['components']['case_history'] = history_matches
    
    # Extract publication status
    status_match = re.search(r'\((unpublished|published|memorandum|per\s+curiam)\)', text, re.IGNORECASE)
    if status_match:
        analysis['components']['publication_status'] = status_match.group(1)
    
    # Extract year
    year_match = re.search(r'\((\d{4})\)', text)
    if year_match:
        analysis['components']['year'] = year_match.group(1)
    
    # Analyze issues
    if len(citations) > 1:
        analysis['issues'].append("Multiple citations detected - system may split them into separate entries")
    
    if analysis['components'].get('case_history'):
        analysis['issues'].append("Case history markers present - may confuse citation verification")
    
    if analysis['components'].get('docket_numbers'):
        analysis['issues'].append("Docket numbers present - not typically verified by citation APIs")
    
    if analysis['components'].get('publication_status') == 'unpublished':
        analysis['issues'].append("Unpublished case - may not be available in citation databases")
    
    # Generate recommendations
    if len(citations) > 1:
        analysis['recommendations'].append("Consider treating as a single complex citation rather than multiple separate citations")
    
    if analysis['components'].get('case_history'):
        analysis['recommendations'].append("Extract case history separately from citation verification")
    
    if analysis['components'].get('docket_numbers'):
        analysis['recommendations'].append("Use docket numbers for additional verification if available")
    
    return analysis

def test_citation_analysis():
    """Test the citation analysis with your specific example."""
    
    test_citation = """John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished)"""
    
    print("=== Complex Citation Analysis ===")
    print(f"Original Text: {test_citation}")
    print()
    
    analysis = analyze_complex_citation(test_citation)
    
    print("=== Components Found ===")
    for component_type, value in analysis['components'].items():
        print(f"{component_type}: {value}")
    
    print()
    print("=== Issues Identified ===")
    for issue in analysis['issues']:
        print(f"• {issue}")
    
    print()
    print("=== Recommendations ===")
    for rec in analysis['recommendations']:
        print(f"• {rec}")
    
    print()
    print("=== Why This Doesn't Generate Full Data ===")
    print("1. Your current system extracts individual citations (199 Wn. App. 280, 399 P.3d 1195)")
    print("2. Each citation is verified separately, losing the relationship between them")
    print("3. Case history markers (Doe I, Doe II) are not recognized as part of the citation")
    print("4. Docket numbers (No. 48000-0-II) are not verified by citation APIs")
    print("5. Unpublished cases may not be available in standard citation databases")
    print("6. The complex structure confuses the verification process")

if __name__ == "__main__":
    test_citation_analysis() 