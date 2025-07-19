#!/usr/bin/env python3
"""
Process one brief and generate a report showing ToA vs main body differences.
"""

import re
from src.toa_parser import ToAParser

def main():
    logger.info("=" * 60)
    logger.info("PROCESSING ONE BRIEF: ToA vs Main Body Comparison")
    logger.info("=" * 60)
    
    # Step 1: Read the brief
    logger.info("\n1. READING BRIEF FILE...")
    brief_file = "../wa_briefs_text/004_COA Respondent Brief.txt"
    try:
        with open(brief_file, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"   ✓ Successfully read {len(text):,} characters")
    except Exception as e:
        logger.error(f"   ✗ Error reading file: {e}")
        return
    
    # Step 2: Find ToA section
    logger.info("\n2. FINDING TABLE OF AUTHORITIES...")
    lines = text.splitlines()
    toa_start = None
    for i, line in enumerate(lines):
        if 'table of authorities' in line.lower():
            toa_start = i
            break
    
    if toa_start is None:
        logger.info("   ✗ No Table of Authorities found!")
        return
    
    logger.info(f"   ✓ Found ToA at line {toa_start}")
    
    # Step 3: Extract ToA section (next 100 lines)
    logger.info("\n3. EXTRACTING ToA SECTION...")
    toa_end = min(toa_start + 100, len(lines))
    toa_lines = lines[toa_start:toa_end]
    toa_section = '\n'.join(toa_lines)
    logger.info(f"   ✓ Extracted {len(toa_lines)} lines ({len(toa_section):,} characters)")
    
    # Step 4: Parse ToA entries
    logger.info("\n4. PARSING ToA ENTRIES...")
    toa_parser = ToAParser()
    toa_entries = toa_parser.parse_toa_section(toa_section)
    logger.info(f"   ✓ Parsed {len(toa_entries)} ToA entries")
    
    # Step 5: Show ToA results
    logger.info("\n5. ToA EXTRACTION RESULTS:")
    logger.info("-" * 40)
    
    toa_citations = []
    for i, entry in enumerate(toa_entries):
        case_name = entry.case_name or "No case name"
        year = entry.years[0] if entry.years else "No year"
        citations = entry.citations
        
        toa_citations.append({
            'case_name': case_name,
            'year': year,
            'citations': citations
        })
        
        if i < 10:  # Show first 10
            logger.info(f"{i+1:2d}. {case_name} ({year})")
            logger.info(f"     Citations: {citations}")
    
    if len(toa_entries) > 10:
        logger.info(f"     ... and {len(toa_entries) - 10} more entries")
    
    # Step 6: Simple main body extraction (just count citations)
    logger.info("\n6. ANALYZING MAIN BODY...")
    main_body = text.replace(toa_section, "")
    
    # Simple citation counting in main body
    citation_patterns = [
        r'\d+\s+Wn\.2d\s+\d+',  # 123 Wn.2d 456
        r'\d+\s+P\.\d+d\s+\d+',  # 123 P.3d 456
        r'\d+\s+Wn\.\s+App\.\s+\d+',  # 123 Wn. App. 456
    ]
    
    body_citations = []
    for pattern in citation_patterns:
        matches = re.findall(pattern, main_body)
        body_citations.extend(matches)
    
    logger.info(f"   ✓ Found {len(body_citations)} citation patterns in main body")
    
    # Step 7: Generate comparison report
    logger.info("\n" + "=" * 60)
    logger.info("FINAL REPORT")
    logger.info("=" * 60)
    
    logger.info(f"\nSUMMARY:")
    logger.info(f"• ToA entries found: {len(toa_entries)}")
    logger.info(f"• ToA entries with case names: {sum(1 for e in toa_entries if e.case_name)}")
    logger.info(f"• ToA entries with years: {sum(1 for e in toa_entries if e.years)}")
    logger.info(f"• Citation patterns in main body: {len(body_citations)}")
    
    logger.info(f"\nToA CASE NAMES (first 15):")
    logger.info("-" * 40)
    for i, entry in enumerate(toa_entries[:15]):
        case_name = entry.case_name or "No case name"
        year = entry.years[0] if entry.years else "No year"
        logger.info(f"{i+1:2d}. {case_name} ({year})")
    
    logger.info(f"\nMAIN BODY CITATION PATTERNS (first 15):")
    logger.info("-" * 40)
    for i, citation in enumerate(body_citations[:15]):
        logger.info(f"{i+1:2d}. {citation}")
    
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 