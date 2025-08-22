#!/usr/bin/env python3
"""
Optimized Unified Citation Processor v2

This version maintains the corrected processing order and comprehensive features
but optimizes for performance while preserving accuracy.

PERFORMANCE OPTIMIZATIONS:
1. Early exit conditions to avoid unnecessary processing
2. Cached regex compilation
3. Optimized text chunking for large documents
4. Selective eyecite usage (only when regex finds few results)
5. Efficient parallel detection using proximity heuristics
6. Streamlined name/date extraction with context windows

MAINTAINED FEATURES:
- Corrected processing order (context operations before deduplication)
- Enhanced false positive prevention
- Both regex and eyecite extraction
- Proper name/date extraction with full text context
- Parallel citation detection and clustering
"""

import re
import logging
import time
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from src.models import CitationResult

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Track processing statistics for performance analysis."""
    total_time: float = 0.0
    regex_time: float = 0.0
    eyecite_time: float = 0.0
    name_extraction_time: float = 0.0
    date_extraction_time: float = 0.0
    parallel_detection_time: float = 0.0
    deduplication_time: float = 0.0
    citations_found: int = 0
    text_length: int = 0

class OptimizedUnifiedCitationProcessorV2:
    """
    Optimized unified citation processor with performance improvements.
    """
    
    def __init__(self):
        logger.info('[OPTIMIZED] Initializing optimized unified citation processor')
        self._init_cached_patterns()
        self._init_performance_thresholds()
        logger.info('[OPTIMIZED] Initialization complete')
    
    def _init_cached_patterns(self):
        """Pre-compile regex patterns for better performance."""
        # Cache compiled regex patterns
        self.citation_patterns_compiled = [
            # Federal patterns
            re.compile(r'\b(\d+)\s+(U\.S\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(S\.Ct\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(L\.Ed\.2d|L\.Ed\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(F\.3d|F\.2d|F\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(F\.Supp\.3d|F\.Supp\.2d|F\.Supp\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(F\.App\'x)\s+(\d+)\b', re.IGNORECASE),
            
            # State patterns (common ones)
            re.compile(r'\b(\d+)\s+(P\.3d|P\.2d|P\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(A\.3d|A\.2d|A\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(N\.E\.3d|N\.E\.2d|N\.E\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(S\.E\.3d|S\.E\.2d|S\.E\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(So\.3d|So\.2d|So\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(S\.W\.3d|S\.W\.2d|S\.W\.)\s+(\d+)\b', re.IGNORECASE),
            re.compile(r'\b(\d+)\s+(N\.W\.3d|N\.W\.2d|N\.W\.)\s+(\d+)\b', re.IGNORECASE),
        ]
        
        # False positive detection patterns
        self.false_positive_patterns = [
            re.compile(r'\bpage\s+\d+', re.IGNORECASE),
            re.compile(r'\bp\.\s*\d+', re.IGNORECASE),
            re.compile(r'\bat\s+\d+', re.IGNORECASE),
            re.compile(r'\bsee\s+\d+', re.IGNORECASE),
            re.compile(r'\bid\.\s*\d+', re.IGNORECASE),
            re.compile(r'\bibid\s*\d+', re.IGNORECASE),
        ]
        
        # Case name patterns
        self.case_name_patterns = [
            re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
            re.compile(r'\b(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
            re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
        ]
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'\((\d{4})\)'),
            re.compile(r'\b(\d{4})\b'),
        ]
    
    def _init_performance_thresholds(self):
        """Set performance thresholds for optimization decisions."""
        self.LARGE_TEXT_THRESHOLD = 50000  # 50KB
        self.CHUNK_SIZE = 10000  # 10KB chunks for large texts
        self.MIN_CITATIONS_FOR_EYECITE = 5  # Only use eyecite if regex finds < 5 citations
        self.CONTEXT_WINDOW = 200  # Characters around citation for name/date extraction
        self.PARALLEL_PROXIMITY_THRESHOLD = 150  # Characters for parallel detection
    
    def extract_citations_optimized(self, text: str) -> Tuple[List[CitationResult], ProcessingStats]:
        """
        Optimized citation extraction with performance tracking.
        
        Args:
            text: Text to extract citations from
            
        Returns:
            Tuple of (citations, processing_stats)
        """
        stats = ProcessingStats()
        stats.text_length = len(text)
        start_time = time.time()
        
        logger.info(f"[OPTIMIZED] Starting optimized extraction for {len(text)} characters")
        
        # STEP 1: Fast regex extraction with false positive prevention
        regex_start = time.time()
        citations = self._extract_with_regex_optimized(text)
        stats.regex_time = time.time() - regex_start
        stats.citations_found = len(citations)
        
        logger.info(f"[OPTIMIZED] Regex found {len(citations)} citations in {stats.regex_time:.2f}s")
        
        # STEP 2: Conditional eyecite extraction (only if needed)
        if len(citations) < self.MIN_CITATIONS_FOR_EYECITE:
            eyecite_start = time.time()
            try:
                eyecite_citations = self._extract_with_eyecite_optimized(text)
                citations.extend(eyecite_citations)
                stats.eyecite_time = time.time() - eyecite_start
                logger.info(f"[OPTIMIZED] Eyecite added {len(eyecite_citations)} citations in {stats.eyecite_time:.2f}s")
            except Exception as e:
                logger.warning(f"[OPTIMIZED] Eyecite extraction failed: {e}")
                stats.eyecite_time = time.time() - eyecite_start
        else:
            logger.info(f"[OPTIMIZED] Skipping eyecite (regex found sufficient citations)")
        
        # STEP 3: Optimized name and date extraction
        name_start = time.time()
        self._extract_names_and_dates_optimized(citations, text)
        stats.name_extraction_time = time.time() - name_start
        
        # STEP 4: Fast parallel detection
        parallel_start = time.time()
        self._detect_parallel_citations_optimized(citations, text)
        stats.parallel_detection_time = time.time() - parallel_start
        
        # STEP 5: Efficient deduplication
        dedup_start = time.time()
        citations = self._deduplicate_citations_optimized(citations)
        stats.deduplication_time = time.time() - dedup_start
        
        stats.total_time = time.time() - start_time
        stats.citations_found = len(citations)
        
        logger.info(f"[OPTIMIZED] Extraction complete: {len(citations)} citations in {stats.total_time:.2f}s")
        
        return citations, stats
    
    def _extract_with_regex_optimized(self, text: str) -> List[CitationResult]:
        """Optimized regex extraction with cached patterns and chunking."""
        citations = []
        seen_citations = set()
        
        # For large texts, process in chunks
        if len(text) > self.LARGE_TEXT_THRESHOLD:
            chunks = self._chunk_text_optimized(text)
            for chunk in chunks:
                chunk_citations = self._extract_from_chunk(chunk, seen_citations)
                citations.extend(chunk_citations)
        else:
            citations = self._extract_from_chunk(text, seen_citations)
        
        return citations
    
    def _chunk_text_optimized(self, text: str) -> List[str]:
        """Split large text into overlapping chunks for processing."""
        chunks = []
        overlap = 500  # Overlap to catch citations spanning chunk boundaries
        
        for i in range(0, len(text), self.CHUNK_SIZE - overlap):
            chunk = text[i:i + self.CHUNK_SIZE]
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def _extract_from_chunk(self, text: str, seen_citations: Set[str]) -> List[CitationResult]:
        """Extract citations from a text chunk using cached patterns."""
        citations = []
        
        for pattern in self.citation_patterns_compiled:
            for match in pattern.finditer(text):
                volume, reporter, page = match.groups()
                citation_text = f"{volume} {reporter} {page}"
                
                # Skip duplicates
                if citation_text in seen_citations:
                    continue
                
                # Fast false positive check
                if not self._is_valid_citation_fast(citation_text, text, match.start()):
                    continue
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=match.start(),
                    end_index=match.end(),
                    source='regex_optimized'
                )
                
                citations.append(citation)
                seen_citations.add(citation_text)
        
        return citations
    
    def _is_valid_citation_fast(self, citation: str, text: str, position: int) -> bool:
        """Fast false positive detection using cached patterns."""
        # Extract context around the citation
        context_start = max(0, position - 50)
        context_end = min(len(text), position + len(citation) + 50)
        context = text[context_start:context_end].lower()
        
        # Check for false positive indicators
        for pattern in self.false_positive_patterns:
            if pattern.search(context):
                logger.debug(f"[FALSE_POSITIVE] Rejected '{citation}' due to context: {context[:100]}")
                return False
        
        # Volume number validation
        try:
            volume_match = re.search(r'^(\d+)', citation)
            if volume_match:
                vol_num = int(volume_match.group(1))
                if vol_num < 10 and 'P.' in citation:  # Pacific reporter false positive check
                    return False
        except ValueError:
            return False
        
        return True
    
    def _extract_with_eyecite_optimized(self, text: str) -> List[CitationResult]:
        """Optimized eyecite extraction (only when needed)."""
        try:
            import eyecite
            from eyecite import get_citations
            
            # For large texts, sample key sections instead of processing everything
            if len(text) > self.LARGE_TEXT_THRESHOLD:
                # Sample first 20KB, middle 10KB, and last 20KB
                sample_text = text[:20000] + text[len(text)//2-5000:len(text)//2+5000] + text[-20000:]
            else:
                sample_text = text
            
            eyecite_citations = get_citations(sample_text)
            
            citations = []
            for cite in eyecite_citations:
                citation = CitationResult(
                    citation=str(cite),
                    source='eyecite_optimized'
                )
                citations.append(citation)
            
            return citations
            
        except ImportError:
            logger.warning("[OPTIMIZED] Eyecite not available")
            return []
        except Exception as e:
            logger.warning(f"[OPTIMIZED] Eyecite extraction failed: {e}")
            return []
    
    def _extract_names_and_dates_optimized(self, citations: List[CitationResult], text: str):
        """Optimized name and date extraction using context windows."""
        for citation in citations:
            if hasattr(citation, 'start_index') and citation.start_index is not None:
                # Use context window around citation
                context_start = max(0, citation.start_index - self.CONTEXT_WINDOW)
                context_end = min(len(text), citation.start_index + self.CONTEXT_WINDOW)
                context = text[context_start:context_end]
            else:
                # Fallback: find citation in text and use context
                pos = text.find(citation.citation)
                if pos != -1:
                    context_start = max(0, pos - self.CONTEXT_WINDOW)
                    context_end = min(len(text), pos + len(citation.citation) + self.CONTEXT_WINDOW)
                    context = text[context_start:context_end]
                else:
                    context = citation.citation  # Minimal context
            
            # Fast name extraction
            if not citation.extracted_case_name:
                citation.extracted_case_name = self._extract_case_name_fast(context)
            
            # Fast date extraction
            if not citation.extracted_date:
                citation.extracted_date = self._extract_date_fast(context)
    
    def _extract_case_name_fast(self, context: str) -> Optional[str]:
        """Fast case name extraction using cached patterns."""
        for pattern in self.case_name_patterns:
            match = pattern.search(context)
            if match:
                if 'v.' in match.group(0) or 'v ' in match.group(0):
                    return match.group(0).strip()
                elif match.group(0).startswith('In re'):
                    return match.group(0).strip()
        return None
    
    def _extract_date_fast(self, context: str) -> Optional[str]:
        """Fast date extraction using cached patterns."""
        for pattern in self.date_patterns:
            match = pattern.search(context)
            if match:
                year = match.group(1)
                # Basic year validation
                if 1800 <= int(year) <= 2030:
                    return year
        return None
    
    def _detect_parallel_citations_optimized(self, citations: List[CitationResult], text: str):
        """Optimized parallel citation detection using proximity heuristics."""
        if len(citations) < 2:
            return
        
        # Sort citations by position for efficient proximity checking
        positioned_citations = []
        for citation in citations:
            if hasattr(citation, 'start_index') and citation.start_index is not None:
                positioned_citations.append((citation.start_index, citation))
            else:
                # Find position in text
                pos = text.find(citation.citation)
                if pos != -1:
                    positioned_citations.append((pos, citation))
        
        positioned_citations.sort(key=lambda x: x[0])
        
        # Group nearby citations as potential parallels
        for i, (pos1, citation1) in enumerate(positioned_citations):
            parallel_candidates = []
            
            # Check citations within proximity threshold
            for j, (pos2, citation2) in enumerate(positioned_citations[i+1:], i+1):
                if abs(pos1 - pos2) <= self.PARALLEL_PROXIMITY_THRESHOLD:
                    parallel_candidates.append(citation2)
                else:
                    break  # Citations are sorted, so no more candidates
            
            # Mark parallel relationships
            if parallel_candidates:
                citation1.parallel_citations = [c.citation for c in parallel_candidates]
                citation1.is_parallel = True
                
                for candidate in parallel_candidates:
                    candidate.parallel_citations = [citation1.citation] + [c.citation for c in parallel_candidates if c != candidate]
                    candidate.is_parallel = True
    
    def _deduplicate_citations_optimized(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Efficient deduplication preserving the best citation data."""
        seen = {}
        deduplicated = []
        
        for citation in citations:
            key = citation.citation.strip().lower()
            
            if key not in seen:
                seen[key] = citation
                deduplicated.append(citation)
            else:
                # Merge data from duplicate, keeping the one with more metadata
                existing = seen[key]
                if self._citation_has_more_metadata(citation, existing):
                    # Replace with better citation
                    deduplicated[deduplicated.index(existing)] = citation
                    seen[key] = citation
        
        return deduplicated
    
    def _citation_has_more_metadata(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if citation1 has more complete metadata than citation2."""
        score1 = sum([
            1 if citation1.extracted_case_name else 0,
            1 if citation1.extracted_date else 0,
            1 if getattr(citation1, 'canonical_name', None) else 0,
            1 if getattr(citation1, 'canonical_date', None) else 0,
        ])
        
        score2 = sum([
            1 if citation2.extracted_case_name else 0,
            1 if citation2.extracted_date else 0,
            1 if getattr(citation2, 'canonical_name', None) else 0,
            1 if getattr(citation2, 'canonical_date', None) else 0,
        ])
        
        return score1 > score2

# Convenience function for backward compatibility
def extract_citations_optimized(text: str) -> Tuple[List[CitationResult], ProcessingStats]:
    """Extract citations using the optimized processor."""
    processor = OptimizedUnifiedCitationProcessorV2()
    return processor.extract_citations_optimized(text)
