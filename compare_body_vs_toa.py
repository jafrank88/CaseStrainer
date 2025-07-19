#!/usr/bin/env python3
"""
Compare citations extracted from the main body of a brief to those parsed from the Table of Authorities (ToA).
"""
import os
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ToAParser

def get_unified_citations(text, logger=None):
    """Get citations using the new unified processor with eyecite."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
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

BRIEF_TEXT_FILE = "wa_briefs_text/003_COA  Appellant Brief.txt"


def main():
    if not os.path.exists(BRIEF_TEXT_FILE):
        print(f"Text file {BRIEF_TEXT_FILE} not found")
        return

    with open(BRIEF_TEXT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    # --- 1. Extract ToA entries ---
    toa_parser = ToAParser()
    toa_section = toa_parser.detect_toa_section(text)
    if not toa_section:
        print("No ToA section detected.")
        return
    start, end = toa_section
    toa_text = text[start:end]
    body_text = text[:start] + text[end:]
    toa_entries = toa_parser.parse_toa_section(toa_text)
    toa_citations = set()
    toa_citation_map = defaultdict(list)
    for entry in toa_entries:
        for cit in entry.citations:
            toa_citations.add(cit)
            toa_citation_map[cit].append(entry)

    print(f"Parsed {len(toa_entries)} ToA entries, {len(toa_citations)} unique citations.")

    # --- 2. Extract citations from main body (excluding ToA) ---
    body_citations = set(get_unified_citations(body_text))
    print(f"Extracted {len(body_citations)} unique citations from main body.")

    # --- 3. Compare ---
    in_both = body_citations & toa_citations
    only_in_body = body_citations - toa_citations
    only_in_toa = toa_citations - body_citations

    print(f"\nCitations found in BOTH body and ToA: {len(in_both)}")
    for cit in sorted(in_both):
        print(f"  {cit}")

    print(f"\nCitations ONLY in main body: {len(only_in_body)}")
    for cit in sorted(only_in_body):
        print(f"  {cit}")

    print(f"\nCitations ONLY in ToA: {len(only_in_toa)}")
    for cit in sorted(only_in_toa):
        print(f"  {cit}")

    # Optionally, compare years/case names for matches
    # (not shown here, but can be added if desired)

if __name__ == "__main__":
    main() 