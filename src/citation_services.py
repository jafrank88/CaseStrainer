"""
CitationServices Module for CaseStrainer
Enhanced citation extraction, validation, and processing capabilities

NOTE: This module is primarily used for reference and testing.
The main application uses UnifiedCitationProcessorV2 for production citation processing.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import warnings

logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """Configuration for citation extraction"""
    extract_case_names: bool = True
    extract_years: bool = True
    extract_courts: bool = True
    extract_reporters: bool = True
    include_parallel_citations: bool = True
    resolve_ambiguous_citations: bool = True
    enable_context_analysis: bool = True
    ocr_error_correction: bool = False
    min_confidence_threshold: float = 0.7
    extract_pinpoint_citations: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)


class CitationSpan(NamedTuple):
    """Represents the position of a citation in text"""
    start: int
    end: int


class CitationResult:
    """Represents a single extracted citation with all metadata"""
    
    def __init__(self, raw_text: str, span: CitationSpan, confidence_score: float = 0.0):
        self.raw_text = raw_text
        self.span = span
        self.confidence_score = confidence_score
        
        # Core citation components
        self.case_name = ""
        self.year = None
        self.court = ""
        self.reporter = ""
        self.volume = ""
        self.page = ""
        self.pinpoint = ""
        
        # Additional metadata
        self.citation_type = "unknown"
        self.parallel_citations = []
        self.context = ""
        self.errors = []
        self.warnings = []
        
    def get_bluebook_format(self) -> str:
        """Generate Bluebook formatted citation"""
        parts = []
        
        if self.case_name:
            parts.append(self.case_name)
        
        if self.year:
            parts.append(str(self.year))
        
        if self.reporter and self.volume and self.page:
            parts.append(f"{self.volume} {self.reporter} {self.page}")
        
        if self.pinpoint:
            parts.append(f"at {self.pinpoint}")
        
        return ", ".join(parts) if parts else self.raw_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'raw_text': self.raw_text,
            'span': (self.span.start, self.span.end),
            'confidence_score': self.confidence_score,
            'case_name': self.case_name,
            'year': self.year,
            'court': self.court,
            'reporter': self.reporter,
            'volume': self.volume,
            'page': self.page,
            'pinpoint': self.pinpoint,
            'citation_type': self.citation_type,
            'parallel_citations': self.parallel_citations,
            'context': self.context,
            'errors': self.errors,
            'warnings': self.warnings
        }


class ValidationResult:
    """Result of citation validation"""
    
    def __init__(self):
        self.is_valid = False
        self.likely_valid = False
        self.ambiguous = False
        self.suggestions = []
        self.alternatives = []
        self.confidence = 0.0
        self.warnings = []


class CitationServices:
    """Enhanced citation extraction and processing service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_patterns()
        self._load_court_data()
        self._load_reporter_data()
    
    def _load_patterns(self):
        """Load regex patterns for citation extraction"""
        # Enhanced case name patterns - more flexible
        self.case_name_patterns = [
            # Standard v. format
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            # vs. format
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+vs\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            # et al. format
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.\b',
            # & format
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+&\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            # Parenthetical format
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\)\b',
            # Simple case name (for cases without clear v. format)
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})\b'
        ]
        
        # Year patterns - more comprehensive
        self.year_patterns = [
            r'\b(19[0-9]{2}|20[0-2][0-9])\b',
            r'\b(19[0-9]{2}|20[0-2][0-9])\s*\([A-Za-z]+\)\b',
            r'\b(19[0-9]{2}|20[0-2][0-9])\s*WL\b'  # Westlaw format
        ]
        
        # Enhanced reporter patterns - more comprehensive
        self.reporter_patterns = [
            # Federal reporters
            r'\b(\d+)\s+(U\.?S\.?|S\.?Ct\.?|L\.?Ed\.?|L\.?Ed\.?2d)\s+(\d+)\b',
            r'\b(\d+)\s+(F\.?|F\.?2d|F\.?3d|F\.?Supp\.?|F\.?Supp\.?2d)\s+(\d+)\b',
            # Regional reporters
            r'\b(\d+)\s+(A\.?2d|A\.?3d|A\.?4d)\s+(\d+)\b',
            r'\b(\d+)\s+(P\.?|P\.?2d|P\.?3d)\s+(\d+)\b',
            r'\b(\d+)\s+(N\.?E\.?|N\.?E\.?2d|N\.?E\.?3d)\s+(\d+)\b',
            r'\b(\d+)\s+(S\.?E\.?|S\.?E\.?2d)\s+(\d+)\b',
            r'\b(\d+)\s+(S\.?W\.?|S\.?W\.?2d|S\.?W\.?3d)\s+(\d+)\b',
            r'\b(\d+)\s+(N\.?W\.?|N\.?W\.?2d)\s+(\d+)\b',
            # State-specific reporters
            r'\b(\d+)\s+(Cal\.?|Cal\.?2d|Cal\.?3d|Cal\.?4th)\s+(\d+)\b',
            r'\b(\d+)\s+(Wash\.?|Wash\.?2d)\s+(\d+)\b',
            # Westlaw citations
            r'\b(20[0-2][0-9])\s+(WL)\s+(\d+)\b',
            # Lexis citations
            r'\b(20[0-2][0-9])\s+(U\.?S\.?\s+LEXIS)\s+(\d+)\b'
        ]
        
        # Court patterns - more comprehensive
        self.court_patterns = [
            r'\b(U\.?S\.?\s+Supreme\s+Court|Supreme\s+Court\s+of\s+the\s+United\s+States)\b',
            r'\b(U\.?S\.?\s+Court\s+of\s+Appeals|Circuit\s+Court)\b',
            r'\b(U\.?S\.?\s+District\s+Court|District\s+Court)\b',
            r'\b(Supreme\s+Court\s+of\s+[A-Za-z\s]+)\b',
            r'\b(Court\s+of\s+Appeals\s+of\s+[A-Za-z\s]+)\b',
            r'\b(Superior\s+Court\s+of\s+[A-Za-z\s]+)\b',
            r'\b([A-Za-z\s]+Supreme\s+Court)\b',
            r'\b([A-Za-z\s]+Court\s+of\s+Appeals)\b'
        ]
        
        # Pinpoint citation patterns
        self.pinpoint_patterns = [
            r'\bat\s+(\d+)\b',
            r'\bpage\s+(\d+)\b',
            r'\bp\.\s*(\d+)\b',
            r'\bpp\.\s*(\d+)\s*-\s*(\d+)\b'
        ]
    
    def _load_court_data(self):
        """Load court hierarchy and jurisdiction data"""
        self.court_hierarchy = {
            'federal': {
                'supreme': ['U.S. Supreme Court', 'Supreme Court of the United States'],
                'appellate': ['U.S. Court of Appeals', 'Circuit Court'],
                'district': ['U.S. District Court', 'District Court']
            },
            'state': {
                'supreme': ['Supreme Court'],
                'appellate': ['Court of Appeals', 'Appellate Court'],
                'superior': ['Superior Court', 'Circuit Court'],
                'municipal': ['Municipal Court', 'City Court']
            }
        }
    
    def _load_reporter_data(self):
        """Load reporter information and abbreviations"""
        self.reporter_data = {
            'U.S.': {'name': 'United States Reports', 'type': 'federal', 'level': 'supreme'},
            'S.Ct.': {'name': 'Supreme Court Reporter', 'type': 'federal', 'level': 'supreme'},
            'L.Ed.': {'name': 'Lawyers Edition', 'type': 'federal', 'level': 'supreme'},
            'L.Ed.2d': {'name': 'Lawyers Edition, Second Series', 'type': 'federal', 'level': 'supreme'},
            'F.': {'name': 'Federal Reporter', 'type': 'federal', 'level': 'appellate'},
            'F.2d': {'name': 'Federal Reporter, Second Series', 'type': 'federal', 'level': 'appellate'},
            'F.3d': {'name': 'Federal Reporter, Third Series', 'type': 'federal', 'level': 'appellate'},
            'F.Supp.': {'name': 'Federal Supplement', 'type': 'federal', 'level': 'district'},
            'F.Supp.2d': {'name': 'Federal Supplement, Second Series', 'type': 'federal', 'level': 'district'},
            'A.2d': {'name': 'Atlantic Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'A.3d': {'name': 'Atlantic Reporter, Third Series', 'type': 'state', 'level': 'appellate'},
            'A.4d': {'name': 'Atlantic Reporter, Fourth Series', 'type': 'state', 'level': 'appellate'},
            'P.': {'name': 'Pacific Reporter', 'type': 'state', 'level': 'appellate'},
            'P.2d': {'name': 'Pacific Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'P.3d': {'name': 'Pacific Reporter, Third Series', 'type': 'state', 'level': 'appellate'},
            'N.E.': {'name': 'Northeastern Reporter', 'type': 'state', 'level': 'appellate'},
            'N.E.2d': {'name': 'Northeastern Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'N.E.3d': {'name': 'Northeastern Reporter, Third Series', 'type': 'state', 'level': 'appellate'},
            'S.E.': {'name': 'Southeastern Reporter', 'type': 'state', 'level': 'appellate'},
            'S.E.2d': {'name': 'Southeastern Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'S.W.': {'name': 'Southwestern Reporter', 'type': 'state', 'level': 'appellate'},
            'S.W.2d': {'name': 'Southwestern Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'S.W.3d': {'name': 'Southwestern Reporter, Third Series', 'type': 'state', 'level': 'appellate'},
            'N.W.': {'name': 'Northwestern Reporter', 'type': 'state', 'level': 'appellate'},
            'N.W.2d': {'name': 'Northwestern Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'Cal.': {'name': 'California Reporter', 'type': 'state', 'level': 'appellate'},
            'Cal.2d': {'name': 'California Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'Cal.3d': {'name': 'California Reporter, Third Series', 'type': 'state', 'level': 'appellate'},
            'Cal.4th': {'name': 'California Reporter, Fourth Series', 'type': 'state', 'level': 'appellate'},
            'Wash.': {'name': 'Washington Reporter', 'type': 'state', 'level': 'appellate'},
            'Wash.2d': {'name': 'Washington Reporter, Second Series', 'type': 'state', 'level': 'appellate'},
            'WL': {'name': 'Westlaw', 'type': 'online', 'level': 'various'},
            'U.S. LEXIS': {'name': 'LexisNexis', 'type': 'online', 'level': 'various'}
        }
    
    def extract_citations(self, text: str, config: ExtractionConfig = None) -> List[CitationResult]:
        """Extract citations from text using enhanced patterns"""
        if config is None:
            config = ExtractionConfig()
        
        self.logger.info(f"Extracting citations from text ({len(text)} characters)")
        
        citations = []
        
        # Find potential citation spans
        citation_spans = self._find_citation_spans(text, config)
        
        for span in citation_spans:
            try:
                citation = self._extract_citation_from_span(text, span, config)
                if citation and citation.confidence_score >= config.min_confidence_threshold:
                    citations.append(citation)
            except Exception as e:
                self.logger.warning(f"Error extracting citation from span {span}: {e}")
        
        self.logger.info(f"Extracted {len(citations)} citations")
        return citations
    
    def _find_citation_spans(self, text: str, config: ExtractionConfig) -> List[CitationSpan]:
        """Find potential citation spans in text"""
        spans = []
        
        # Look for patterns that indicate citations
        citation_indicators = [
            r'\b\d+\s+[A-Z]\.?\s+\d+\b',  # Volume Reporter Page
            r'\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+\b',  # Case v. Case
            r'\b[A-Z][a-z]+\s+vs\.\s+[A-Z][a-z]+\b',  # Case vs. Case
            r'\b[A-Z][a-z]+\s+et\s+al\.\b',  # Case et al.
            r'\b[A-Z][a-z]+\s+&\s+[A-Z][a-z]+\b',  # Case & Case
            r'\b\d{4}\s+WL\s+\d+\b',  # Westlaw citations
            r'\b\d{4}\s+U\.?S\.?\s+LEXIS\s+\d+\b',  # Lexis citations
            r'\b\d{4}\s+WL\s+\d+\b',  # Westlaw citations (duplicate for emphasis)
        ]
        
        for pattern in citation_indicators:
            for match in re.finditer(pattern, text):
                # Expand span to include context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                spans.append(CitationSpan(start, end))
        
        # Remove overlapping spans
        spans = self._remove_overlapping_spans(spans)
        return spans
    
    def _remove_overlapping_spans(self, spans: List[CitationSpan]) -> List[CitationSpan]:
        """Remove overlapping spans, keeping the most specific ones"""
        if not spans:
            return spans
        
        # Sort by start position
        spans = sorted(spans, key=lambda x: x.start)
        
        non_overlapping = [spans[0]]
        for span in spans[1:]:
            last_span = non_overlapping[-1]
            
            # Check if spans overlap
            if span.start <= last_span.end:
                # Merge overlapping spans
                non_overlapping[-1] = CitationSpan(
                    min(last_span.start, span.start),
                    max(last_span.end, span.end)
                )
            else:
                non_overlapping.append(span)
        
        return non_overlapping
    
    def _extract_citation_from_span(self, text: str, span: CitationSpan, config: ExtractionConfig) -> Optional[CitationResult]:
        """Extract citation data from a specific text span"""
        span_text = text[span.start:span.end]
        
        # Create citation result
        citation = CitationResult(span_text, span)
        
        # Extract components based on config
        if config.extract_case_names:
            self._extract_case_name(citation, span_text)
        
        if config.extract_years:
            self._extract_year(citation, span_text)
        
        if config.extract_reporters:
            self._extract_reporter_info(citation, span_text)
        
        if config.extract_courts:
            self._extract_court(citation, span_text)
        
        if config.extract_pinpoint_citations:
            self._extract_pinpoint(citation, span_text)
        
        # Calculate confidence score
        citation.confidence_score = self._calculate_confidence(citation, config)
        
        # Determine citation type
        citation.citation_type = self._determine_citation_type(citation)
        
        # Extract context
        if config.enable_context_analysis:
            citation.context = self._extract_context(text, span)
        
        return citation
    
    def _extract_case_name(self, citation: CitationResult, text: str):
        """Extract case name from text"""
        # First, try to find case names in the context around the citation
        # Look for patterns like "in Smith v. Jones," or "held in Doe v. Roe"
        context_patterns = [
            r'\b(in|held in|see|referenced in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b(in|held in|see|referenced in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+et\s+al\.)\b',
            r'\b(in|held in|see|referenced in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+&\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
        ]
        
        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                citation.case_name = match.group(2).strip()
                return
        
        # Fallback to direct pattern matching
        for pattern in self.case_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'v.' in pattern or 'vs.' in pattern:
                    # Plaintiff v. Defendant format
                    plaintiff = match.group(1).strip()
                    defendant = match.group(2).strip()
                    citation.case_name = f"{plaintiff} v. {defendant}"
                elif 'et al.' in pattern:
                    # Case et al. format
                    case_name = match.group(1).strip()
                    citation.case_name = f"{case_name} et al."
                elif '&' in pattern:
                    # Case & Case format
                    case1 = match.group(1).strip()
                    case2 = match.group(2).strip()
                    citation.case_name = f"{case1} & {case2}"
                else:
                    # Simple case name
                    citation.case_name = match.group(1).strip()
                break
    
    def _extract_year(self, citation: CitationResult, text: str):
        """Extract year from text"""
        for pattern in self.year_patterns:
            match = re.search(pattern, text)
            if match:
                year_str = match.group(1)
                try:
                    citation.year = int(year_str)
                    break
                except ValueError:
                    continue
    
    def _extract_reporter_info(self, citation: CitationResult, text: str):
        """Extract reporter, volume, and page information"""
        for pattern in self.reporter_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'WL' in pattern or 'LEXIS' in pattern:
                    # Online citation format (year, reporter, page)
                    citation.year = int(match.group(1))
                    citation.reporter = match.group(2)
                    citation.page = match.group(3)
                else:
                    # Traditional reporter format (volume, reporter, page)
                    citation.volume = match.group(1)
                    citation.reporter = match.group(2)
                    citation.page = match.group(3)
                break
    
    def _extract_court(self, citation: CitationResult, text: str):
        """Extract court information"""
        for pattern in self.court_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                citation.court = match.group(1)
                break
    
    def _extract_pinpoint(self, citation: CitationResult, text: str):
        """Extract pinpoint citation"""
        for pattern in self.pinpoint_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    citation.pinpoint = match.group(1)
                else:
                    citation.pinpoint = f"{match.group(1)}-{match.group(2)}"
                break
    
    def _calculate_confidence(self, citation: CitationResult, config: ExtractionConfig) -> float:
        """Calculate confidence score for citation extraction"""
        score = 0.0
        max_score = 0.0
        
        # Case name confidence (30%)
        if citation.case_name:
            score += 0.3
            # Check for common case name patterns
            if 'v.' in citation.case_name or 'vs.' in citation.case_name:
                score += 0.1
            # Check for reasonable length
            if 5 <= len(citation.case_name) <= 100:
                score += 0.05
        max_score += 0.45
        
        # Year confidence (20%)
        if citation.year:
            score += 0.2
            # Check if year is reasonable
            current_year = datetime.now().year
            if 1800 <= citation.year <= current_year:
                score += 0.1
        max_score += 0.3
        
        # Reporter confidence (35%)
        if citation.reporter and citation.volume and citation.page:
            score += 0.3
            # Check if reporter is known
            if citation.reporter in self.reporter_data:
                score += 0.1
            # Check if volume and page are numeric
            try:
                int(citation.volume)
                int(citation.page)
                score += 0.05
            except ValueError:
                pass
        max_score += 0.45
        
        # Court confidence (5%)
        if citation.court:
            score += 0.05
        max_score += 0.05
        
        # Format validation bonus (10%)
        if self._validate_citation_format(citation):
            score += 0.1
        max_score += 0.1
        
        return score / max_score if max_score > 0 else 0.0
    
    def _validate_citation_format(self, citation: CitationResult) -> bool:
        """Validate that the citation follows expected format"""
        # Check if we have the minimum required components
        has_reporter = bool(citation.reporter)
        has_volume = bool(citation.volume)
        has_page = bool(citation.page)
        
        # For traditional citations, need reporter, volume, and page
        if has_reporter and has_volume and has_page:
            return True
        
        # For online citations (WL, LEXIS), need year and page
        if citation.reporter in ['WL', 'U.S. LEXIS'] and citation.year and citation.page:
            return True
        
        return False
    
    def _determine_citation_type(self, citation: CitationResult) -> str:
        """Determine the type of citation"""
        if citation.reporter in self.reporter_data:
            reporter_info = self.reporter_data[citation.reporter]
            if reporter_info['type'] == 'federal':
                if reporter_info['level'] == 'supreme':
                    return 'federal_supreme'
                elif reporter_info['level'] == 'appellate':
                    return 'federal_appellate'
                else:
                    return 'federal_district'
            elif reporter_info['type'] == 'online':
                return 'online'
            else:
                return 'state'
        
        if citation.court:
            court_lower = citation.court.lower()
            if 'supreme' in court_lower:
                return 'supreme_court'
            elif 'appellate' in court_lower or 'appeals' in court_lower:
                return 'appellate_court'
            elif 'district' in court_lower:
                return 'district_court'
        
        return 'unknown'
    
    def _extract_context(self, full_text: str, span: CitationSpan) -> str:
        """Extract context around citation (DEPRECATED: use isolation-aware logic instead)"""
        warnings.warn(
            "_extract_context is deprecated. Use isolation-aware extraction instead.",
            DeprecationWarning,
            stacklevel=2
        )
        context_start = max(0, span.start - 100)
        context_end = min(len(full_text), span.end + 100)
        context = full_text[context_start:context_end]
        # Clean up context
        context = re.sub(r'\s+', ' ', context).strip()
        return context
    
    def validate_citation(self, citation: CitationResult) -> ValidationResult:
        """Validate a citation against known patterns and databases"""
        result = ValidationResult()
        
        # Basic validation checks
        if not citation.case_name:
            result.suggestions.append("Missing case name")
        
        if not citation.year:
            result.suggestions.append("Missing year")
        
        if not citation.reporter:
            result.suggestions.append("Missing reporter")
        
        if not citation.volume or not citation.page:
            result.suggestions.append("Missing volume or page")
        
        # Check if reporter is known
        if citation.reporter and citation.reporter not in self.reporter_data:
            result.warnings.append(f"Unknown reporter: {citation.reporter}")
        
        # Format validation
        if not self._validate_citation_format(citation):
            result.suggestions.append("Invalid citation format")
        
        # Determine validity
        if len(result.suggestions) == 0 and len(result.warnings) == 0:
            result.is_valid = True
            result.confidence = 0.9
        elif len(result.suggestions) <= 1:
            result.likely_valid = True
            result.confidence = 0.7
        else:
            result.confidence = 0.3
        
        return result
    
    def get_citation_statistics(self, citations: List[CitationResult]) -> Dict[str, Any]:
        """Generate statistics for a list of citations"""
        if not citations:
            return {'total': 0}
        
        stats = {
            'total': len(citations),
            'valid_count': 0,
            'invalid_count': 0,
            'average_confidence': 0.0,
            'citation_types': {},
            'reporters': {},
            'years': {},
            'courts': {}
        }
        
        total_confidence = 0.0
        
        for citation in citations:
            # Count valid/invalid
            if citation.confidence_score >= 0.7:
                stats['valid_count'] += 1
            else:
                stats['invalid_count'] += 1
            
            # Accumulate confidence
            total_confidence += citation.confidence_score
            
            # Count citation types
            cite_type = citation.citation_type
            stats['citation_types'][cite_type] = stats['citation_types'].get(cite_type, 0) + 1
            
            # Count reporters
            if citation.reporter:
                stats['reporters'][citation.reporter] = stats['reporters'].get(citation.reporter, 0) + 1
            
            # Count years
            if citation.year:
                stats['years'][citation.year] = stats['years'].get(citation.year, 0) + 1
            
            # Count courts
            if citation.court:
                stats['courts'][citation.court] = stats['courts'].get(citation.court, 0) + 1
        
        stats['average_confidence'] = total_confidence / len(citations)
        
        return stats 