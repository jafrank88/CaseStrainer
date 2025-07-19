#!/usr/bin/env python3
"""
Simple ToA vs main body extraction - just basic counts and examples.
"""

import re
from src.toa_parser import ToAParser

def extract_toa_section(text):
    """Simple ToA extraction."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if 'table of authorities' in line.lower():
            start = i
            break
    if start is None:
        return ""
    
    # Get next 50 lines as ToA section
    end = min(start + 50, len(lines))
    return '\n'.join(lines[start:end])

def main():
    brief_file = "../wa_briefs_text/004_COA Respondent Brief.txt"
    
    logger.info("Simple ToA vs Main Body Comparison")
    logger.info("=" * 50)
    
    logger.info("Reading brief...")
    with open(brief_file, 'r', encoding='utf-8') as f:
        text = f.read()
    logger.info(f"✓ Read {len(text)} characters")
    
    logger.info("\nExtracting ToA section...")
    toa_section = extract_toa_section(text)
    if not toa_section:
        logger.info("✗ No ToA section found!")
        return
    logger.info(f"✓ ToA section: {len(toa_section)} characters")
    
    logger.info("\nParsing ToA entries...")
    toa_parser = ToAParser()
    toa_entries = toa_parser.parse_toa_section(toa_section)
    logger.info(f"✓ Found {len(toa_entries)} ToA entries")
    
    logger.info("\nToA ENTRIES (first 5):")
    for i, entry in enumerate(toa_entries[:5]):
        logger.info(f"{i+1}. {entry.case_name} ({entry.years[0] if entry.years else 'No year'})")
        logger.info(f"   Citations: {entry.citations}")
    
    logger.info(f"\nSUMMARY:")
    logger.info(f"Total ToA entries: {len(toa_entries)}")
    logger.info(f"ToA entries with case names: {sum(1 for e in toa_entries if e.case_name)}")
    logger.info(f"ToA entries with years: {sum(1 for e in toa_entries if e.years)}")
    
    logger.info("\n✓ COMPARISON COMPLETE")

if __name__ == "__main__":
    main() 