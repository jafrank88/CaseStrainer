#!/usr/bin/env python3
"""
Debug script to troubleshoot citation extraction from the main body of a brief.
"""
import os
import sys
from pathlib import Path
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
# Updated to use unified processor

BRIEF_TEXT_FILE = "wa_briefs_text/003_COA  Appellant Brief.txt"

def main():
    if not os.path.exists(BRIEF_TEXT_FILE):
        print(f"Text file {BRIEF_TEXT_FILE} not found")
        return

    with open(BRIEF_TEXT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Total text length: {len(text)} characters")
    
    # --- 1. Extract ToA section ---
    toa_parser = ToAParser()
    toa_section = toa_parser.detect_toa_section(text)
    if not toa_section:
        print("No ToA section detected.")
        return
    
    start, end = toa_section
    toa_text = text[start:end]
    body_text = text[:start] + text[end:]
    
    print(f"ToA section: {start} to {end} ({len(toa_text)} chars)")
    print(f"Body text: {len(body_text)} chars")
    
    # --- 2. Examine body text sample ---
    print(f"\nBody text preview (first 1000 chars):")
    print("=" * 80)
    print(body_text[:1000])
    print("=" * 80)
    
    # --- 3. Look for citation patterns in body text ---
    print(f"\nSearching for citation patterns in body text...")
    
    # Look for common citation patterns
    import re
    
    # Pattern 1: Volume Wn.2d Page (Year)
    pattern1 = r'\d+\s+Wn\.2d\s+\d+\s*\(\d{4}\)'
    matches1 = re.findall(pattern1, body_text)
    print(f"Pattern 1 (Wn.2d): {len(matches1)} matches")
    if matches1:
        print(f"  Examples: {matches1[:5]}")
    
    # Pattern 2: Volume Wn. App. Page (Year)
    pattern2 = r'\d+\s+Wn\.\s+App\.\s+\d+\s*\(\d{4}\)'
    matches2 = re.findall(pattern2, body_text)
    print(f"Pattern 2 (Wn. App.): {len(matches2)} matches")
    if matches2:
        print(f"  Examples: {matches2[:5]}")
    
    # Pattern 3: U.S. citations
    pattern3 = r'\d+\s+U\.S\.\s+\d+\s*\(\d{4}\)'
    matches3 = re.findall(pattern3, body_text)
    print(f"Pattern 3 (U.S.): {len(matches3)} matches")
    if matches3:
        print(f"  Examples: {matches3[:5]}")
    
    # Pattern 4: Any citation with year
    pattern4 = r'\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)'
    matches4 = re.findall(pattern4, body_text)
    print(f"Pattern 4 (Any with year): {len(matches4)} matches")
    if matches4:
        print(f"  Examples: {matches4[:5]}")
    
    # --- 4. Test citation extraction function ---
    print(f"\nTesting citation extraction function...")
    try:
        citations = get_unified_citations(body_text)
        print(f"extract_citations_from_text returned: {len(citations)} citations")
        if citations:
            print(f"  Examples: {citations[:5]}")
        else:
            print("  No citations found by extract_citations_from_text")
    except Exception as e:
        print(f"Error in extract_citations_from_text: {e}")
    
    # --- 5. Look for specific citations we know should be in the body ---
    print(f"\nLooking for specific citations from ToA in body text...")
    toa_entries = toa_parser.parse_toa_section(toa_text)
    toa_citations = set()
    for entry in toa_entries:
        for cit in entry.citations:
            toa_citations.add(cit)
    
    # Check if any ToA citations appear in body
    found_in_body = []
    for citation in list(toa_citations)[:10]:  # Check first 10
        if citation in body_text:
            found_in_body.append(citation)
    
    print(f"Citations from ToA found in body: {len(found_in_body)}")
    if found_in_body:
        print(f"  Examples: {found_in_body[:5]}")

if __name__ == "__main__":
    main() 