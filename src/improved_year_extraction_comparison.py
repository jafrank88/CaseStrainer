#!/usr/bin/env python3
"""
Improved year extraction comparison for ToA vs main body.
Focuses specifically on extracting years from citations in the body text.
"""

import re
import time
import psutil
import os
import json
import logging
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Import case name extraction functions
try:
    from src.case_name_extraction_core import extract_case_name_from_text, is_valid_case_name, clean_case_name_enhanced
except ImportError:
    # Fallback if the module is not available
    def extract_case_name_from_text(text, citation_text):
        return  
    def is_valid_case_name(case_name):
        return bool(case_name and len(case_name) > 3)
    
    def clean_case_name_enhanced(case_name):
        return case_name.strip() if case_name else ""

def log_memory_usage(stage=""):
    """Log current memory usage."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"[MEMORY] {stage}: {memory_mb:.2f} MB")

def log_timing(start_time, stage=""):
    """Log elapsed time for a stage."""
    elapsed = time.time() - start_time
    logger.info(f"[TIMING] {stage}: {elapsed:.2f} seconds")

def extract_toa_section(text: str) -> str:
    """Extract the Table of Authorities section from text using character positions."""
    # Find the start of TABLE OF AUTHORITIES
    toa_start = text.find('TABLE OF AUTHORITIES')
    if toa_start == -1:
        toa_start = text.find('Table of Authorities')
    
    if toa_start == -1:
        logger.warning("[WARNING] Could not find TABLE OF AUTHORITIES section")
        return ""
    
    logger.debug(f"[DEBUG] Found TABLE OF AUTHORITIES at position {toa_start}")
    
    # Find the end by looking for the next major section header
    # Look for common section headers that come after ToA
    end_markers = [
        'I.ASSIGNMENT OF ERRORS',
        'II.STATEMENT OF FACTS', 
        'III.ARGUMENT',
        'ARGUMENT',
        'CONCLUSION',
        'CERTIFICATE'
    ]
    
    toa_end = len(text)  # Default to end of text
    for marker in end_markers:
        pos = text.find(marker, toa_start + 100)  # Start searching after ToA header
        if pos != -1 and pos < toa_end:
            toa_end = pos
            logger.debug(f"[DEBUG] Found end marker '{marker}' at position {pos}")
    
    toa_section = text[toa_start:toa_end]
    logger.debug(f"[DEBUG] ToA section: {toa_start} to {toa_end} ({len(toa_section)} characters)")
    
    return toa_section

def extract_case_name_from_body_text(text: str, citation: str, citation_start: int) -> Optional[str]:
    """
    Extract case name from body text before a citation using context and existing extraction logic.
    """
    try:
        # Get context before the citation (up to 300 characters)
        context_start = max(0, citation_start - 300)
        context_before = text[context_start:citation_start]

        # Use the existing case name extraction function
        case_name = extract_case_name_from_text(context_before, citation)

        if case_name and is_valid_case_name(case_name):
            # Clean the case name
            cleaned_name = clean_case_name_enhanced(case_name)
            if cleaned_name and is_valid_case_name(cleaned_name):
                return cleaned_name
        return None
    except Exception as e:
        logger.error(f"[WARNING] Error extracting case name for citation '{citation}': {e}")
        return None

def extract_citations_with_years_from_body(text: str) -> List[Dict[str, Any]]:
    """
    Extract citations with years from the main body text using improved patterns.
    Only match complete citations (volume, reporter, page).
    Handles years in parentheses at the end and years between case name and citation.
    Splits citations with procedural phrases into separate entries.
    """
    citations = []
    
    # Procedural phrases that indicate separate citation stages
    procedural_phrases = [
        r'review denied',
        r'review granted',
        r'relief denied',
        r'affirmed',
        r'reversed',
        r'remanded',
        r'cert\. denied',
        r'cert. granted',
        r'petition denied',
        r'petition granted',
        r'writ denied',
        r'writ granted',
        r'motion denied',
        r'motion granted',
        r'appeal denied',
        r'appeal granted',
    ]
    # Improved citation patterns for complete citations only
    # Handle both: "194 Wn.2d 784 (2020)" and "State v. Smith, 2020, 194 Wn.2d 784"
    citation_patterns = [
        # Washington Supreme Court: 194 Wn.2d 784 (2019) or State v. Smith, 2019, 194 Wn.2d 784
        r'(\d+\s+Wn\.2d\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+Wn\.2d\s+\d+)',
        
        # Washington Court of Appeals: 153 Wn. App. 197 (2009) or State v. Smith, 2009, 153 Wn. App. 197
        r'(\d+\s+Wn\.\s*App\.\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+Wn\.\s*App\.\s+\d+)',
        
        # Pacific Reporter: 453 P.3d 696 (2019) or State v. Smith, 2019, 453 P.3d 696
        r'(\d+\s+P\.\d+[d]?\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+P\.\d+[d]?\s+\d+)',
        
        # U.S. Supreme Court: 392 U.S. 1 (1968) or State v. Smith, 1968, 392 U.S. 1
        r'(\d+\s+U\.S\.\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+U\.S\.\s+\d+)',
        
        # Supreme Court Reporter: 87 S.Ct. 824 (1967) or State v. Smith, 1967, 87 S.Ct. 824
        r'(\d+\s+S\.Ct\.\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+S\.Ct\.\s+\d+)',
        
        # Lawyers Edition: 17 L.Ed. 2d 705 (1967) or State v. Smith, 1967, 17 L.Ed. 2d 705
        r'(\d+\s+L\.Ed\.(?:\s*2d)?\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+L\.Ed\.(?:\s*2d)?\s+\d+)',
        
        # Federal Reporter: 123 F.3d 456 (1997) or State v. Smith, 1997, 123 F.3d 456
        r'(\d+\s+F\.\d+[d]?\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+F\.\d+[d]?\s+\d+)',
        
        # Federal Supplement: 123 F.Supp. 456 (1997) or State v. Smith, 1997, 123 F.Supp. 456
        r'(\d+\s+F\.Supp\.?\s+\d+(?:\s*\(\d{4}\))?)',
        r'(?:[^,]+,\s*)?(\d{4}),\s*(\d+\s+F\.Supp\.?\s+\d+)',
    ]
    
    # Year extraction patterns
    year_patterns = [
        r'\((\d{4})\)',  # Year in parentheses
        r',\s*(\d{4})\s*(?=[A-Z]|$)',  # Year after comma
        r'\b(\d{4})\b',  # Any 4-digit year
    ]
    
    def validate_year(year_str: str) -> bool:
        try:
            year = int(year_str)
            return 1800 <= year <= 2030
        except (ValueError, TypeError):
            return False
    
    def extract_year_from_context(text: str, citation_start: int, citation_end: int) -> Optional[str]:
        # Only look for year in text after the citation, not before
        context_start = citation_end  # Start from the end of the citation
        context_end = min(len(text), citation_end + 100)  # Look ahead 100 characters
        context = text[context_start:context_end]
        
        # Try to find year in parentheses first (most reliable)
        year_match = re.search(r'\((\d{4})\)', context)
        if year_match:
            year = year_match.group(1)
            if validate_year(year):
                return year
        
        # Try other patterns in the context after the citation
        for pattern in year_patterns:
            matches = re.findall(pattern, context)
            for match in matches:
                if validate_year(match):
                    return match
        
        return None
    
    def extract_procedural_citations(text: str, base_citation: str, base_year: str, start_pos: int, end_pos: int) -> List[Dict[str, Any]]:
        """Extract additional citations from procedural phrases in the same context."""
        procedural_citations = []
        
        # Look in the context after the base citation for procedural phrases
        context_start = end_pos
        context_end = min(len(text), end_pos + 200)  # Look ahead 200 characters
        context = text[context_start:context_end]
        
        for phrase_pattern in procedural_phrases:
            phrase_match = re.search(phrase_pattern, context, re.IGNORECASE)
            if phrase_match:
                # Look for a year near this procedural phrase
                phrase_start = context_start + phrase_match.start()
                phrase_end = context_start + phrase_match.end()
                
                # Look for year in parentheses near the procedural phrase
                year_context_start = max(phrase_start - 50, phrase_end)
                year_context_end = min(len(text), phrase_end + 50)
                year_context = text[year_context_start:year_context_end]
                
                year_match = re.search(r'\((\d{4})\)', year_context)
                if year_match:
                    proc_year = year_match.group(1)
                    if validate_year(proc_year) and proc_year != base_year:
                        # Create a new citation entry for the procedural stage
                        procedural_citations.append({
                            'citation': f"{base_citation} ({phrase_match.group(0)})",
                            'year': proc_year,
                            'start_pos': phrase_start,
                            'end_pos': phrase_end,
                            'source': 'Body (Procedural)',
                            'procedural_phrase': phrase_match.group(0)
                        })
        
        return procedural_citations
    
    for pattern in citation_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            
            # Handle different pattern types
            if len(groups) == 1:
                # Standard pattern: citation with optional year in parentheses
                citation_text = groups[0]
                citation_start = match.start()
                citation_end = match.end()
                year = None
                
                # Check if year is in parentheses in the citation
                if '(' in citation_text and ')' in citation_text:
                    year_match = re.search(r'\((\d{4})\)', citation_text)
                    if year_match:
                        year = year_match.group(1)
                
                # If no year in parentheses, look in context after citation
                if not year:
                    year = extract_year_from_context(text, citation_start, citation_end)
                    
            elif len(groups) == 2:
                # Pattern with year between case name and citation: "State v. Smith, 2020, 194 Wn.2d 784"
                year = groups[0]
                citation_text = groups[1]
                citation_start = match.start()
                citation_end = match.end()
                
                # Validate the year
                if not validate_year(year):
                    year = None
                    year = extract_year_from_context(text, citation_start, citation_end)
            else:
                continue
            
            if year and validate_year(year):
                # Extract case name from body text before the citation
                case_name = extract_case_name_from_body_text(text, citation_text, citation_start)
                # Add the base citation
                citations.append({
                    'citation': citation_text,
                    'year': year,
                    'start_pos': citation_start,
                    'end_pos': citation_end,
                    'source': 'Body',
                    'case_name': case_name
                })
                # Look for procedural citations with the same case name
                procedural_citations = extract_procedural_citations(text, citation_text, year, citation_start, citation_end)
                citations.extend(procedural_citations)
    
    unique_citations = {}
    for cit in citations:
        key = cit['citation'].lower().strip()
        if key not in unique_citations:
            unique_citations[key] = cit
        else:
            if cit['year'] and not unique_citations[key]['year']:
                unique_citations[key] = cit
    
    return list(unique_citations.values())

def extract_toa_citations_with_years(text: str) -> List[Dict[str, Any]]:
    """Extract citations with years from ToA section."""
    try:
        from src.toa_parser import ImprovedToAParser
        toa_parser = ImprovedToAParser()
        toa_entries = toa_parser.parse_toa_section(text)
        
        citations = []
        for entry in toa_entries:
            for citation in entry.citations:
                year = entry.years[0] if entry.years else None
                citations.append({
                    'citation': citation,
                    'year': year,
                    'case_name': entry.case_name,
                    'source': 'ToA'
                })
        
        return citations
    except Exception as e:
        logger.error(f"[ERROR] Failed to parse ToA: {e}")
        return []

def compare_year_extraction(toa_citations: List[Dict], body_citations: List[Dict]) -> Dict[str, Any]:
    """Compare year extraction between ToA and body citations."""
    results = {
        'toa_citations': len(toa_citations),
        'body_citations': len(body_citations),
        'toa_with_years': len([c for c in toa_citations if c.get('year')]),
        'body_with_years': len([c for c in body_citations if c.get('year')]),
        'matching_citations': [],
        'toa_only': [],
        'body_only': [],
        'different_years': [],
        'different_case_names': [],  # Add case name differences
        'year_distribution': Counter(),
        'extraction_analysis': {}
    }
    
    # Create lookup dictionaries
    toa_lookup = {}
    for cit in toa_citations:
        key = cit['citation'].lower().strip()
        toa_lookup[key] = cit
    
    body_lookup = {}
    for cit in body_citations:
        key = cit['citation'].lower().strip()
        body_lookup[key] = cit
    
    # Find matches and differences
    all_citations = set(toa_lookup.keys()) | set(body_lookup.keys())
    
    for citation_key in all_citations:
        toa_cit = toa_lookup.get(citation_key)
        body_cit = body_lookup.get(citation_key)
        
        if toa_cit and body_cit:
            # Both have this citation - compare details
            toa_name = toa_cit.get('case_name')
            body_name = body_cit.get('case_name')
            toa_year = toa_cit.get('year')
            body_year = body_cit.get('year')
            
            if toa_name == body_name and toa_year == body_year:
                results['matching_citations'].append({
                    'citation': citation_key,
                    'toa': toa_cit,
                    'body': body_cit
                })
            else:
                if toa_name != body_name:
                    results['different_case_names'].append({
                        'citation': citation_key,
                        'toa_name': toa_name,
                        'body_name': body_name,
                        'toa_year': toa_year,
                        'body_year': body_year,
                        'toa': toa_cit,
                        'body': body_cit
                    })
                if toa_year != body_year:
                    results['different_years'].append({
                        'citation': citation_key,
                        'toa_name': toa_name,
                        'body_name': body_name,
                        'toa_year': toa_year,
                        'body_year': body_year,
                        'toa': toa_cit,
                        'body': body_cit
                    })
        elif toa_cit:
            results['toa_only'].append(toa_cit)
        else:
            results['body_only'].append(body_cit)
    
    # Analyze year distribution
    for cit in toa_citations + body_citations:
        if cit.get('year'):
            results['year_distribution'][cit['year']] += 1
    
    # Analyze extraction success rates
    results['extraction_analysis'] = {
        'toa_year_rate': results['toa_with_years'] / len(toa_citations) if toa_citations else 0,
        'body_year_rate': results['body_with_years'] / len(body_citations) if body_citations else 0,
        'total_citations': len(all_citations),
        'citations_with_years': results['toa_with_years'] + results['body_with_years']
    }
    
    return results

def process_document(file_path: str) -> dict:
    """Process a single legal brief and return structured extraction/comparison results."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        return {'document': file_path, 'error': f'Failed to read: {e}'}

    toa_section = extract_toa_section(text)
    toa_citations = extract_toa_citations_with_years(toa_section)
    body_citations = extract_citations_with_years_from_body(text)
    comparison = compare_year_extraction(toa_citations, body_citations)
    result = {
        'document': file_path,
        'toa_citations': toa_citations,
        'body_citations': body_citations,
        'comparison': comparison
    }
    return result

def process_batch(file_paths: List[str]) -> List[dict]:
    """Process a batch of legal briefs and return a list of results."""
    results = []
    for file_path in file_paths:
        result = process_document(file_path)
        results.append(result)
    return results

def log_mismatches_to_jsonl(batch_results: List[dict], output_path: str):
    """Write mismatches (case name/year) to a JSONL file for review and ML."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in batch_results:
            doc = result['document']
            comparison = result.get('comparison', {})
            toa_citations = {c['citation'].lower().strip(): c for c in result.get('toa_citations', [])}
            body_citations = {c['citation'].lower().strip(): c for c in result.get('body_citations', [])}
            # Year mismatches
            for diff in comparison.get('different_years', []):
                citation = diff['citation']
                entry = {
                    'document': doc,
                    'citation': citation,
                    'toa_case_name': diff.get('toa_name'),
                    'toa_year': diff.get('toa_year'),
                    'body_case_name': diff.get('body_name'),
                    'body_year': diff.get('body_year'),
                    'error_type': 'year_mismatch',
                    'toa_context': None,
                    'body_context': None
                }
                # Add context if available
                toa_cit = toa_citations.get(citation)
                body_cit = body_citations.get(citation)
                if toa_cit:
                    entry['toa_context'] = f"...{toa_cit.get('citation', '')}..."
                if body_cit:
                    entry['body_context'] = f"...{body_cit.get('citation', '')}..."
                f.write(json.dumps(entry) + '\n')
            # Case name mismatches
            for diff in comparison.get('different_case_names', []):
                citation = diff['citation']
                entry = {
                    'document': doc,
                    'citation': citation,
                    'toa_case_name': diff.get('toa_name'),
                    'toa_year': diff.get('toa_year'),
                    'body_case_name': diff.get('body_name'),
                    'body_year': diff.get('body_year'),
                    'error_type': 'case_name_mismatch',
                    'toa_context': None,
                    'body_context': None
                }
                toa_cit = toa_citations.get(citation)
                body_cit = body_citations.get(citation)
                if toa_cit:
                    entry['toa_context'] = f"...{toa_cit.get('citation', '')}..."
                if body_cit:
                    entry['body_context'] = f"...{body_cit.get('citation', '')}..."
                f.write(json.dumps(entry) + '\n')

def main():
    """Main comparison function."""
    script_start_time = time.time()
    logger.info("=== IMPROVED YEAR EXTRACTION COMPARISON ===")
    log_memory_usage("Script start")

    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    logger.info(f"[STATUS] Using brief file: {brief_file}")

    # Use the new process_document function
    result = process_document(brief_file)
    if 'error' in result:
        logger.error(f"[ERROR] {result['error']}")
        return
    toa_citations = result['toa_citations']
    body_citations = result['body_citations']
    comparison = result['comparison']

    logger.info(f"\nToA citations: {len(toa_citations)}")
    logger.info(f"Body citations: {len(body_citations)}")
    logger.info(f"Matching citations: {len(comparison['matching_citations'])}")
    logger.info(f"ToA only: {len(comparison['toa_only'])}")
    logger.info(f"Body only: {len(comparison['body_only'])}")
    logger.info(f"Different years: {len(comparison['different_years'])}")
    logger.info(f"Different case names: {len(comparison['different_case_names'])}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        logger.error('=== EXCEPTION OCCURRED ===')
        logger.info(e)
        traceback.print_exc() 