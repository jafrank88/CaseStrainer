#!/usr/bin/env python3
"""
Test script to find a brief with a proper Table of Authorities (ToA) 
and compare citation extraction results with and without the ToA.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
def get_unified_citations(text, logger=None):
    """Get citations using the new unified processor with eyecite."""
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        debug_mode=False
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(text)
    
    # Return just the citation strings for compatibility
    return [result.citation for result in results]



# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ToAParser
from document_processing_unified import extract_text_from_file
# Updated to use unified processor
from case_name_extraction_core import extract_case_name_triple_comprehensive

def find_brief_with_toa(briefs_dir: str = "wa_briefs") -> Optional[Tuple[str, str]]:
    """
    Find a brief that has a proper Table of Authorities section.
    
    Returns:
        Tuple of (brief_path, brief_name) if found, None otherwise
    """
    briefs_path = Path(briefs_dir)
    if not briefs_path.exists():
        print(f"Briefs directory {briefs_dir} not found")
        return None
    
    toa_parser = ToAParser()
    
    for pdf_file in briefs_path.glob("*.pdf"):
        print(f"Checking {pdf_file.name} for ToA...")
        
        try:
            # Extract text from PDF with error handling
            try:
                text = extract_text_from_file(str(pdf_file))
            except RecursionError:
                print(f"  Recursion error - skipping {pdf_file.name}")
                continue
            except Exception as e:
                print(f"  Error extracting text from {pdf_file.name}: {e}")
                continue
                
            if not text or len(text.strip()) < 1000:
                continue
            
            # Check for ToA section
            toa_section = toa_parser.detect_toa_section(text)
            if toa_section:
                start, end = toa_section
                toa_text = text[start:end]
                
                # Parse ToA entries
                entries = toa_parser.parse_toa_section(toa_text)
                
                if entries:
                    print(f"Found ToA in {pdf_file.name} with {len(entries)} entries")
                    print(f"Sample entries:")
                    for i, entry in enumerate(entries[:3]):
                        print(f"  {i+1}. {entry.case_name} - {entry.citations} - {entry.years}")
                    
                    return str(pdf_file), pdf_file.name
                else:
                    print(f"  ToA section found but no entries parsed")
            else:
                print(f"  No ToA section found")
                
        except Exception as e:
            print(f"  Error processing {pdf_file.name}: {e}")
            continue
    
    return None

def extract_citations_without_toa(text: str) -> List[Dict]:
    """
    Extract citations from text without using ToA information.
    """
    # Extract citations using the citation_utils function
    citations = get_unified_citations(text)
    
    # Convert to list of dicts for easier comparison
    extracted_citations = []
    for citation in citations:
        # Extract case name using the improved extraction
        case_name = extract_case_name_triple_comprehensive(text, citation)
        
        extracted_citations.append({
            'citation': citation,
            'case_name': case_name,
            'year': '',  # Will be extracted separately if needed
            'source': 'extraction_without_toa'
        })
    
    return extracted_citations

def extract_toa_citations(text: str) -> List[Dict]:
    """
    Extract citations from the Table of Authorities section.
    """
    toa_parser = ToAParser()
    toa_section = toa_parser.detect_toa_section(text)
    
    if not toa_section:
        return []
    
    start, end = toa_section
    toa_text = text[start:end]
    entries = toa_parser.parse_toa_section(toa_text)
    
    toa_citations = []
    for entry in entries:
        for citation in entry.citations:
            toa_citations.append({
                'citation': citation,
                'case_name': entry.case_name,
                'year': entry.years[0] if entry.years else '',
                'source': 'toa_parser'
            })
    
    return toa_citations

def compare_extractions(extracted_citations: List[Dict], toa_citations: List[Dict]) -> Dict:
    """
    Compare citations extracted without ToA vs ToA citations.
    """
    comparison = {
        'extracted_count': len(extracted_citations),
        'toa_count': len(toa_citations),
        'matches': [],
        'extracted_only': [],
        'toa_only': []
    }
    
    # Find matches by citation
    extracted_citations_set = {c['citation'] for c in extracted_citations}
    toa_citations_set = {c['citation'] for c in toa_citations}
    
    # Find matches
    matches = extracted_citations_set.intersection(toa_citations_set)
    for citation in matches:
        extracted = next(c for c in extracted_citations if c['citation'] == citation)
        toa = next(c for c in toa_citations if c['citation'] == citation)
        
        comparison['matches'].append({
            'citation': citation,
            'extracted': extracted,
            'toa': toa,
            'case_name_match': extracted['case_name'] == toa['case_name'],
            'year_match': extracted['year'] == toa['year']
        })
    
    # Find extracted only
    comparison['extracted_only'] = [
        c for c in extracted_citations 
        if c['citation'] not in toa_citations_set
    ]
    
    # Find ToA only
    comparison['toa_only'] = [
        c for c in toa_citations 
        if c['citation'] not in extracted_citations_set
    ]
    
    return comparison

def main():
    """Main function to test brief with ToA."""
    print("Searching for brief with Table of Authorities...")
    
    # Find a brief with ToA
    result = find_brief_with_toa()
    if not result:
        print("No brief with proper ToA found")
        return
    
    brief_path, brief_name = result
    print(f"\nTesting brief: {brief_name}")
    
    # Extract text from the brief
    text = extract_text_from_file(brief_path)
    if not text:
        print("Failed to extract text from brief")
        return
    
    print(f"Extracted {len(text)} characters of text")
    
    # Extract citations without using ToA
    print("\nExtracting citations without ToA...")
    extracted_citations = extract_citations_without_toa(text)
    print(f"Found {len(extracted_citations)} citations without ToA")
    
    # Extract citations from ToA
    print("\nExtracting citations from ToA...")
    toa_citations = extract_toa_citations(text)
    print(f"Found {len(toa_citations)} citations in ToA")
    
    # Compare the results
    print("\nComparing extractions...")
    comparison = compare_extractions(extracted_citations, toa_citations)
    
    # Print results
    print(f"\n=== COMPARISON RESULTS ===")
    print(f"Citations extracted without ToA: {comparison['extracted_count']}")
    print(f"Citations found in ToA: {comparison['toa_count']}")
    print(f"Matching citations: {len(comparison['matches'])}")
    print(f"Extracted only: {len(comparison['extracted_only'])}")
    print(f"ToA only: {len(comparison['toa_only'])}")
    
    if comparison['matches']:
        print(f"\n=== MATCHING CITATIONS ===")
        for i, match in enumerate(comparison['matches'][:5]):  # Show first 5
            print(f"{i+1}. {match['citation']}")
            print(f"   Extracted case name: {match['extracted']['case_name']}")
            print(f"   ToA case name: {match['toa']['case_name']}")
            print(f"   Case name match: {match['case_name_match']}")
            print(f"   Year match: {match['year_match']}")
            print()
    
    if comparison['extracted_only']:
        print(f"\n=== EXTRACTED ONLY (first 5) ===")
        for i, citation in enumerate(comparison['extracted_only'][:5]):
            print(f"{i+1}. {citation['citation']} - {citation['case_name']}")
    
    if comparison['toa_only']:
        print(f"\n=== TOA ONLY (first 5) ===")
        for i, citation in enumerate(comparison['toa_only'][:5]):
            print(f"{i+1}. {citation['citation']} - {citation['case_name']}")
    
    # Save detailed results
    results = {
        'brief_name': brief_name,
        'brief_path': brief_path,
        'comparison': comparison,
        'extracted_citations': extracted_citations,
        'toa_citations': toa_citations
    }
    
    output_file = f"toa_comparison_{brief_name.replace(' ', '_').replace('.pdf', '')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main() 