#!/usr/bin/env python3
"""
Comprehensive comparison of ToA vs main body extraction.
Uses reliable ToA parser for ToA sections and unified processor for main body.
Highlights differences in case names and years.
"""

import re
import time
import psutil
import os
import logging
from collections import defaultdict
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add dependency checking at the top
def check_dependencies():
    """Check if required modules and files exist."""
    logger.info("=== DEPENDENCY CHECK ===")
    
    # Check for required Python modules
    missing_modules = []
    try:
        from toa_parser import ToAParser
        logger.info("✓ ToAParser module found")
    except ImportError as e:
        logger.info(f"✗ ToAParser module missing: {e}")
        missing_modules.append("toa_parser")
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        logger.info("✓ UnifiedCitationProcessorV2 module found")
    except ImportError as e:
        logger.info(f"✗ UnifiedCitationProcessorV2 module missing: {e}")
        missing_modules.append("unified_citation_processor_v2")
    
    # Check for required files
    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    if os.path.exists(brief_file):
        file_size = os.path.getsize(brief_file) / (1024 * 1024)  # MB
        logger.info(f"✓ Brief file found: {brief_file} ({file_size:.2f} MB)")
    else:
        logger.info(f"✗ Brief file missing: {brief_file}")
        missing_modules.append("brief_file")
    
    if missing_modules:
        logger.error(f"\n[ERROR] Missing dependencies: {missing_modules}")
        return False
    
    logger.info("✓ All dependencies found")
    return True

def log_memory_usage(stage=""):
    """Log current memory usage."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"[MEMORY] {stage}: {memory_mb:.2f} MB")

def log_timing(start_time, stage=""):
    """Log elapsed time for a stage."""
    elapsed = time.time() - start_time
    logger.info(f"[TIMING] {stage}: {elapsed:.2f} seconds")

logger.info('=== SCRIPT STARTED ===')

logger.info('--- IMPORT TEST START ---')
try:
    from toa_parser import ToAParser
    logger.info('Imported ToAParser successfully')
except Exception as e:
    logger.error(f'Failed to import ToAParser: {e}')
try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2
    logger.info('Imported UnifiedCitationProcessorV2 successfully')
except Exception as e:
    logger.error(f'Failed to import UnifiedCitationProcessorV2: {e}')
logger.info('--- IMPORT TEST END ---')

def extract_toa_section(text: str) -> str:
    """Extract the Table of Authorities section from text, stopping at the first major section header."""
    lines = text.splitlines()
    start, end = None, None
    major_headers = [
        'TABLE OF CONTENTS', 'ARGUMENT', 'CONCLUSION', 'CERTIFICATE',
        'STATEMENT OF THE CASE', 'ISSUES PRESENTED', 'STATEMENT OF FACTS',
        'SUMMARY OF ARGUMENT', 'JURISDICTIONAL STATEMENT', 'PRELIMINARY STATEMENT',
        'STATEMENT OF THE ISSUE', 'STATEMENT OF ISSUES', 'STATEMENT OF GROUNDS',
        'PROCEDURAL HISTORY', 'BACKGROUND', 'INTRODUCTION', 'DISCUSSION',
        'ASSIGNMENTS OF ERROR', 'ASSIGNMENT OF ERROR', 'RESPONSE', 'REPLY'
    ]
    # Find ToA section start
    for i, line in enumerate(lines):
        if 'table of authorities' in line.lower() or 'TABLE OF AUTHORITIES' in line:
            start = i
            break
    if start is None:
        return ""
    # Find ToA section end (next major section header)
    for j in range(start + 1, len(lines)):
        line = lines[j].strip()
        if not line:
            continue
        if any(h in line.upper() for h in major_headers):
            end = j
            break
        # If we hit another section header (all caps, long enough), stop
        if re.match(r'^[A-Z\s]+$', line) and len(line) > 10:
            end = j
            break
    if end is None:
        end = len(lines)
    return '\n'.join(lines[start:end])

def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip().lower())

def process_text_safe(text: str, max_text_size: int = 100000, max_citations: int = 100) -> List[Dict]:
    """Safe version of citation processing with limits and timeouts for debugging."""
    import time
    start_time = time.time()
    
    logger.info(f"[SAFETY] Starting safe citation processing...")
    logger.info(f"[SAFETY] Input text length: {len(text)} characters")
    
    # Limit text size
    if len(text) > max_text_size:
        text = text[:max_text_size]
        logger.info(f"[SAFETY] Truncated text to {max_text_size} characters")
    
    citations = []
    
    try:
        # Step 1: Simple regex extraction with limits
        logger.info(f"[SAFETY] Step 1: Starting simple regex extraction...")
        step_start = time.time()
        
        # Use simple patterns to avoid complex regex issues
        simple_patterns = [
            (r'\b\d+\s+Wn\.\s*\d+\b', 'Washington Reporter'),
            (r'\b\d+\s+P\.\s*\d+\b', 'Pacific Reporter'),
            (r'\b\d+\s+U\.S\.\s*\d+\b', 'US Supreme Court'),
            (r'\b\d+\s+S\.Ct\.\s*\d+\b', 'Supreme Court Reporter'),
            (r'\b\d+\s+L\.Ed\.\s*\d+\b', 'Lawyers Edition'),
        ]
        
        for pattern_str, pattern_name in simple_patterns:
            try:
                import re
                pattern = re.compile(pattern_str, re.IGNORECASE)
                matches = list(pattern.finditer(text))
                
                if len(matches) > 20:  # Limit matches per pattern
                    matches = matches[:20]
                    logger.info(f"[SAFETY] Limited {pattern_name} to 20 matches")
                
                logger.info(f"[SAFETY] Pattern {pattern_name}: {len(matches)} matches")
                
                for match in matches:
                    citation_str = match.group(0).strip()
                    if citation_str and len(citations) < max_citations:
                        citations.append({
                            'citation': citation_str,
                            'case_name': f"Extracted from {pattern_name}",
                            'year': None,
                            'source': 'Safe Processing'
                        })
                
                if len(citations) >= max_citations:
                    logger.info(f"[SAFETY] Reached citation limit of {max_citations}")
                    break
                    
            except Exception as e:
                logger.error(f"[SAFETY] Error with pattern {pattern_name}: {e}")
                continue
        
        step_time = time.time() - step_start
        logger.info(f"[SAFETY] Step 1: Complete - {len(citations)} citations in {step_time:.2f} seconds")
        
        # Skip expensive operations for debugging
        logger.debug(f"[SAFETY] Skipping verification and clustering for debugging")
        
        total_time = time.time() - start_time
        logger.info(f"[SAFETY] Total processing time: {total_time:.2f} seconds")
        
        return citations
        
    except Exception as e:
        logger.error(f"[SAFETY] Exception in process_text_safe: {e}")
        import traceback
        traceback.print_exc()
        return citations

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
    script_start_time = time.time()
    logger.info("=== SCRIPT STARTED ===")
    
    # Check dependencies first
    if not check_dependencies():
        logger.error("[ERROR] Missing dependencies. Exiting.")
        return
    
    log_memory_usage("Script start")
    
    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    logger.info(f"[STATUS] Using brief file: {brief_file}")
    logger.info(f"Comprehensive ToA vs Main Body Comparison")
    logger.info(f"Brief: {brief_file}")
    logger.info("=" * 80)
    
    logger.info("Step 1: Reading brief file...")
    step_start = time.time()
    # Read brief
    try:
        logger.info("[STATUS] Opening file...")
        with open(brief_file, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"   ✓ Read {len(text)} characters")
        log_timing(step_start, "File reading")
        log_memory_usage("After file read")
    except Exception as e:
        logger.error(f"[ERROR] Failed to read file: {e}")
        return
    logger.info("[STATUS] Finished reading file.")
    
    logger.info("\nStep 2: Extracting ToA section...")
    step_start = time.time()
    logger.info("[STATUS] Extracting TOA section...")
    try:
        toa_section = extract_toa_section(text)
        logger.debug(f"[DEBUG] TOA section length: {len(toa_section)}")
        logger.debug(f"[DEBUG] TOA section preview (first 1000 chars):\n{toa_section[:1000]}")
        
        # Check if TOA extraction is working correctly
        if len(toa_section) == len(text):
            logger.error("[WARNING] TOA section is the same length as full text - extraction may have failed!")
            logger.debug("[DEBUG] Looking for 'TABLE OF AUTHORITIES' in text...")
            toa_start = text.find('TABLE OF AUTHORITIES')
            if toa_start != -1:
                logger.debug(f"[DEBUG] Found 'TABLE OF AUTHORITIES' at position {toa_start}")
                # Try to find the end of TOA section
                toa_end = text.find('I.ASSIGNMENT OF ERRORS', toa_start)
                if toa_end != -1:
                    logger.debug(f"[DEBUG] Found end marker at position {toa_end}")
                    toa_section = text[toa_start:toa_end]
                    logger.debug(f"[DEBUG] Corrected TOA section length: {len(toa_section)}")
                else:
                    logger.debug("[DEBUG] Could not find end marker, using first 10000 chars of TOA")
                    toa_section = text[toa_start:toa_start+10000]
            else:
                logger.debug("[DEBUG] Could not find 'TABLE OF AUTHORITIES' in text")
        
        log_timing(step_start, "TOA extraction")
        log_memory_usage("After TOA extraction")
    except Exception as e:
        logger.error(f"[ERROR] Failed to extract TOA section: {e}")
        return
    logger.info("[STATUS] Finished extracting TOA section.")
    
    # Use a much simpler regex to find entry starts
    step_start = time.time()
    logger.info("[STATUS] Processing TOA chunks...")
    try:
        simple_entry_start_pattern = r' v\. '
        starts = [m.start() for m in re.finditer(simple_entry_start_pattern, toa_section)]
        # Only use up to 130 chunks
        starts = starts[:130] + [len(toa_section)] if len(starts) >= 130 else starts + [len(toa_section)]
        logger.debug(f"[DEBUG] Number of TOA chunks using simple regex (max 130): {len(starts)-1}")
        for idx in [127, 128, 129]:
            if idx < len(starts)-1:
                chunk = toa_section[starts[idx]:starts[idx+1]].strip()
                logger.debug(f"\n[DEBUG] TOA chunk {idx+1} (length {len(chunk)}):\n{chunk[:1000]}\n---END CHUNK---")
            else:
                logger.debug(f"[DEBUG] No chunk at index {idx+1}")
        log_timing(step_start, "TOA chunk processing")
    except Exception as e:
        logger.error(f"[ERROR] Failed to process TOA chunks: {e}")
        return
    logger.info("[STATUS] TOA chunk preview complete.")
    
    # Print debug for main body extraction
    logger.info("\nStep 3: Removing ToA from main body...")
    step_start = time.time()
    logger.info("[STATUS] Removing TOA section from main body...")
    try:
        main_body = text.replace(toa_section, "")
        logger.debug(f"[DEBUG] Main body length: {len(main_body)}")
        logger.info(f"   ✓ Main body prepared ({len(main_body)} characters)")
        log_timing(step_start, "Main body preparation")
        log_memory_usage("After main body prep")
    except Exception as e:
        logger.error(f"[ERROR] Failed to prepare main body: {e}")
        return
    logger.info("[STATUS] Finished preparing main body.")
    
    logger.info("\nStep 4: Parsing ToA using ToA parser...")
    step_start = time.time()
    logger.info("[STATUS] Parsing TOA section...")
    try:
        from toa_parser import ToAParser
        toa_parser = ToAParser()
        toa_entries = toa_parser.parse_toa_section(toa_section)[:20]
        logger.debug(f"[DEBUG] Parsed {len(toa_entries)} TOA entries (limited to 20)")
        logger.debug("[DEBUG] First 5 parsed ToA entries (case_name):")
        for i, entry in enumerate(toa_entries[:5]):
            logger.info(f"  {i+1}: {getattr(entry, 'case_name', None)}")
        logger.info(f"   ✓ Parsed {len(toa_entries)} ToA entries (limited to 20)")
        toa_citations = []
        for entry in toa_entries:
            for citation in entry.citations:
                toa_citations.append({
                    'citation': citation,
                    'case_name': entry.case_name,
                    'year': entry.years[0] if entry.years else None,
                    'source': 'ToA'
                })
        logger.debug(f"[DEBUG] Extracted {len(toa_citations)} TOA citations")
        logger.info(f"   ✓ Extracted {len(toa_citations)} ToA citations")
        log_timing(step_start, "TOA parsing")
        log_memory_usage("After TOA parsing")
    except Exception as e:
        logger.error(f"[ERROR] Failed to parse TOA section: {e}")
        return
    logger.info("[STATUS] Finished parsing TOA section.")
    
    logger.info("\nStep 5: Parsing main body using safe processor...")
    step_start = time.time()
    logger.info("[STATUS] Parsing main body citations...")
    try:
        # Use safe processing to avoid hanging
        logger.info("[STATUS] Using safe citation processing (limited scope)...")
        logger.debug(f"[DEBUG] About to process main body text with safe processor...")
        logger.debug(f"[DEBUG] Main body text length: {len(main_body)} characters")
        
        # Use our safe processing function with very small limits for testing
        body_citations = process_text_safe(main_body, max_text_size=10000, max_citations=20)
        logger.debug(f"[DEBUG] Safe processor returned {len(body_citations)} citations")
        
        logger.debug(f"[DEBUG] Extracted {len(body_citations)} main body citations")
        logger.info(f"   ✓ Extracted {len(body_citations)} main body citations")
        log_timing(step_start, "Main body citation processing")
        log_memory_usage("After main body processing")
    except Exception as e:
        logger.error(f"[ERROR] Failed to process main body citations: {e}")
        import traceback
        traceback.print_exc()
        return
    logger.info("[STATUS] Finished parsing main body.")
    
    logger.info("\nStep 6: Comparing results...")
    step_start = time.time()
    logger.info("[STATUS] Comparing TOA and main body citations...")
    try:
        # Compare results
        comparison = compare_citations(toa_citations, body_citations)
        logger.info("   ✓ Comparison complete")
        log_timing(step_start, "Citation comparison")
        log_memory_usage("After comparison")
    except Exception as e:
        logger.error(f"[ERROR] Failed to compare citations: {e}")
        return
    logger.info("[STATUS] Finished comparison.")
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL REPORT")
    logger.info("=" * 80)
    
    # Print results
    logger.info(f"\nSUMMARY:")
    logger.info(f"ToA citations: {len(toa_citations)}")
    logger.info(f"Main body citations: {len(body_citations)}")
    logger.info(f"Matching citations: {len(comparison['matching'])}")
    logger.info(f"ToA only: {len(comparison['toa_only'])}")
    logger.info(f"Main body only: {len(comparison['body_only'])}")
    logger.info(f"Different names: {len(comparison['different_names'])}")
    logger.info(f"Different years: {len(comparison['different_years'])}")
    
    # Print first 5 entries for each category
    def print_sample(title, items, fields=None):
        logger.info(f"\n{title} (showing up to 5):")
        for item in items[:5]:
            if fields:
                logger.info({k: item.get(k) for k in fields})
            else:
                logger.info(item)
        if len(items) > 5:
            logger.info(f"... and {len(items) - 5} more.")
    
    print_sample("Matching Citations", comparison['matching'], fields=['citation', 'toa', 'body'])
    print_sample("ToA Only Citations", comparison['toa_only'], fields=['citation', 'case_name', 'year'])
    print_sample("Main Body Only Citations", comparison['body_only'], fields=['citation', 'case_name', 'year'])
    print_sample("Different Names", comparison['different_names'], fields=['citation', 'toa_name', 'body_name', 'toa_year', 'body_year'])
    print_sample("Different Years", comparison['different_years'], fields=['citation', 'toa_name', 'body_name', 'toa_year', 'body_year'])
    
    # Show different names
    if comparison['different_names']:
        logger.info(f"\nCITATIONS WITH DIFFERENT CASE NAMES:")
        logger.info("-" * 60)
        for diff in comparison['different_names']:
            logger.info(f"Citation: {diff['citation']}")
            logger.info(f"  ToA:     {diff['toa_name']} ({diff['toa_year']})")
            logger.info(f"  Body:    {diff['body_name']} ({diff['body_year']})")
            logger.info()
    
    # Show different years
    if comparison['different_years']:
        logger.info(f"\nCITATIONS WITH DIFFERENT YEARS:")
        logger.info("-" * 60)
        for diff in comparison['different_years']:
            logger.info(f"Citation: {diff['citation']}")
            logger.info(f"  ToA:     {diff['toa_name']} ({diff['toa_year']})")
            logger.info(f"  Body:    {diff['body_name']} ({diff['body_year']})")
            logger.info()
    
    # Show ToA only citations
    if comparison['toa_only']:
        logger.info(f"CITATIONS ONLY IN ToA:")
        logger.info("-" * 60)
        for cit in comparison['toa_only'][:10]:  # Show first 10
            logger.info(f"  {cit['case_name']} ({cit['year']}) - {cit['citation']}")
        if len(comparison['toa_only']) > 10:
            logger.info(f"  ... and {len(comparison['toa_only']) - 10} more")
        logger.info()
    
    # Show main body only citations
    if comparison['body_only']:
        logger.info(f"CITATIONS ONLY IN MAIN BODY:")
        logger.info("-" * 60)
        for cit in comparison['body_only'][:10]:  # Show first 10
            logger.info(f"  {cit['case_name']} ({cit['year']}) - {cit['citation']}")
        if len(comparison['body_only']) > 10:
            logger.info(f"  ... and {len(comparison['body_only']) - 10} more")
        logger.info()
    
    log_timing(script_start_time, "Total script execution")
    log_memory_usage("Script end")
    logger.info("[STATUS] SCRIPT COMPLETE.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        logger.error('=== EXCEPTION OCCURRED ===')
        logger.info(e)
        traceback.print_exc() 