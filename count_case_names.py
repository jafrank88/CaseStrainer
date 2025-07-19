#!/usr/bin/env python3
"""
Count and analyze unique case names extracted from citations.
"""
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ToAParser
from src.extract_case_name import extract_case_name_unified

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
        enable_verification=False
    )
    
    processor = UnifiedCitationProcessorV2(config)
    result = processor.process_text(text)
    return result

def main():
    # Load the brief text
    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    
    if not os.path.exists(brief_file):
        print(f"Error: Brief file not found: {brief_file}")
        return
    
    print(f"Loading brief: {brief_file}")
    with open(brief_file, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"Full text length: {len(full_text):,} characters")
    
    # Parse ToA
    print("\nParsing Table of Authorities...")
    toa_parser = ToAParser()
    toa_bounds = toa_parser.detect_toa_section(full_text)
    
    if toa_bounds:
        start, end = toa_bounds
        toa_section = full_text[start:end]
        main_body = full_text[:start] + full_text[end:]
        print(f"ToA section: {len(toa_section):,} characters")
        print(f"Main body: {len(main_body):,} characters")
    else:
        print("No ToA section found")
        main_body = full_text
        toa_section = ""
    
    # Extract citations from both sections
    print("\nExtracting citations from main body...")
    main_body_citations = get_unified_citations(main_body)
    
    print("Extracting citations from ToA...")
    toa_citations = get_unified_citations(toa_section)
    
    # Debug: Print first few citation objects from main body
    print("\nFirst 3 main body citation objects:")
    for citation in main_body_citations[:3]:
        print(vars(citation))

    # Debug: Print first few citation objects from ToA
    print("\nFirst 3 ToA citation objects:")
    for citation in toa_citations[:3]:
        print(vars(citation))

    # Collect all case names
    all_case_names = set()
    case_names_with_counts = Counter()
    citations_without_case_names = 0
    
    print("\n=== CASE NAME ANALYSIS ===")
    
    # Helper to get the best available case name
    # Use the canonical extract_case_name_unified from src.extract_case_name

    def get_best_case_name(citation, text=None):
        # Prefer canonical_name if present
        name = getattr(citation, 'canonical_name', None)
        if name:
            return name.strip()
        # Next, try extracted_case_name
        name = getattr(citation, 'extracted_case_name', None)
        if name:
            return name.strip()
        # Next, try cluster_extracted_case_name in metadata
        meta = getattr(citation, 'metadata', {})
        if meta and isinstance(meta, dict):
            name = meta.get('cluster_extracted_case_name')
            if name:
                return name.strip()
        # As a last resort, use the canonical extraction function if text and citation are available
        if text and getattr(citation, 'citation', None):
            return extract_case_name_unified(text, citation.citation)
        return None

    # Process main body citations
    print(f"\nMain body citations: {len(main_body_citations)}")
    for citation in main_body_citations:
        case_name = get_best_case_name(citation, full_text)
        if case_name:
            all_case_names.add(case_name)
            case_names_with_counts[case_name] += 1
        else:
            citations_without_case_names += 1
    
    # Process ToA citations
    print(f"ToA citations: {len(toa_citations)}")
    for citation in toa_citations:
        case_name = get_best_case_name(citation, toa_section)
        if case_name:
            all_case_names.add(case_name)
            case_names_with_counts[case_name] += 1
        else:
            citations_without_case_names += 1

    print(f"\nTotal unique case names: {len(all_case_names)}")
    print(f"Citations without a case name: {citations_without_case_names}")
    print("\nMost common extracted case names:")
    for name, count in case_names_with_counts.most_common(20):
        print(f"  {name}: {count}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total unique case names: {len(all_case_names)}")
    print(f"Total citations without case names: {citations_without_case_names}")
    print(f"Total citations with case names: {sum(case_names_with_counts.values())}")
    
    # Show case names with their citation counts
    print(f"\n=== CASE NAMES WITH CITATION COUNTS ===")
    for case_name, count in sorted(case_names_with_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{count:3d} | {case_name}")
    
    # Save detailed results
    output_file = "case_names_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== CASE NAME ANALYSIS ===\n")
        f.write(f"Total unique case names: {len(all_case_names)}\n")
        f.write(f"Total citations without case names: {citations_without_case_names}\n")
        f.write(f"Total citations with case names: {sum(case_names_with_counts.values())}\n\n")
        
        f.write("=== CASE NAMES WITH CITATION COUNTS ===\n")
        for case_name, count in sorted(case_names_with_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{count:3d} | {case_name}\n")
        
        f.write(f"\n=== ALL UNIQUE CASE NAMES (alphabetical) ===\n")
        for case_name in sorted(all_case_names):
            f.write(f"{case_name}\n")
    
    print(f"\nDetailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main() 