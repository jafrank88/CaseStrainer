#!/usr/bin/env python3
"""
Analyze citations by their source (ToA vs main body) and identify duplicates.
"""
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter

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
        enable_verification=False
    )
    
    processor = UnifiedCitationProcessorV2(config)
    result = processor.process_text(text)
    return result

def main():
    # Load the brief text
    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    
    if not os.path.exists(brief_file):
        print(f"Error: {brief_file} not found")
        return
    
    with open(brief_file, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    print(f"Loaded brief: {len(full_text):,} characters")
    
    # Parse ToA
    print("\nParsing Table of Authorities...")
    toa_parser = ToAParser()
    toa_bounds = toa_parser.detect_toa_section(full_text)
    
    if toa_bounds:
        start, end = toa_bounds
        toa_section = full_text[start:end]
        print(f"ToA section found: {len(toa_section):,} characters")
        
        # Extract main body (everything except ToA)
        main_body = full_text[:start] + full_text[end:]
        print(f"Main body length: {len(main_body):,} characters")
    else:
        print("No ToA section found, using full text as main body")
        main_body = full_text
        toa_section = ""
    
    # Extract citations from each section
    print("\nExtracting citations from main body...")
    main_body_citations = get_unified_citations(main_body)
    
    print("Extracting citations from ToA...")
    toa_citations = get_unified_citations(toa_section)
    
    # Create normalized sets for each section
    main_body_normalized = set()
    toa_normalized = set()
    
    # Track citation details by source
    citation_details = {}
    
    # Process main body citations
    for citation in main_body_citations:
        normalized = citation.citation
        main_body_normalized.add(normalized)
        if normalized not in citation_details:
            citation_details[normalized] = {'main_body': [], 'toa': []}
        citation_details[normalized]['main_body'].append({
            'case_name': citation.extracted_case_name,
            'date': citation.extracted_date,
            'context': citation.context[:100] + "..." if len(citation.context) > 100 else citation.context
        })
    
    # Process ToA citations
    for citation in toa_citations:
        normalized = citation.citation
        toa_normalized.add(normalized)
        if normalized not in citation_details:
            citation_details[normalized] = {'main_body': [], 'toa': []}
        citation_details[normalized]['toa'].append({
            'case_name': citation.extracted_case_name,
            'date': citation.extracted_date,
            'context': citation.context[:100] + "..." if len(citation.context) > 100 else citation.context
        })
    
    # Analyze results
    all_citations = set(citation_details.keys())
    
    print(f"\n=== ANALYSIS RESULTS ===")
    print(f"Total unique citations: {len(all_citations)}")
    print(f"Citations found in main body only: {len(main_body_normalized - toa_normalized)}")
    print(f"Citations found in ToA only: {len(toa_normalized - main_body_normalized)}")
    print(f"Citations found in both: {len(main_body_normalized & toa_normalized)}")
    
    # Save detailed analysis
    output_file = "citation_source_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== CITATION SOURCE ANALYSIS ===\n")
        f.write(f"Total unique citations: {len(all_citations)}\n")
        f.write(f"Citations found in main body only: {len(main_body_normalized - toa_normalized)}\n")
        f.write(f"Citations found in ToA only: {len(toa_normalized - main_body_normalized)}\n")
        f.write(f"Citations found in both: {len(main_body_normalized & toa_normalized)}\n\n")
        
        # Sort citations for consistent output
        sorted_citations = sorted(all_citations)
        
        for i, citation in enumerate(sorted_citations):
            f.write(f"{i+1}. {citation}\n")
            
            details = citation_details[citation]
            
            if details['main_body']:
                f.write("   MAIN BODY:\n")
                for j, detail in enumerate(details['main_body']):
                    f.write(f"     {j+1}. Case: {detail['case_name'] or 'None'}\n")
                    f.write(f"        Date: {detail['date'] or 'None'}\n")
                    f.write(f"        Context: {detail['context']}\n")
            
            if details['toa']:
                f.write("   TOA:\n")
                for j, detail in enumerate(details['toa']):
                    f.write(f"     {j+1}. Case: {detail['case_name'] or 'None'}\n")
                    f.write(f"        Date: {detail['date'] or 'None'}\n")
                    f.write(f"        Context: {detail['context']}\n")
            
            # Mark duplicates
            if len(details['main_body']) > 0 and len(details['toa']) > 0:
                f.write("   *** DUPLICATE: Found in both sections ***\n")
            
            f.write("\n")
    
    print(f"\nDetailed analysis saved to: {output_file}")
    
    # Show some examples of duplicates
    print("\n=== EXAMPLES OF DUPLICATES (found in both sections) ===")
    duplicate_count = 0
    for citation in sorted_citations:
        details = citation_details[citation]
        if len(details['main_body']) > 0 and len(details['toa']) > 0:
            duplicate_count += 1
            if duplicate_count <= 5:  # Show first 5 duplicates
                print(f"{duplicate_count}. {citation}")
                print(f"   Main body: {len(details['main_body'])} instances")
                print(f"   ToA: {len(details['toa'])} instances")
                print()
    
    if duplicate_count > 5:
        print(f"... and {duplicate_count - 5} more duplicates")

if __name__ == "__main__":
    main() 