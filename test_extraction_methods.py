#!/usr/bin/env python3
"""
Compare citation extraction results between different methods:
1. Old regex-only method from citation_utils.py
2. New unified processor with eyecite
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

# Updated to use unified processor

# Import with absolute path to avoid relative import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

BRIEF_TEXT_FILE = "wa_briefs_text/003_COA  Appellant Brief.txt"

def test_old_regex_method(text):
    """Test the old regex-only method from citation_utils.py"""
    print("=== Testing OLD regex-only method ===")
    citations = get_unified_citations(text)
    print(f"Found {len(citations)} citations using old regex method")
    for i, citation in enumerate(citations[:10]):  # Show first 10
        print(f"  {i+1}. {citation}")
    if len(citations) > 10:
        print(f"  ... and {len(citations) - 10} more")
    return set(citations)

def test_new_unified_method(text):
    """Test the new unified processor with eyecite"""
    print("\n=== Testing NEW unified processor with eyecite ===")
    
    # Configure processor
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(text)
    
    # Extract citation strings
    citations = [result.citation for result in results]
    print(f"Found {len(citations)} citations using new unified method")
    
    # Show first 10 with method info
    for i, result in enumerate(results[:10]):
        method = result.method
        print(f"  {i+1}. {result.citation} (method: {method})")
    if len(results) > 10:
        print(f"  ... and {len(results) - 10} more")
    
    return set(citations)

def test_new_regex_only(text):
    """Test the new unified processor with regex only (no eyecite)"""
    print("\n=== Testing NEW unified processor with regex only ===")
    
    # Configure processor
    config = ProcessingConfig(
        use_eyecite=False,  # Disable eyecite
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(text)
    
    # Extract citation strings
    citations = [result.citation for result in results]
    print(f"Found {len(citations)} citations using new regex-only method")
    
    # Show first 10 with method info
    for i, result in enumerate(results[:10]):
        method = result.method
        print(f"  {i+1}. {result.citation} (method: {method})")
    if len(results) > 10:
        print(f"  ... and {len(results) - 10} more")
    
    return set(citations)

def main():
    if not os.path.exists(BRIEF_TEXT_FILE):
        print(f"Text file {BRIEF_TEXT_FILE} not found")
        return

    with open(BRIEF_TEXT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Testing with brief: {BRIEF_TEXT_FILE}")
    print(f"Text length: {len(text)} characters")
    
    # Test all methods
    old_regex_citations = test_old_regex_method(text)
    new_unified_citations = test_new_unified_method(text)
    new_regex_only_citations = test_new_regex_only(text)
    
    # Compare results
    print("\n=== COMPARISON RESULTS ===")
    
    # Old regex vs New unified
    only_in_old = old_regex_citations - new_unified_citations
    only_in_new = new_unified_citations - old_regex_citations
    in_both = old_regex_citations & new_unified_citations
    
    print(f"Citations in BOTH old regex and new unified: {len(in_both)}")
    print(f"Citations ONLY in old regex: {len(only_in_old)}")
    print(f"Citations ONLY in new unified: {len(only_in_new)}")
    
    if only_in_old:
        print("\nCitations found by old regex but NOT by new unified:")
        for citation in sorted(only_in_old):
            print(f"  {citation}")
    
    if only_in_new:
        print("\nCitations found by new unified but NOT by old regex:")
        for citation in sorted(only_in_new):
            print(f"  {citation}")
    
    # New regex-only vs New unified (to see eyecite contribution)
    print(f"\n=== EYECITE CONTRIBUTION ===")
    only_regex = new_regex_only_citations - new_unified_citations
    only_unified = new_unified_citations - new_regex_only_citations
    in_both_new = new_regex_only_citations & new_unified_citations
    
    print(f"Citations in BOTH new regex-only and new unified: {len(in_both_new)}")
    print(f"Citations ONLY in new regex-only: {len(only_regex)}")
    print(f"Citations ONLY in new unified (eyecite contribution): {len(only_unified)}")
    
    if only_unified:
        print("\nCitations found by eyecite but NOT by regex:")
        for citation in sorted(only_unified):
            print(f"  {citation}")

if __name__ == "__main__":
    main() 