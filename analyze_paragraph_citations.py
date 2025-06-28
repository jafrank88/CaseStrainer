#!/usr/bin/env python3
"""
Analyze citations in a paragraph to count total citations and parallel citations.
"""

import re
from typing import List, Tuple

def analyze_paragraph_citations(paragraph: str) -> Tuple[int, int, List[str]]:
    """
    Analyze a paragraph to count total citations and parallel citations.
    
    Returns:
        Tuple of (total_citations, parallel_citations, list_of_citations)
    """
    
    # Citation patterns for Washington and Pacific Reporter
    citation_patterns = [
        r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',  # Wn. App.
        r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',        # Wn.2d
        r'\b(\d+)\s+Wn\.3d\s+(\d+)\b',        # Wn.3d
        r'\b(\d+)\s+Wash\.\s+(\d+)\b',        # Wash.
        r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', # Wash. App.
        r'\b(\d+)\s+P\.3d\s+(\d+)\b',         # P.3d
        r'\b(\d+)\s+P\.2d\s+(\d+)\b',         # P.2d
    ]
    
    # Docket number pattern (can be citations for unpublished opinions)
    docket_pattern = r'No\.\s*([0-9\-]+)'
    
    all_citations = []
    
    # Find all citations in the paragraph
    for pattern in citation_patterns:
        matches = re.finditer(pattern, paragraph)
        for match in matches:
            volume, page = match.groups()
            full_citation = match.group(0)
            all_citations.append(full_citation)
    
    # Find docket numbers (which can be citations for unpublished opinions)
    docket_matches = re.finditer(docket_pattern, paragraph)
    for match in docket_matches:
        docket_num = match.group(1)
        full_docket = f"No. {docket_num}"
        all_citations.append(full_docket)
    
    # Remove duplicates while preserving order
    unique_citations = []
    for citation in all_citations:
        if citation not in unique_citations:
            unique_citations.append(citation)
    
    total_citations = len(unique_citations)
    
    # Count parallel citations (citations that appear together for the same case)
    # Look for patterns where multiple citations appear in sequence
    parallel_count = 0
    
    # Check if there are multiple citations in close proximity (within 50 characters)
    for i, citation1 in enumerate(unique_citations):
        for j, citation2 in enumerate(unique_citations):
            if i != j:
                # Find positions of both citations in the paragraph
                pos1 = paragraph.find(citation1)
                pos2 = paragraph.find(citation2)
                
                # If citations are close together (within 50 chars), they're likely parallel
                if abs(pos1 - pos2) <= 50:
                    parallel_count += 1
    
    # Divide by 2 since we're counting each pair twice
    parallel_count = parallel_count // 2
    
    return total_citations, parallel_count, unique_citations

def main():
    paragraph = """Zink filed her first appeal after the trial court granted summary judgment to 
the Does. While the appeal was pending, this court decided John Doe A v. 
Washington State Patrol, which rejected a PRA exemption claim for sex offender 
registration records that was materially identical to one of the Does' claims in this 
case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court 
of Appeals here reversed in part and held "that the registration records must be 
released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 
(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. 
App. Oct. 2, 2018) (Doe II) (unpublished),"""
    
    total, parallel, citations = analyze_paragraph_citations(paragraph)
    
    print(f"Paragraph Analysis:")
    print(f"Total citations found: {total}")
    print(f"Parallel citations: {parallel}")
    print(f"\nIndividual citations:")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. {citation}")
    
    print(f"\nDetailed breakdown:")
    print(f"- First case: John Doe A v. Washington State Patrol")
    print(f"  Citations: 185 Wn.2d 363, 374 P.3d 63 (2016)")
    print(f"  This is a parallel citation (Wn.2d and P.3d)")
    
    print(f"\n- Second case: John Doe P v. Thurston County")
    print(f"  Citations: 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)")
    print(f"  This includes: 199 Wn. App. 280 (primary), 283 (pinpoint), 399 P.3d 1195 (parallel)")
    print(f"  Plus: No. 48000-0-II (docket number citation for unpublished opinion)")
    
    print(f"\nNote: Docket numbers like 'No. 48000-0-II' can be citations for unpublished opinions,")
    print(f"as shown in the CaseMine case: https://www.casemine.com/judgement/us/5bbc56958f67d60a1bfef5f0")

if __name__ == "__main__":
    main() 