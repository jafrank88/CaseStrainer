#!/usr/bin/env python3
"""
Comprehensive test to compare citation extraction between ToA and non-ToA parts
using the unified processor with eyecite.
"""
import os
import sys
import re
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Optional, Tuple

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
        enable_verification=False  # Disable verification for faster processing
    )
    
    processor = UnifiedCitationProcessorV2(config)
    result = processor.process_text(text)
    return result

def normalize_citation(citation):
    """Normalize a citation for comparison by removing page numbers and standardizing format."""
    if hasattr(citation, 'volume') and hasattr(citation, 'reporter') and hasattr(citation, 'page'):
        return f"{citation.volume} {citation.reporter} {citation.page}"
    elif hasattr(citation, 'text'):
        # For text-based citations, try to extract volume and reporter
        text = citation.text.strip()
        # Remove common page number patterns
        text = re.sub(r',\s*\d+\s*$', '', text)  # Remove trailing page numbers
        text = re.sub(r'\(\d{4}\)', '', text)     # Remove years in parentheses
        return text.strip()
    else:
        return str(citation)

def analyze_citations(citations, source_name):
    """Analyze and display citation statistics."""
    print(f"\n=== {source_name} ANALYSIS ===")
    print(f"Total citations found: {len(citations)}")
    
    if not citations:
        print("No citations found.")
        return set()
    
    # Group by type
    citation_types = Counter()
    normalized_citations = set()
    
    for citation in citations:
        # Determine citation type
        if hasattr(citation, 'reporter'):
            citation_types[citation.reporter] += 1
        else:
            citation_types['unknown'] += 1
        
        # Normalize for comparison
        normalized = normalize_citation(citation)
        normalized_citations.add(normalized)
    
    print(f"Unique normalized citations: {len(normalized_citations)}")
    print(f"Citation types: {dict(citation_types)}")
    
    # Show first few examples
    print(f"\nFirst 5 citations from {source_name}:")
    for i, citation in enumerate(citations[:5]):
        if hasattr(citation, 'volume') and hasattr(citation, 'reporter') and hasattr(citation, 'page'):
            print(f"  {i+1}. {citation.volume} {citation.reporter} {citation.page}")
        else:
            print(f"  {i+1}. {citation}")
    
    return normalized_citations

def main():
    """Main comparison function."""
    brief_file = "wa_briefs_text/004_COA Respondent Brief.txt"
    
    if not os.path.exists(brief_file):
        print(f"Error: Brief file not found: {brief_file}")
        return
    
    print("Loading brief text...")
    with open(brief_file, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"Brief length: {len(full_text):,} characters")
    
    # Parse ToA
    print("\nParsing Table of Authorities...")
    toa_parser = ToAParser()
    toa_bounds = toa_parser.detect_toa_section(full_text)
    
    if toa_bounds:
        start, end = toa_bounds
        toa_section = full_text[start:end]
        print(f"ToA section found: {len(toa_section):,} characters")
        print(f"ToA starts at: {start}")
        print(f"ToA ends at: {end}")
        
        # Extract main body (everything except ToA)
        main_body = full_text[:start] + full_text[end:]
        print(f"Main body length: {len(main_body):,} characters")
    else:
        print("No ToA section found, using full text as main body")
        main_body = full_text
        toa_section = ""
    
    # Extract citations from both sections
    print("\nExtracting citations from main body...")
    main_body_citations = get_unified_citations(main_body)
    
    print("\nExtracting citations from ToA...")
    toa_citations = get_unified_citations(toa_section)
    
    # Analyze each section
    main_body_normalized = analyze_citations(main_body_citations, "MAIN BODY")
    toa_normalized = analyze_citations(toa_citations, "TABLE OF AUTHORITIES")
    
    # Compare results
    print("\n=== COMPARISON RESULTS ===")
    
    # Find overlaps and differences
    both_sections = main_body_normalized & toa_normalized
    only_main_body = main_body_normalized - toa_normalized
    only_toa = toa_normalized - main_body_normalized
    all_citations = main_body_normalized | toa_normalized
    
    print(f"Citations found in BOTH sections: {len(both_sections)}")
    print(f"Citations found ONLY in main body: {len(only_main_body)}")
    print(f"Citations found ONLY in ToA: {len(only_toa)}")
    print(f"Total unique citations in either section: {len(all_citations)}")
    
    # Show examples of each category
    if both_sections:
        print(f"\nExamples of citations found in BOTH sections:")
        for i, citation in enumerate(list(both_sections)[:5]):
            print(f"  {i+1}. {citation}")
    
    if only_main_body:
        print(f"\nExamples of citations found ONLY in main body:")
        for i, citation in enumerate(list(only_main_body)[:5]):
            print(f"  {i+1}. {citation}")
    
    if only_toa:
        print(f"\nExamples of citations found ONLY in ToA:")
        for i, citation in enumerate(list(only_toa)[:5]):
            print(f"  {i+1}. {citation}")
    
    # Print full list of all unique citations in either section
    print("\n=== FULL LIST OF ALL UNIQUE CITATIONS IN EITHER SECTION ===")
    for i, citation in enumerate(sorted(all_citations)):
        print(f"{i+1}. {citation}")
    
    # Save the list to a file for easy viewing
    output_file = "all_citations_list.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== FULL LIST OF ALL UNIQUE CITATIONS IN EITHER SECTION ===\n")
        f.write(f"Total unique citations: {len(all_citations)}\n\n")
        for i, citation in enumerate(sorted(all_citations)):
            f.write(f"{i+1}. {citation}\n")
    
    print(f"\nFull list saved to: {output_file}")

    # Print full list of citations found in BOTH for manual review
    print("\n=== FULL LIST: Citations found in BOTH sections (for manual review) ===")
    for citation in sorted(both_sections):
        print(citation)
    
    # Quality analysis
    print(f"\n=== QUALITY ANALYSIS ===")
    print(f"Main body extraction quality: {len(main_body_citations)} raw citations -> {len(main_body_normalized)} unique")
    print(f"ToA extraction quality: {len(toa_citations)} raw citations -> {len(toa_normalized)} unique")
    
    if len(main_body_citations) > 0:
        main_body_duplicate_rate = 1 - (len(main_body_normalized) / len(main_body_citations))
        print(f"Main body duplicate rate: {main_body_duplicate_rate:.1%}")
    
    if len(toa_citations) > 0:
        toa_duplicate_rate = 1 - (len(toa_normalized) / len(toa_citations))
        print(f"ToA duplicate rate: {toa_duplicate_rate:.1%}")

    # Build sets of (case_name, date) for ToA and main body
    def get_name_date_set(citations):
        s = set()
        for c in citations:
            name = getattr(c, 'canonical_name', None) or getattr(c, 'extracted_case_name', None)
            date = getattr(c, 'canonical_date', None) or getattr(c, 'extracted_date', None)
            if name and date:
                s.add((name.strip().lower(), str(date).strip()))
        return s

    toa_name_date = get_name_date_set(toa_citations)
    main_body_name_date = get_name_date_set(main_body_citations)

    # For each main body citation, check if its (name, date) is in ToA
    matches = 0
    total = 0
    for c in main_body_citations:
        name = getattr(c, 'canonical_name', None) or getattr(c, 'extracted_case_name', None)
        date = getattr(c, 'canonical_date', None) or getattr(c, 'extracted_date', None)
        if name and date:
            total += 1
            if (name.strip().lower(), str(date).strip()) in toa_name_date:
                matches += 1

    percent = (matches / total * 100) if total else 0
    print(f"\n=== PERCENTAGE OF MAIN BODY CITATIONS WITH MATCHING CASE NAME AND DATE IN TOA ===")
    print(f"{matches} out of {total} main body citations ({percent:.1f}%) have a matching case name and date in the ToA.")

    # --- BEGIN: Generate and save enhanced extracted name/date/cluster report ---
    # Parse ToA entries for accurate mapping
    toa_entries = ToAParser().parse_toa_section(toa_section)

    # Print first 10 parsed ToA entries for inspection
    print("\nFirst 10 parsed ToA entries:")
    for i, entry in enumerate(toa_entries[:10]):
        print(f"{i+1}. case_name: {getattr(entry, 'case_name', None)} | citations: {getattr(entry, 'citations', None)} | years: {getattr(entry, 'years', None)} | source_line: {getattr(entry, 'source_line', None)}")

    toa_citation_to_entry = {}
    toa_source_lines = {}  # Store original ToA lines
    for entry in toa_entries:
        for cit in entry.citations:
            toa_citation_to_entry[cit] = entry
            toa_source_lines[cit] = getattr(entry, 'source_line', '')

    # Helper to find ToA entry for a given citation (by text match or partial match)
    def find_toa_entry_for_citation(citation_text):
        # Try exact match first
        if citation_text in toa_citation_to_entry:
            return toa_citation_to_entry[citation_text]
        
        # Try partial match
        for toa_cit, entry in toa_citation_to_entry.items():
            if citation_text in toa_cit or toa_cit in citation_text:
                return entry
        
        return None

    def get_citation_report_rows(citations, section_label):
        rows = []
        for c in citations:
            # Prefer canonical, then extracted, then cluster metadata
            name = getattr(c, 'canonical_name', None) or getattr(c, 'extracted_case_name', None)
            date = getattr(c, 'canonical_date', None) or getattr(c, 'extracted_date', None)
            # Try cluster metadata if missing
            if not name and hasattr(c, 'metadata') and c.metadata:
                name = c.metadata.get('cluster_extracted_case_name', '')
            if not date and hasattr(c, 'metadata') and c.metadata:
                date = c.metadata.get('cluster_extracted_date', '')
            
            # Get cluster info
            cluster = getattr(c, 'cluster_id', None) or getattr(c, 'cluster', None)
            if cluster is None and hasattr(c, 'metadata') and c.metadata:
                cluster = c.metadata.get('cluster_id', '')
            
            # Get ToA info if this is a ToA citation
            toa_name = ''
            toa_year = ''
            toa_source_line = ''
            if section_label == 'ToA':
                toa_entry = find_toa_entry_for_citation(c.citation)
                if toa_entry:
                    toa_name = getattr(toa_entry, 'case_name', '')
                    toa_years = getattr(toa_entry, 'years', [])
                    toa_year = toa_years[0] if toa_years else ''
                    toa_source_line = toa_source_lines.get(c.citation, '')
            
            # Get context for main body citations
            context = ''
            if section_label == 'Main Body':
                # Try to get some context around the citation
                context = f"Context for {c.citation}"  # Placeholder for now
            
            rows.append({
                'section': section_label,
                'citation': c.citation,
                'toa_name': toa_name,
                'toa_year': toa_year,
                'toa_source_line': toa_source_line,
                'extracted_name': name or '',
                'extracted_date': date or '',
                'cluster': str(cluster) if cluster else '',
                'context': context
            })
        return rows

    # Generate report rows
    toa_rows = get_citation_report_rows(toa_citations, 'ToA')
    main_body_rows = get_citation_report_rows(main_body_citations, 'Main Body')
    all_rows = toa_rows + main_body_rows

    # Sort by date (try to convert to int, fallback to string sort)
    def date_key(row):
        try:
            date_str = str(row['extracted_date']).strip()
            if date_str and date_str != 'None':
                return int(date_str[:4])
            else:
                return 9999  # Put empty dates at the end
        except Exception:
            return 9999  # Put unparseable dates at the end
    all_rows_sorted = sorted(all_rows, key=date_key)

    # Print and save CSV
    header = ['Section', 'Citation', 'ToA Name', 'ToA Year', 'ToA Source Line', 'Extracted Name', 'Extracted Date', 'Cluster', 'Context']
    print('\n' + ' | '.join(header))
    print('-' * 200)
    for row in all_rows_sorted:
        print(' | '.join([row.get(h.lower().replace(' ', '_'), '') for h in header]))
    
    with open('citation_name_date_cluster_report.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in all_rows_sorted:
            writer.writerow({h: row.get(h.lower().replace(' ', '_'), '') for h in header})
    
    print("\nEnhanced report saved to: citation_name_date_cluster_report.csv")
    print(f"Total citations: {len(all_rows_sorted)}")
    print(f"ToA citations: {len(toa_rows)}")
    print(f"Main body citations: {len(main_body_rows)}")
    # --- END: Generate and save enhanced extracted name/date/cluster report ---

if __name__ == "__main__":
    main() 