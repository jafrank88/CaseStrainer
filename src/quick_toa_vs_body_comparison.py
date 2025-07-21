#!/usr/bin/env python3
"""
Quick comparison of ToA vs main body extraction (no verification).
Uses reliable ToA parser for ToA sections and unified processor for main body.
Highlights differences in case names and years.
"""

# DEPRECATED: This file has been consolidated into src/toa_utils_consolidated.py
# Please use: from src.toa_utils_consolidated import quick_toa_vs_body_comparison, normalize_text, compare_citations
import warnings
warnings.warn(
    "quick_toa_vs_body_comparison.py is deprecated. Use toa_utils_consolidated.py instead.",
    DeprecationWarning,
    stacklevel=2
)

import os
import sys
import re
import logging
from collections import defaultdict
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.toa_parser import ToAParser
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def extract_toa_section(text: str) -> str:
    """Extract the Table of Authorities section from text."""
    lines = text.splitlines()
    start, end = None, None
    
    # Find ToA section start
    for i, line in enumerate(lines):
        if 'table of authorities' in line.lower():
            start = i
            break
    
    if start is None:
        return ""
    
    # Find ToA section end (next major section or blank line)
    for j in range(start + 1, len(lines)):
        line = lines[j].strip()
        if not line:  # Empty line
            continue
        if line.upper() in ['TABLE OF CONTENTS', 'ARGUMENT', 'CONCLUSION', 'CERTIFICATE']:
            end = j
            break
        # If we hit another section header, stop
        if re.match(r'^[A-Z\s]+$', line) and len(line) > 10:
            end = j
            break
    
    if end is None:
        end = len(lines)
    
    return '\n'.join(lines[start:end])

def normalize_text(text: str) -> str:
    """
    DEPRECATED: Use isolation-aware text normalization logic instead.
    Normalize text for comparison.
    """
    warnings.warn(
        "normalize_text is deprecated. Use isolation-aware text normalization instead.",
        DeprecationWarning,
        stacklevel=2
    )
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip().lower())

def compare_citations(toa_citations: List[Dict], body_citations: List[Dict]) -> Dict[str, Any]:
    """Compare ToA and body citations, highlighting differences."""
    results = {
        'matching': [],
        'toa_only': [],
        'body_only': [],
        'different_names': [],
        'different_years': []
    }
    
    # Create lookup dictionaries
    toa_lookup = {}
    for cit in toa_citations:
        key = normalize_text(cit.get('citation', ''))
        toa_lookup[key] = cit
    
    body_lookup = {}
    for cit in body_citations:
        key = normalize_text(cit.get('citation', ''))
        body_lookup[key] = cit
    
    # Find matches and differences
    all_citations = set(toa_lookup.keys()) | set(body_lookup.keys())
    
    for citation_key in all_citations:
        toa_cit = toa_lookup.get(citation_key)
        body_cit = body_lookup.get(citation_key)
        
        if toa_cit and body_cit:
            # Both have this citation - compare details
            toa_name = normalize_text(toa_cit.get('case_name', ''))
            body_name = normalize_text(body_cit.get('case_name', ''))
            toa_year = toa_cit.get('year', '')
            body_year = body_cit.get('year', '')
            
            if toa_name == body_name and toa_year == body_year:
                results['matching'].append({
                    'citation': citation_key,
                    'toa': toa_cit,
                    'body': body_cit
                })
            else:
                if toa_name != body_name:
                    results['different_names'].append({
                        'citation': citation_key,
                        'toa_name': toa_cit.get('case_name', ''),
                        'body_name': body_cit.get('case_name', ''),
                        'toa_year': toa_year,
                        'body_year': body_year
                    })
                if toa_year != body_year:
                    results['different_years'].append({
                        'citation': citation_key,
                        'toa_name': toa_cit.get('case_name', ''),
                        'body_name': body_cit.get('case_name', ''),
                        'toa_year': toa_year,
                        'body_year': body_year
                    })
        elif toa_cit:
            results['toa_only'].append(toa_cit)
        else:
            results['body_only'].append(body_cit)
    
    return results

def main():
    """Main comparison function."""
    brief_file = "../wa_briefs_text/004_COA Respondent Brief.txt"
    
    logger.info("Quick ToA vs Main Body Comparison (No Verification)")
    logger.info(f"Brief: {brief_file}")
    logger.info("=" * 80)
    
    logger.info("Step 1: Reading brief file...")
    # Read brief
    with open(brief_file, 'r', encoding='utf-8') as f:
        text = f.read()
    logger.info(f"   ✓ Read {len(text)} characters")
    
    logger.info("Step 2: Extracting ToA section...")
    # Extract ToA section
    toa_section = extract_toa_section(text)
    if not toa_section.strip():
        logger.info("   ✗ No ToA section found!")
        return
    logger.info(f"   ✓ ToA section extracted ({len(toa_section)} characters)")
    
    logger.info("Step 3: Removing ToA from main body...")
    # Remove ToA from main body
    main_body = text.replace(toa_section, "")
    logger.info(f"   ✓ Main body prepared ({len(main_body)} characters)")
    
    logger.info("Step 4: Parsing ToA using ToA parser...")
    # Parse ToA using ToA parser
    toa_parser = ToAParser()
    toa_entries = toa_parser.parse_toa_section(toa_section)
    logger.info(f"   ✓ Parsed {len(toa_entries)} ToA entries")
    
    # Convert ToA entries to comparable format
    toa_citations = []
    for entry in toa_entries:
        for citation in entry.citations:
            toa_citations.append({
                'citation': citation,
                'case_name': entry.case_name,
                'year': entry.years[0] if entry.years else None,
                'source': 'ToA'
            })
    logger.info(f"   ✓ Extracted {len(toa_citations)} ToA citations")
    
    logger.info("Step 5: Parsing main body using unified processor (no verification)...")
    # Parse main body using unified processor (without verification)
    from src.unified_citation_processor_v2 import ProcessingConfig
    config = ProcessingConfig(enable_verification=False)
    citation_processor = UnifiedCitationProcessorV2(config)
    
    body_results = citation_processor.process_text(main_body)
    
    # Convert body results to comparable format
    body_citations = []
    if body_results:
        for citation in body_results:
            case_name = getattr(citation, 'extracted_case_name', None)
            year = getattr(citation, 'extracted_date', None)
            body_citations.append({
                'citation': getattr(citation, 'citation', ''),
                'case_name': case_name,
                'year': year,
                'source': 'Main Body'
            })
    logger.info(f"   ✓ Extracted {len(body_citations)} main body citations")
    
    logger.info("Step 6: Comparing results...")
    # Compare results
    comparison = compare_citations(toa_citations, body_citations)
    logger.info("   ✓ Comparison complete")
    
    logger.info("=" * 80)
    logger.info("FINAL REPORT")
    logger.info("=" * 80)
    
    # Print results
    logger.info("SUMMARY:")
    logger.info(f"ToA citations: {len(toa_citations)}")
    logger.info(f"Main body citations: {len(body_citations)}")
    logger.info(f"Matching citations: {len(comparison['matching'])}")
    logger.info(f"ToA only: {len(comparison['toa_only'])}")
    logger.info(f"Main body only: {len(comparison['body_only'])}")
    logger.info(f"Different names: {len(comparison['different_names'])}")
    logger.info(f"Different years: {len(comparison['different_years'])}")
    
    # Show different names
    if comparison['different_names']:
        logger.info("CITATIONS WITH DIFFERENT CASE NAMES:")
        logger.info("-" * 60)
        for diff in comparison['different_names']:
            logger.info(f"Citation: {diff['citation']}")
            logger.info(f"  ToA:     {diff['toa_name']} ({diff['toa_year']})")
            logger.info(f"  Body:    {diff['body_name']} ({diff['body_year']})")
            logger.info("")
    
    # Show different years
    if comparison['different_years']:
        logger.info("CITATIONS WITH DIFFERENT YEARS:")
        logger.info("-" * 60)
        for diff in comparison['different_years']:
            logger.info(f"Citation: {diff['citation']}")
            logger.info(f"  ToA:     {diff['toa_name']} ({diff['toa_year']})")
            logger.info(f"  Body:    {diff['body_name']} ({diff['body_year']})")
            logger.info("")
    
    # Show ToA only citations
    if comparison['toa_only']:
        logger.info("CITATIONS ONLY IN ToA:")
        logger.info("-" * 60)
        for cit in comparison['toa_only'][:10]:  # Show first 10
            logger.info(f"  {cit['case_name']} ({cit['year']}) - {cit['citation']}")
        if len(comparison['toa_only']) > 10:
            logger.info(f"  ... and {len(comparison['toa_only']) - 10} more")
        logger.info("")
    
    # Show main body only citations
    if comparison['body_only']:
        logger.info("CITATIONS ONLY IN MAIN BODY:")
        logger.info("-" * 60)
        for cit in comparison['body_only'][:10]:  # Show first 10
            logger.info(f"  {cit['case_name']} ({cit['year']}) - {cit['citation']}")
        if len(comparison['body_only']) > 10:
            logger.info(f"  ... and {len(comparison['body_only']) - 10} more")
        logger.info("")
    
    logger.info("=" * 80)
    logger.info("COMPARISON COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main() 