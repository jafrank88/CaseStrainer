#!/usr/bin/env python3
"""
IMPROVED Comprehensive comparison of ToA vs main body extraction.
Uses reliable ToA parser for ToA sections and unified processor for main body.
Highlights differences in case names and years.

SAFETY IMPROVEMENTS:
- Timeouts on all major operations
- Text size limits
- Progress tracking
- Safe mode operation
- Enhanced error handling
- Granular debugging
"""

import os
import sys
import re
import time
import threading
import logging
import warnings
from collections import defaultdict
from typing import List, Dict, Any, Optional
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info('=== IMPROVED SCRIPT STARTED ===')

# Safety configuration
class SafetyConfig:
    MAX_TEXT_SIZE = 500000  # 500KB limit
    MAX_TOA_SIZE = 200000   # 200KB limit for ToA section
    MAX_CITATIONS = 1000    # Limit citations processed
    OPERATION_TIMEOUT = 120 # 2 minutes per operation
    ENABLE_VERIFICATION = False  # Disable API calls initially
    ENABLE_CLUSTERING = False    # Disable clustering initially
    DEBUG_MODE = True

config = SafetyConfig()

def timeout(seconds):
    """Cross-platform timeout decorator using threading."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result: List[Any] = [None]
            exception: List[Optional[Exception]] = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                logger.info(f"[TIMEOUT] Function {func.__name__} timed out after {seconds} seconds")
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            if exception[0] is not None:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator

def safe_import(module_name: str, class_name: Optional[str] = None):
    """Safely import modules with error handling."""
    try:
        if class_name:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        else:
            return __import__(module_name)
    except Exception as e:
        logger.error(f'[ERROR] Failed to import {class_name or module_name} from {module_name}: {e}')
        return None

logger.info('--- SAFE IMPORT TEST START ---')
# Import the original modules, not the safe wrappers
ToAParser = safe_import('toa_parser', 'ToAParser')
UnifiedCitationProcessorV2 = safe_import('unified_citation_processor_v2', 'UnifiedCitationProcessorV2')

if not ToAParser:
    logger.error('[ERROR] ToAParser not available - script cannot continue')
    sys.exit(1)
if not UnifiedCitationProcessorV2:
    logger.error('[ERROR] UnifiedCitationProcessorV2 not available - script cannot continue')
    sys.exit(1)

logger.info('Imported modules successfully')
logger.info('--- SAFE IMPORT TEST END ---')

def safe_text_read(file_path: str, max_size: Optional[int] = None) -> Optional[str]:
    """Safely read text file with size limits."""
    max_size = max_size or config.MAX_TEXT_SIZE
    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"[SAFE READ] File size: {file_size:,} bytes")
        
        if file_size > max_size:
            logger.info(f"[SAFE READ] File too large ({file_size:,} bytes), limiting to {max_size:,} bytes")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_size > max_size:
                text = f.read(max_size)
            else:
                text = f.read()
        
        logger.info(f"[SAFE READ] Successfully read {len(text):,} characters")
        return text
        
    except Exception as e:
        logger.error(f"[SAFE READ ERROR] Failed to read {file_path}: {e}")
        return None

def extract_first_section_header(text: str) -> Optional[str]:
    """Parse the Table of Contents to find the first main section header (e.g., 'I. ASSIGNMENT OF ERRORS')."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'table of contents' in line.lower():
            # Found ToC line - look for section headers on this line or next few lines
            toc_line = line.strip()
            
            # First, check if section headers are on the same line as ToC
            section_match = re.search(r'([IVX]+\.\s*[A-Z\s]+)', toc_line)
            if section_match:
                header = section_match.group(1).strip()
                logger.info(f"[SAFE TOA] Found section header on ToC line: '{header}'")
                return header
            
            # If not on same line, check next few lines
            for j in range(i + 1, min(i + 10, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                section_match = re.search(r'([IVX]+\.\s*[A-Z\s]+)', next_line)
                if section_match:
                    header = section_match.group(1).strip()
                    logger.info(f"[SAFE TOA] Found section header on line {j}: '{header}'")
                    return header
                # Stop if we hit another major section
                if any(marker in next_line.upper() for marker in ['TABLE OF AUTHORITIES', 'INTRODUCTION', 'ARGUMENT']):
                    break
    return None

@timeout(60)
def safe_extract_toa_section(text: str) -> str:
    """Safely extract ToA section using character positions for start and end, robust to line breaks."""
    logger.info("[SAFE TOA] Starting ToA section extraction...")
    if len(text) > config.MAX_TEXT_SIZE:
        logger.info(f"[SAFE TOA] Text too large, using first {config.MAX_TEXT_SIZE:,} characters")
        text = text[:config.MAX_TEXT_SIZE]
    # Find ToA section start using character position
    toa_pos = text.lower().find('table of authorities')
    if toa_pos == -1:
        logger.info("[SAFE TOA] No ToA section found")
        return ""
    # Find the next major section header (e.g., 'II.', 'III.', etc.) after ToA start
    end_pos = None
    section_header_pattern = re.compile(r'\n\s*([IVX]+\.[A-Z][A-Z\s]+)', re.MULTILINE)
    for match in section_header_pattern.finditer(text, toa_pos):
        if match.start() > toa_pos:
            end_pos = match.start()
            logger.info(f"[SAFE TOA] Found ToA end at char pos {end_pos}: '{match.group(1).strip()}'")
            break
    if end_pos is None:
        end_pos = min(len(text), toa_pos + 20000)
        logger.info(f"[SAFE TOA] No clear end found, using char pos {end_pos}")
    toa_text = text[toa_pos:end_pos]
    if len(toa_text) > config.MAX_TOA_SIZE:
        logger.info(f"[SAFE TOA] ToA section too large ({len(toa_text):,} chars), truncating to {config.MAX_TOA_SIZE:,}")
        toa_text = toa_text[:config.MAX_TOA_SIZE]
    logger.info(f"[SAFE TOA] Extracted ToA section: {len(toa_text):,} characters")
    return toa_text

@timeout(120)
def safe_parse_toa(toa_parser, toa_section: str, max_entries: int = 500) -> List[Any]:
    """Safely parse ToA section with limits."""
    logger.info(f"[SAFE TOA PARSE] Starting ToA parsing with max {max_entries} entries...")
    
    try:
        # Parse with the ToA parser
        entries = toa_parser.parse_toa_section(toa_section)
        
        # Limit number of entries
        if len(entries) > max_entries:
            logger.info(f"[SAFE TOA PARSE] Found {len(entries)} entries, limiting to {max_entries}")
            entries = entries[:max_entries]
        
        logger.info(f"[SAFE TOA PARSE] Successfully parsed {len(entries)} ToA entries")
        
        # Debug first few entries
        for i, entry in enumerate(entries[:3]):
            logger.info(f"[SAFE TOA PARSE] Entry {i+1}: {getattr(entry, 'case_name', 'N/A')}")
        
        return entries
        
    except Exception as e:
        logger.error(f"[SAFE TOA PARSE ERROR] {e}")
        import traceback
        traceback.print_exc()
        return []

class SafeUnifiedProcessor:
    """Wrapper for UnifiedCitationProcessorV2 with safety measures."""
    
    def __init__(self):
        logger.info("[SAFE PROCESSOR] Initializing safe processor...")
        
        try:
            # Import and configure the processor
            from unified_citation_processor_v2 import ProcessingConfig
            
            # Create safe configuration
            self.config = ProcessingConfig(
                use_eyecite=False,               # Disable eyecite (can be slow)
                use_regex=True,                  # Keep regex but with limits
                extract_case_names=True,         # Keep case name extraction
                extract_dates=True,              # Keep date extraction
                enable_clustering=config.ENABLE_CLUSTERING,   # Use global config
                enable_deduplication=True,       # Keep deduplication
                enable_verification=config.ENABLE_VERIFICATION, # Use global config
                context_window=150,              # Smaller context
                min_confidence=0.3,              # Lower threshold
                max_citations_per_text=config.MAX_CITATIONS,
                debug_mode=config.DEBUG_MODE
            )
            
            # Initialize processor
            if UnifiedCitationProcessorV2 is not None:
                self.processor = UnifiedCitationProcessorV2(self.config)
            else:
                self.processor = None
            logger.info("[SAFE PROCESSOR] Processor initialized successfully")
            
        except Exception as e:
            logger.error(f"[SAFE PROCESSOR ERROR] Failed to initialize: {e}")
            self.processor = None
    
    @timeout(180)  # 3 minutes for main body processing
    def safe_process_text(self, text: str) -> List[Dict[str, Any]]:
        """Safely process text with the processor."""
        if not self.processor:
            logger.info("[SAFE PROCESSOR] Processor not available")
            return []
        
        logger.info(f"[SAFE PROCESSOR] Processing text of {len(text):,} characters...")
        
        # Limit text size
        if len(text) > config.MAX_TEXT_SIZE:
            logger.info(f"[SAFE PROCESSOR] Text too large, using first {config.MAX_TEXT_SIZE:,} characters")
            text = text[:config.MAX_TEXT_SIZE]
        
        try:
            # Process with timeout protection
            results = self.processor.process_text(text)
            
            # Convert to dict format and limit results
            citations = []
            for i, citation in enumerate(results[:config.MAX_CITATIONS]):
                try:
                    citation_dict = {
                        'citation': getattr(citation, 'citation', ''),
                        'case_name': getattr(citation, 'extracted_case_name', None),
                        'year': getattr(citation, 'extracted_date', None),
                        'source': 'Main Body'
                    }
                    citations.append(citation_dict)
                    
                    if i < 3:  # Debug first few
                        logger.info(f"[SAFE PROCESSOR] Citation {i+1}: {citation_dict['citation']}")
                        
                except Exception as e:
                    logger.error(f"[SAFE PROCESSOR] Error processing citation {i}: {e}")
                    continue
            
            logger.info(f"[SAFE PROCESSOR] Successfully processed {len(citations)} citations")
            return citations
            
        except TimeoutError:
            logger.info("[SAFE PROCESSOR] Processing timed out")
            return []
        except Exception as e:
            logger.error(f"[SAFE PROCESSOR ERROR] {e}")
            import traceback
            traceback.print_exc()
            return []

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
        'different_years': [],
        'stats': {
            'toa_count': len(toa_citations),
            'body_count': len(body_citations)
        }
    }
    
    logger.info(f"[COMPARE] Comparing {len(toa_citations)} ToA vs {len(body_citations)} body citations")
    
    # Create lookup dictionaries
    toa_lookup = {}
    for cit in toa_citations:
        key = normalize_text(cit.get('citation', ''))
        if key:  # Only add non-empty keys
            toa_lookup[key] = cit
    
    body_lookup = {}
    for cit in body_citations:
        key = normalize_text(cit.get('citation', ''))
        if key:  # Only add non-empty keys
            body_lookup[key] = cit
    
    logger.info(f"[COMPARE] Created lookups: {len(toa_lookup)} ToA, {len(body_lookup)} body")
    
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
    
    # Update stats
    results['stats'].update({
        'matching_count': len(results['matching']),
        'toa_only_count': len(results['toa_only']),
        'body_only_count': len(results['body_only']),
        'different_names_count': len(results['different_names']),
        'different_years_count': len(results['different_years'])
    })
    
    return results

def main():
    """Main comparison function with comprehensive safety measures."""
    logger.info("=== IMPROVED SCRIPT STARTED ===")
    start_time = time.time()
    
    # Configuration
    brief_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    
    logger.info(f"[MAIN] Using brief file: {brief_file}")
    logger.info(f"[MAIN] Safety config: max_text={config.MAX_TEXT_SIZE:,}, max_citations={config.MAX_CITATIONS}")
    logger.info(f"[MAIN] Verification: {config.ENABLE_VERIFICATION}, Clustering: {config.ENABLE_CLUSTERING}")
    logger.info("=" * 80)
    
    try:
        # Step 1: Read brief file safely
        logger.info("\n[MAIN] Step 1: Reading brief file...")
        text = safe_text_read(brief_file)
        if not text:
            logger.error("[MAIN ERROR] Failed to read brief file")
            return
        
        elapsed = time.time() - start_time
        logger.info(f"[MAIN] Step 1 complete in {elapsed:.2f}s - Read {len(text):,} characters")
        
        # Step 2: Extract ToA section safely
        logger.info("\n[MAIN] Step 2: Extracting ToA section...")
        step_start = time.time()
        
        toa_section = safe_extract_toa_section(text)
        if not toa_section:
            logger.warning("[MAIN WARNING] No ToA section found")
            toa_citations = []
        else:
            elapsed = time.time() - step_start
            logger.info(f"[MAIN] Step 2 complete in {elapsed:.2f}s - ToA section: {len(toa_section):,} characters")
            
            # Step 3: Parse ToA section safely
            logger.info("\n[MAIN] Step 3: Parsing ToA section...")
            step_start = time.time()
            
            toa_parser = ToAParser() if ToAParser is not None else None
            if toa_parser is not None:
                toa_entries = safe_parse_toa(toa_parser, toa_section)
            else:
                toa_entries = []
            
            # Convert ToA entries to citation format
            toa_citations = []
            for entry in toa_entries:
                for citation in getattr(entry, 'citations', []):
                    toa_citations.append({
                        'citation': citation,
                        'case_name': getattr(entry, 'case_name', None),
                        'year': getattr(entry, 'years', [None])[0] if getattr(entry, 'years', []) else None,
                        'source': 'ToA'
                    })
            
            elapsed = time.time() - step_start
            logger.info(f"[MAIN] Step 3 complete in {elapsed:.2f}s - Extracted {len(toa_citations)} ToA citations")
        
        # Step 4: Prepare main body
        logger.info("\n[MAIN] Step 4: Preparing main body...")
        step_start = time.time()
        
        if toa_section:
            main_body = text.replace(toa_section, "")
        else:
            main_body = text
        
        elapsed = time.time() - step_start
        logger.info(f"[MAIN] Step 4 complete in {elapsed:.2f}s - Main body: {len(main_body):,} characters")
        
        # Step 5: Process main body safely
        logger.info("\n[MAIN] Step 5: Processing main body citations...")
        step_start = time.time()
        
        safe_processor = SafeUnifiedProcessor()
        body_citations = safe_processor.safe_process_text(main_body)
        
        elapsed = time.time() - step_start
        logger.info(f"[MAIN] Step 5 complete in {elapsed:.2f}s - Extracted {len(body_citations)} body citations")
        
        # Step 6: Compare results
        logger.info("\n[MAIN] Step 6: Comparing results...")
        step_start = time.time()
        
        comparison = compare_citations(toa_citations, body_citations)
        
        elapsed = time.time() - step_start
        logger.info(f"[MAIN] Step 6 complete in {elapsed:.2f}s")
        
        # Print results
        total_elapsed = time.time() - start_time
        logger.info(f"\n{'='*80}")
        logger.info(f"FINAL REPORT (Total time: {total_elapsed:.2f}s)")
        logger.info(f"{'='*80}")
        
        # Summary statistics
        stats = comparison['stats']
        logger.info(f"\nSUMMARY:")
        logger.info(f"ToA citations: {stats['toa_count']}")
        logger.info(f"Main body citations: {stats['body_count']}")
        logger.info(f"Matching citations: {stats['matching_count']}")
        logger.info(f"ToA only: {stats['toa_only_count']}")
        logger.info(f"Main body only: {stats['body_only_count']}")
        logger.info(f"Different names: {stats['different_names_count']}")
        logger.info(f"Different years: {stats['different_years_count']}")
        
        # Show samples of each category
        def print_sample(title, items, limit=5):
            logger.info(f"\n{title} (showing up to {limit}):")
            for i, item in enumerate(items[:limit]):
                if isinstance(item, dict):
                    citation = item.get('citation', 'N/A')[:50]
                    case_name = item.get('case_name', 'N/A')
                    if case_name and len(case_name) > 40:
                        case_name = case_name[:40] + "..."
                    year = item.get('year', 'N/A')
                    logger.info(f"  {i+1}: {citation} | {case_name} | {year}")
                else:
                    logger.info(f"  {i+1}: {str(item)[:80]}")
            if len(items) > limit:
                logger.info(f"  ... and {len(items) - limit} more.")
        
        print_sample("ToA Only Citations", comparison['toa_only'])
        print_sample("Main Body Only Citations", comparison['body_only'])
        print_sample("Matching Citations", comparison['matching'])
        
        logger.info("CITATIONS WITH DIFFERENT CASE NAMES:")
        logger.info("-"*60)
        for diff in comparison.get('different_names', [])[:5]:
            logger.info(f"1. Citation: {diff['citation']}")
            toa_name = diff.get('toa_name') or ''
            body_name = diff.get('body_name') or ''
            logger.info(f"   ToA: {toa_name[:60]}")
            logger.info(f"   Body: {body_name[:60]}")
            logger.info("")  # Empty line for readability
        
        logger.info("CITATIONS WITH DIFFERENT YEARS:")
        logger.info("-"*60)
        for diff in comparison.get('different_years', [])[:5]:
            logger.info(f"1. Citation: {diff['citation']}")
            toa_year = diff.get('toa_year') or ''
            body_year = diff.get('body_year') or ''
            logger.info(f"   ToA: {toa_year}")
            logger.info(f"   Body: {body_year}")
            logger.info("")  # Empty line for readability
        
        logger.info(f"[MAIN] SCRIPT COMPLETED SUCCESSFULLY in {total_elapsed:.2f}s")
        
    except KeyboardInterrupt:
        logger.info("\n[MAIN] Script interrupted by user")
    except Exception as e:
        logger.error(f"\n[MAIN ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        total_elapsed = time.time() - start_time
        logger.info(f"\n[MAIN] Total execution time: {total_elapsed:.2f} seconds")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f'=== FATAL EXCEPTION ===')
        logger.error(f'Error: {e}')
        import traceback
        traceback.print_exc()
        logger.info(f'=== SCRIPT TERMINATED ===') 