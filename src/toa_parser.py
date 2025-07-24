"""
IMPROVED Table of Authorities (ToA) Parser
Extracts citations, case names, and years from Table of Authorities sections.

SAFETY IMPROVEMENTS:
- Timeout protection on regex operations
- Chunk size limits
- Progress tracking
- Error recovery
- Memory-efficient processing
"""

import re
import logging
import time
import threading
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

# Safety configuration
MAX_CHUNK_SIZE = 5000      # 5KB per chunk
MAX_CHUNKS = 200           # Maximum chunks to process
MAX_PATTERN_TIME = 5       # 5 seconds per pattern
MAX_TOTAL_TIME = 120       # 2 minutes total

def timeout(seconds):
    """Cross-platform timeout decorator using threading."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
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
            
            if exception[0]:
                raise exception[0]  # type: ignore[misc]
            
            return result[0]
        return wrapper
    return decorator

@dataclass
class ToAEntry:
    """Represents a single entry in a Table of Authorities."""
    case_name: str
    citations: List[str]
    years: List[str]
    page_numbers: List[str]
    confidence: float
    source_line: str

class ImprovedToAParser:
    """
    IMPROVED Parser for Table of Authorities sections with safety measures.
    """
    
    def __init__(self):
        super().__init__()
        logger.info("[TOA PARSER] Initializing improved ToA parser...")
        
        # Simplified patterns to reduce regex complexity
        self.toa_section_patterns = [
            r'TABLE\s+OF\s+AUTHORITIES',
            r'AUTHORITIES?\s+CITED',
            r'CITED\s+AUTHORITIES?',
            r'Cases\s+Cited',
            r'Legal\s+Authorities?',
        ]
        
        # Improved ToA entry patterns: more flexible matching
        self.toa_entry_patterns = [
            # Pattern 1: Full case name (e.g., 'Smith v. Jones, 534 F.3d 1290 (2008)')
            r'([A-Z][A-Za-z\'\-\s\.]+? v\.? [A-Z][A-Za-z\'\-\s\.]+?),?\s+([\dA-Za-z\.\s]+\(\d{4}\))',
            # Pattern 2: In re ...
            r'(In\s+re\s+[A-Z][A-Za-z\'\-\s\.]+),?\s+([\dA-Za-z\.\s]+\(\d{4}\))',
            # Pattern 3: Dep't of ... v. ...
            r'(Dep[\'`]t of [A-Za-z0-9&.,\'\s\-]+ v\. [A-Z][A-Za-z0-9&.,\'\s\-]+),?\s+([\dA-Za-z\.\s]+\(\d{4}\))',
            # Pattern 4: More flexible case name pattern
            r'([A-Z][A-Za-z\'\-\s\.]+? v\.? [A-Z][A-Za-z\'\-\s\.]+?)(?:,|\s+)([\dA-Za-z\.\s]+\(\d{4}\))',
        ]
        
        # Simplified patterns
        self.year_patterns = [
            r'\((\d{4})\)',
            r'\b(\d{4})\b',
        ]
        
        self.citation_patterns = [
            r'\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)',
            r'\d+\s+[A-Za-z\.\s]+\d+',
        ]
        
        logger.info("[TOA PARSER] Initialization complete")
    
    @timeout(30)
    def detect_toa_section(self, text: str) -> Optional[Tuple[int, int]]:
        """Safely detect ToA section with timeout protection."""
        logger.info(f"[TOA DETECT] Searching for ToA in {len(text):,} characters...")
        
        # Limit search to first part of document
        search_text = text[:50000] if len(text) > 50000 else text
        
        for i, pattern in enumerate(self.toa_section_patterns):
            try:
                match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    start = match.start()
                    logger.info(f"[TOA DETECT] Found ToA at position {start} with pattern {i}")
                    
                    # Find the end safely
                    end = self._find_toa_end_safe(text, start)
                    logger.info(f"[TOA DETECT] ToA boundaries: {start} to {end}")
                    return (start, end)
                    
            except Exception as e:
                logger.error(f"[TOA DETECT] Error with pattern {i}: {e}")
                continue
        
        logger.info("[TOA DETECT] No ToA section found")
        return None
    
    def _find_toa_end_safe(self, text: str, start: int) -> int:
        """Safely find ToA end with limits."""
        # Look for common section headers after ToA
        end_patterns = [
            r'\n\s*(?:ARGUMENT|DISCUSSION|CONCLUSION)\s*\n',
            r'\n\s*(?:I\.|II\.|III\.)\s+[A-Z]',
            r'\n\s*\d+\.\s+[A-Z]',
        ]
        
        # Search in limited range after start
        search_range = min(20000, len(text) - start)  # Max 20KB search
        search_text = text[start:start + search_range]
        
        for pattern in end_patterns:
            try:
                match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    return start + match.start()
            except Exception as e:
                logger.error(f"[TOA END] Error with pattern: {e}")
                continue
        
        # Default: end after reasonable ToA size
        return start + min(15000, len(text) - start)
    
    @timeout(MAX_TOTAL_TIME)
    def parse_toa_section(self, text: str) -> List[ToAEntry]:
        """Safely parse ToA section with comprehensive protection, handling multiple citations per line."""
        logger.info(f"[TOA PARSE] Starting parse of {len(text):,} characters...")
        start_time = time.time()
        entries = []
        processed_chunks = 0
        try:
            # Split into manageable chunks
            chunks = self._safe_chunk_text(text)
            logger.info(f"[TOA PARSE] Created {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                if processed_chunks >= MAX_CHUNKS:
                    logger.info(f"[TOA PARSE] Reached max chunks limit ({MAX_CHUNKS})")
                    break
                # Progress update
                if i % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"[TOA PARSE] Processing chunk {i+1}/{len(chunks)} (elapsed: {elapsed:.1f}s)")
                try:
                    # If chunk starts with v./vs./versus, look at previous line
                    chunk_stripped = chunk.lstrip()
                    if re.match(r'^(v\.?|vs\.?|versus)\b', chunk_stripped, re.IGNORECASE):
                        # Find the chunk's position in the original text
                        chunk_pos = text.find(chunk)
                        if chunk_pos > 0:
                            # Get the text before the chunk and find the previous line
                            before = text[:chunk_pos].rstrip('\n')
                            prev_line = before.split('\n')[-1].strip()
                            if prev_line:
                                # Prepend previous line to chunk
                                chunk = prev_line + ' ' + chunk_stripped
                    # NEW: Split chunk by ' v. ' to handle multiple citations per line
                    sub_chunks = re.split(r'(?<=[A-Za-z\.])\s+v\.\s+', chunk)
                    if len(sub_chunks) > 1:
                        # Re-add the ' v. ' to each except the first
                        for idx, sub in enumerate(sub_chunks):
                            if idx == 0:
                                sub_chunk = sub
                            else:
                                sub_chunk = 'v. ' + sub
                            entry = self._parse_chunk_safe(sub_chunk, i)
                            if entry:
                                entries.append(entry)
                    else:
                        entry = self._parse_chunk_safe(chunk, i)
                        if entry:
                            entries.append(entry)
                    processed_chunks += 1
                    if len(entries) >= 100:
                        break
                except Exception as e:
                    logger.error(f"[TOA PARSE] Error processing chunk {i}: {e}")
                    continue
        except Exception as e:
            logger.error(f"[TOA PARSE] Error in parse_toa_section: {e}")
        return entries
    
    def _safe_chunk_text(self, text: str) -> List[str]:
        """Split text into safe chunks for processing."""
        # Look for natural break points (case entries)
        entry_start_pattern = r'(?:^|\n)\s*[A-Z][A-Za-z\'\-&\. ]{1,80}?\s+v\.'
        
        chunks = []
        current_pos = 0
        
        # Find all potential entry start positions
        try:
            matches = list(re.finditer(entry_start_pattern, text, re.MULTILINE))
            
            if not matches:
                # No clear entries found, split by size
                for i in range(0, len(text), MAX_CHUNK_SIZE):
                    chunks.append(text[i:i + MAX_CHUNK_SIZE])
                return chunks
            
            # Split at entry boundaries
            for i, match in enumerate(matches):
                if i == 0:
                    continue  # Skip first match
                
                chunk_start = current_pos
                chunk_end = match.start()
                
                # Create chunk
                chunk = text[chunk_start:chunk_end].strip()
                if chunk and len(chunk) > 10:
                    chunks.append(chunk)
                
                current_pos = match.start()
                
                # Limit chunk count
                if len(chunks) >= MAX_CHUNKS:
                    break
            
            # Add final chunk
            if current_pos < len(text):
                final_chunk = text[current_pos:].strip()
                if final_chunk and len(final_chunk) > 10:
                    chunks.append(final_chunk)
            
        except Exception as e:
            logger.error(f"[TOA CHUNK] Error creating chunks: {e}")
            # Fallback: simple size-based chunking
            for i in range(0, len(text), MAX_CHUNK_SIZE):
                chunks.append(text[i:i + MAX_CHUNK_SIZE])
        
        logger.info(f"[TOA CHUNK] Created {len(chunks)} chunks")
        return chunks
    
    @timeout(MAX_PATTERN_TIME)
    def _parse_chunk_safe(self, chunk: str, chunk_index: int) -> Optional[ToAEntry]:
        """Safely parse a single chunk."""
        # Clean the chunk
        chunk = chunk.strip()
        
        # Remove trailing page indicators
        chunk = re.sub(r'[ \t\u2022\u00b7]*[.·•]+[ \t]*\d+\s*$', '', chunk)
        
        # Try simplified patterns first
        for i, pattern in enumerate(self.toa_entry_patterns):
            try:
                match = re.search(pattern, chunk, re.MULTILINE)
                if match:
                    return self._extract_entry_from_match_safe(match, chunk)
            except Exception as e:
                logger.error(f"[TOA CHUNK] Pattern {i} failed on chunk {chunk_index}: {e}")
                continue
        
        # Try flexible parsing as fallback
        return self._parse_chunk_flexible(chunk)
    
    def _extract_entry_from_match_safe(self, match: re.Match, chunk: str) -> Optional[ToAEntry]:
        """Safely extract entry from regex match."""
        try:
            groups = match.groups()
            
            # Extract case name (first group)
            case_name = groups[0].strip() if groups[0] else ""
            
            # Fix case name if it starts with v.
            case_name = fix_case_name_default(case_name, chunk)
            
            # Extract citations (second group)
            citations_text = groups[1].strip() if len(groups) > 1 and groups[1] else ""
            citations = self._extract_citations_safe(citations_text)
            
            # Extract years
            years = self._extract_years_safe(citations_text + " " + chunk)
            
            # Extract page numbers if available
            page_numbers = []
            if len(groups) > 2 and groups[2]:
                page_numbers = [groups[2]]
            
            if case_name and citations:
                return ToAEntry(
                    case_name=case_name,
                    citations=citations,
                    years=years,
                    page_numbers=page_numbers,
                    confidence=0.8,
                    source_line=chunk[:200]  # Limit source line length
                )
                
        except Exception as e:
            logger.error(f"[TOA EXTRACT] Error extracting from match: {e}")
        
        return None
    
    def _parse_chunk_flexible(self, chunk: str) -> Optional[ToAEntry]:
        """Flexible parsing for chunks that don't match standard patterns."""
        try:
            # Look for basic pattern: text, citation (year)
            pattern = r'^([^,]+),\s*([^,]+\(\d{4}\))'
            match = re.search(pattern, chunk)
            
            if match:
                case_name = match.group(1).strip()
                citations_text = match.group(2).strip()
                
                # Clean case name
                case_name = re.sub(r'\s+', ' ', case_name)
                
                # Extract components
                citations = self._extract_citations_safe(citations_text)
                years = self._extract_years_safe(citations_text)
                
                if case_name and citations:
                    return ToAEntry(
                        case_name=case_name,
                        citations=citations,
                        years=years,
                        page_numbers=[],
                        confidence=0.6,
                        source_line=chunk[:200]
                    )
        except Exception as e:
            logger.error(f"[TOA FLEXIBLE] Error in flexible parsing: {e}")
        
        return None
    
    def _extract_citations_safe(self, text: str) -> List[str]:
        """Safely extract citations with timeout protection."""
        citations = set()  # Use set to avoid duplicates
        
        for pattern in self.citation_patterns:
            try:
                matches = re.findall(pattern, text)
                citations.update(matches)
                
                # Limit number of citations per text
                if len(citations) >= 10:
                    break
                    
            except Exception as e:
                logger.error(f"[TOA CITATIONS] Error with pattern: {e}")
                continue
        
        return list(citations)
    
    def _extract_years_safe(self, text: str) -> List[str]:
        """Safely extract years with validation."""
        years = set()
        
        for pattern in self.year_patterns:
            try:
                matches = re.findall(pattern, text)
                for year in matches:
                    year_int = int(year)
                    if 1900 <= year_int <= 2030:  # Reasonable year range
                        years.add(year)
                        
                # Limit years per entry
                if len(years) >= 3:
                    break
                    
            except Exception as e:
                logger.error(f"[TOA YEARS] Error with pattern: {e}")
                continue
        
        return list(years)
    
    @timeout(60)
    def extract_years_from_toa(self, text: str) -> List[str]:
        """Extract all years from ToA sections safely."""
        years = []
        
        try:
            # Detect ToA section
            toa_section = self.detect_toa_section(text)
            if not toa_section:
                return years
            
            start, end = toa_section
            toa_text = text[start:end]
            
            # Parse ToA entries
            entries = self.parse_toa_section(toa_text)
            
            # Collect all years
            for entry in entries:
                years.extend(entry.years)
            
            # Remove duplicates and sort
            years = sorted(list(set(years)))
            
        except Exception as e:
            logger.error(f"[TOA YEARS] Error extracting years: {e}")
        
        return years
    
    @timeout(60)
    def get_toa_citation_map(self, text: str) -> Dict[str, List[str]]:
        """Create citation-to-year mapping safely."""
        citation_year_map = {}
        
        try:
            # Detect ToA section
            toa_section = self.detect_toa_section(text)
            if not toa_section:
                return citation_year_map
            
            start, end = toa_section
            toa_text = text[start:end]
            
            # Parse ToA entries
            entries = self.parse_toa_section(toa_text)
            
            # Create mapping
            for entry in entries:
                for citation in entry.citations:
                    if citation not in citation_year_map:
                        citation_year_map[citation] = []
                    citation_year_map[citation].extend(entry.years)
            
            # Remove duplicates from year lists
            for citation in citation_year_map:
                citation_year_map[citation] = list(set(citation_year_map[citation]))
            
        except Exception as e:
            logger.error(f"[TOA MAP] Error creating citation map: {e}")
        
        return citation_year_map

    def parse_toa_section_simple(self, text: str) -> List[ToAEntry]:
        """Simple, direct parsing of ToA section without complex chunking."""
        logger.info(f"[TOA SIMPLE] Starting simple parse of {len(text):,} characters...")
        entries = []
        
        # Find the ToA section
        toa_bounds = self.detect_toa_section(text)
        if not toa_bounds:
            return entries
            
        start, end = toa_bounds
        toa_section = text[start:end]
        
        # Simple pattern to find case names followed by citations
        # Look for: Case Name, Citation (Year)
        simple_pattern = r'([A-Z][A-Za-z\'\-\s\.]+? v\.? [A-Z][A-Za-z\'\-\s\.]+?),?\s+([\dA-Za-z\.\s]+\(\d{4}\))'
        
        matches = re.finditer(simple_pattern, toa_section, re.MULTILINE)
        for match in matches:
            case_name = match.group(1).strip()
            citation_text = match.group(2).strip()
            
            # Extract years from citation
            years = self._extract_years_safe(citation_text)
            
            # Extract citations
            citations = self._extract_citations_safe(citation_text)
            
            if case_name and citations:
                entry = ToAEntry(
                    case_name=case_name,
                    citations=citations,
                    years=years,
                    page_numbers=[],
                    confidence=0.8,
                    source_line=match.group(0)
                )
                entries.append(entry)
                logger.info(f"[TOA SIMPLE] Found: {case_name} - {citations} - {years}")
        
        logger.info(f"[TOA SIMPLE] Found {len(entries)} entries")
        return entries


# Convenience functions for backward compatibility
def extract_years_from_toa_enhanced(text: str, citation: Optional[str] = None) -> List[str]:
    """Enhanced year extraction using improved parser."""
    parser = ImprovedToAParser()
    return parser.extract_years_from_toa(text)

def get_citation_year_from_toa(text: str, citation: str) -> Optional[str]:
    """Get year for specific citation using improved parser."""
    parser = ImprovedToAParser()
    citation_year_map = parser.get_toa_citation_map(text)
    
    # Try exact match first
    if citation in citation_year_map and citation_year_map[citation]:
        return citation_year_map[citation][0]
    
    # Try partial match (citation without year)
    citation_no_year = re.sub(r'\s*\(\d{4}\)', '', citation).strip()
    for toa_citation, years in citation_year_map.items():
        toa_citation_no_year = re.sub(r'\s*\(\d{4}\)', '', toa_citation).strip()
        if citation_no_year == toa_citation_no_year and years:
            return years[0]
    
    return None

# Create alias for backward compatibility
ToAParser = ImprovedToAParser 

# Add this helper function

def fix_case_name_default(case_name: str, line: str) -> str:
    # If case_name starts with v. or vs. or versus
    if re.match(r'^(v\.?|vs\.?|versus)\b', case_name, re.IGNORECASE):
        # Find the word before v. in the line
        match = re.search(r'(\b\w+)\s+(v\.?|vs\.?|versus)\b', line, re.IGNORECASE)
        if match:
            first_party = match.group(1)
            return f'{first_party} {case_name}'
    return case_name 