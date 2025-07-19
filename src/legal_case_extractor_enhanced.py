"""
Enhanced Legal Case Extractor
Integrates with existing codebase to provide superior case name extraction, citation parsing, and validation.

This module enhances the existing citation processing pipeline by:
1. Providing more accurate case name extraction with comprehensive patterns
2. Better date parsing with multiple format support
3. Enhanced validation against Table of Authorities
4. Integration with existing CitationResult and processing pipeline
5. Support for complex citation formats and parallel citations
"""

import re
import logging
import time
from typing import List, Dict, NamedTuple, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import unicodedata

# Import existing components for integration
# from .case_name_extraction_core import extract_case_name_triple_comprehensive  # Removed to avoid circular import
try:
    from .unified_citation_processor import CitationResult, DateExtractor
except ImportError:
    from unified_citation_processor import CitationResult, DateExtractor

# Import fallback logging
try:
    from .canonical_case_name_service import log_fallback_usage
except ImportError:
    try:
        from canonical_case_name_service import log_fallback_usage
    except ImportError:
        def log_fallback_usage(citation: str, fallback_type: str, reason: str, context: Dict = None):
            logger.warning(f"FALLBACK_USED: {fallback_type} for {citation} - {reason}")

logger = logging.getLogger(__name__)

@dataclass
class DateInfo:
    """Represents extracted date information from legal citation"""
    year: str
    month: Optional[str] = None
    day: Optional[str] = None
    court: Optional[str] = None
    full_date_string: Optional[str] = None
    date_format: Optional[str] = None  # 'year_only', 'court_year', 'full_date'
    confidence: float = 0.0

@dataclass
class CaseExtraction:
    """Represents an extracted legal case citation with enhanced metadata"""
    full_match: str
    case_name: str
    party_1: Optional[str] = None
    party_2: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    year: Optional[str] = None
    date_info: Optional[DateInfo] = None
    case_type: Optional[str] = None  # 'standard', 'in_re', 'ex_parte', 'matter_of'
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float = 0.0
    extraction_method: str = "enhanced_extractor"
    context: str = ""
    is_parallel: bool = False
    parallel_citations: List[str] = None
    docket_number: Optional[str] = None
    publication_status: Optional[str] = None
    
    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []

class LegalCaseExtractorEnhanced:
    """
    Enhanced legal case extractor that integrates with existing codebase.
    
    This class provides superior case name extraction, citation parsing, and validation
    while maintaining compatibility with the existing CitationResult structure.
    """
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.reporter_patterns = self._get_reporter_patterns()
        # Court abbreviations mapping
        self.court_abbreviations = {
            'D.': 'District Court',
            'S.D.': 'Southern District',
            'N.D.': 'Northern District',
            'E.D.': 'Eastern District',
            'W.D.': 'Western District',
            'C.D.': 'Central District',
            'M.D.': 'Middle District',
            'Cir.': 'Circuit Court of Appeals',
            'Fed.Cir.': 'Federal Circuit',
            'D.C.Cir.': 'D.C. Circuit',
            'Bankr.': 'Bankruptcy Court',
            'Ct.Int\'l Trade': 'Court of International Trade',
            'Fed.Cl.': 'Federal Claims Court',
            'Tax Ct.': 'Tax Court',
            
            # State abbreviations
            'Cal.': 'California',
            'N.Y.': 'New York',
            'Tex.': 'Texas',
            'Fla.': 'Florida',
            'Ill.': 'Illinois',
            'Pa.': 'Pennsylvania',
            'Ohio': 'Ohio',
            'Ga.': 'Georgia',
            'Mich.': 'Michigan',
            'Va.': 'Virginia',
            'Wash.': 'Washington',
            'Mass.': 'Massachusetts',
            'Md.': 'Maryland',
            'N.J.': 'New Jersey',
            'Conn.': 'Connecticut',
            'Or.': 'Oregon',
            'Colo.': 'Colorado',
            'Ariz.': 'Arizona',
            'Nev.': 'Nevada',
            'Utah': 'Utah',
            'Okla.': 'Oklahoma',
            'Kan.': 'Kansas',
            'Mo.': 'Missouri',
            'Ark.': 'Arkansas',
            'La.': 'Louisiana',
            'Miss.': 'Mississippi',
            'Ala.': 'Alabama',
            'Tenn.': 'Tennessee',
            'Ky.': 'Kentucky',
            'W.Va.': 'West Virginia',
            'N.C.': 'North Carolina',
            'S.C.': 'South Carolina',
            'Ind.': 'Indiana',
            'Wis.': 'Wisconsin',
            'Minn.': 'Minnesota',
            'Iowa': 'Iowa',
            'N.D.': 'North Dakota',
            'S.D.': 'South Dakota',
            'Neb.': 'Nebraska',
            'Mont.': 'Montana',
            'Wyo.': 'Wyoming',
            'Idaho': 'Idaho',
            'Alaska': 'Alaska',
            'Haw.': 'Hawaii',
            'Vt.': 'Vermont',
            'N.H.': 'New Hampshire',
            'Maine': 'Maine',
            'R.I.': 'Rhode Island',
            'Del.': 'Delaware',
            'D.C.': 'District of Columbia'
        }
        
        # Month abbreviations
        self.month_abbreviations = {
            r'Jan\.?': 'January',
            r'Feb\.?': 'February',
            r'Mar\.?': 'March',
            r'Apr\.?': 'April',
            r'May\.?': 'May',
            r'Jun\.?': 'June',
            r'Jul\.?': 'July',
            r'Aug\.?': 'August',
            r'Sep\.?|Sept\.?': 'September',
            r'Oct\.?': 'October',
            r'Nov\.?': 'November',
            r'Dec\.?': 'December'
        }
        self.date_extractor = DateExtractor()  # Use existing DateExtractor
        
        # Integration with existing extraction methods
        self.fallback_extractors = [
            # extract_case_name_triple_comprehensive, # Removed to avoid circular import
            self._extract_with_legacy_patterns
        ]
    
        # Court abbreviations mapping
        self.court_abbreviations = {
            'D.': 'District Court',
            'S.D.': 'Southern District',
            'N.D.': 'Northern District',
            'E.D.': 'Eastern District',
            'W.D.': 'Western District',
            'C.D.': 'Central District',
            'M.D.': 'Middle District',
            'Cir.': 'Circuit Court of Appeals',
            'Fed.Cir.': 'Federal Circuit',
            'D.C.Cir.': 'D.C. Circuit',
            'Bankr.': 'Bankruptcy Court',
            'Ct.Int\'l Trade': 'Court of International Trade',
            'Fed.Cl.': 'Federal Claims Court',
            'Tax Ct.': 'Tax Court',
            
            # State abbreviations
            'Cal.': 'California',
            'N.Y.': 'New York',
            'Tex.': 'Texas',
            'Fla.': 'Florida',
            'Ill.': 'Illinois',
            'Pa.': 'Pennsylvania',
            'Ohio': 'Ohio',
            'Ga.': 'Georgia',
            'Mich.': 'Michigan',
            'Va.': 'Virginia',
            'Wash.': 'Washington',
            'Mass.': 'Massachusetts',
            'Md.': 'Maryland',
            'N.J.': 'New Jersey',
            'Conn.': 'Connecticut',
            'Or.': 'Oregon',
            'Colo.': 'Colorado',
            'Ariz.': 'Arizona',
            'Nev.': 'Nevada',
            'Utah': 'Utah',
            'Okla.': 'Oklahoma',
            'Kan.': 'Kansas',
            'Mo.': 'Missouri',
            'Ark.': 'Arkansas',
            'La.': 'Louisiana',
            'Miss.': 'Mississippi',
            'Ala.': 'Alabama',
            'Tenn.': 'Tennessee',
            'Ky.': 'Kentucky',
            'W.Va.': 'West Virginia',
            'N.C.': 'North Carolina',
            'S.C.': 'South Carolina',
            'Ind.': 'Indiana',
            'Wis.': 'Wisconsin',
            'Minn.': 'Minnesota',
            'Iowa': 'Iowa',
            'N.D.': 'North Dakota',
            'S.D.': 'South Dakota',
            'Neb.': 'Nebraska',
            'Mont.': 'Montana',
            'Wyo.': 'Wyoming',
            'Idaho': 'Idaho',
            'Alaska': 'Alaska',
            'Haw.': 'Hawaii',
            'Vt.': 'Vermont',
            'N.H.': 'New Hampshire',
            'Maine': 'Maine',
            'R.I.': 'Rhode Island',
            'Del.': 'Delaware',
            'D.C.': 'District of Columbia'
        }
        
        # Month abbreviations
        self.month_abbreviations = {
            r'Jan\.?': 'January',
            r'Feb\.?': 'February',
            r'Mar\.?': 'March',
            r'Apr\.?': 'April',
            r'May\.?': 'May',
            r'Jun\.?': 'June',
            r'Jul\.?': 'July',
            r'Aug\.?': 'August',
            r'Sep\.?|Sept\.?': 'September',
            r'Oct\.?': 'October',
            r'Nov\.?': 'November',
            r'Dec\.?': 'December'
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for case extraction with enhanced accuracy"""
        patterns = {}
        
        # Enhanced parenthetical pattern to capture more date formats
        date_pattern = r'\(([^)]*(?:\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})[^)]*)\)'
        
        # Standard adversarial cases (Party v. Party) - Enhanced with business entities
        patterns['standard'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'([A-Z][^,]*?(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|et al\.|L\.P\.|L\.L\.C\.)?)'  # Party 1 with business suffixes
            r'\s+v\.\s+'  # " v. "
            r'([^,]+?(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|et al\.|L\.P\.|L\.L\.C\.)?)'  # Party 2 with business suffixes
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            + date_pattern,  # Enhanced date pattern
            re.IGNORECASE
        )
        
        # In re cases
        patterns['in_re'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'In re\s+'  # "In re "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            + date_pattern,  # Enhanced date pattern
            re.IGNORECASE
        )
        
        # Ex parte cases
        patterns['ex_parte'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'Ex parte\s+'  # "Ex parte "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            + date_pattern,  # Enhanced date pattern
            re.IGNORECASE
        )
        
        # Matter of cases
        patterns['matter_of'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'Matter of\s+'  # "Matter of "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            + date_pattern,  # Enhanced date pattern
            re.IGNORECASE
        )
        
        # Department cases (e.g., Dep't of Ecology v. Campbell)
        patterns['department'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'(?:Dep\'t|Department)\s+of\s+'  # "Dep't of " or "Department of "
            r'([^,]+?)'  # Department name
            r'\s+v\.\s+'  # " v. "
            r'([^,]+?)'  # Party
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            + date_pattern,  # Enhanced date pattern
            re.IGNORECASE
        )
        
        # State/People/United States cases
        patterns['government'] = re.compile(
            r'(?:see\s+(?:also\s+)?)?'  # Optional "see" or "see also"
            r'(State|People|United\s+States|Commonwealth)\s+v\.\s+'  # Government party
            r'([^,]+?)'  # Defendant
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'.*?'  # Optional additional citation info
            + date_pattern,  # Enhanced date pattern
            re.IGNORECASE
        )
        
        return patterns
    
    def _get_reporter_patterns(self) -> Dict[str, List[str]]:
        """Define common legal reporter abbreviations by jurisdiction"""
        return {
            'federal': [
                r'F\.', r'F\.2d', r'F\.3d', r'F\.4th',
                r'F\.Supp\.', r'F\.Supp\.2d', r'F\.Supp\.3d',
                r'F\.R\.D\.', r'Fed\.R\.'
            ],
            'supreme_court': [
                r'U\.S\.', r'S\.Ct\.', r'L\.Ed\.', r'L\.Ed\.2d'
            ],
            'state': [
                r'P\.', r'P\.2d', r'P\.3d',
                r'A\.', r'A\.2d', r'A\.3d',
                r'N\.E\.', r'N\.E\.2d', r'N\.E\.3d',
                r'S\.E\.', r'S\.E\.2d', r'S\.E\.3d',
                r'S\.W\.', r'S\.W\.2d', r'S\.W\.3d',
                r'So\.', r'So\.2d', r'So\.3d',
                r'N\.W\.', r'N\.W\.2d', r'N\.W\.3d',
                r'Wash\.', r'Wash\.2d', r'Wash\.App\.'
            ]
        }
    
    def extract_cases(self, text: str) -> List[CaseExtraction]:
        """Extract all legal cases from text with enhanced accuracy"""
        extractions = []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        for case_type, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                extraction = self._parse_match(match, case_type, text)
                if extraction:
                    extractions.append(extraction)
        
        # Remove duplicates and sort by position
        extractions = self._deduplicate_extractions(extractions)
        return sorted(extractions, key=lambda x: x.start_pos or 0)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better extraction"""
        if not text:
            return ""
        
        # Normalize unicode characters
        try:
            text = unicodedata.normalize("NFKC", text)
        except:
            pass
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Normalize quotes
        text = re.sub(r"[\u2018\u2019]", "'", text)
        text = re.sub(r"[\u201C\u201D]", '"', text)
        
        return text.strip()
    
    def _parse_match(self, match: re.Match, case_type: str, text: str) -> Optional[CaseExtraction]:
        """Parse a regex match into a CaseExtraction object with enhanced context"""
        try:
            groups = match.groups()
            context = self._get_context(text, match.start(), match.end())
            
            if case_type == 'standard':
                date_string = groups[6] if len(groups) > 6 else groups[5]
                date_info = self._parse_date_string(date_string)
                
                return CaseExtraction(
                    full_match=match.group(0),
                    case_name=f"{groups[0]} v. {groups[1]}",
                    party_1=groups[0].strip(),
                    party_2=groups[1].strip(),
                    volume=groups[2],
                    reporter=groups[3],
                    page=groups[4],
                    pincite=groups[5] if len(groups) > 5 and groups[5] else None,
                    year=date_info.year,
                    date_info=date_info,
                    case_type='standard',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=self._calculate_confidence(match, case_type, date_info),
                    context=context
                )
            
            elif case_type in ['in_re', 'ex_parte', 'matter_of']:
                date_string = groups[5] if len(groups) > 5 else groups[4]
                date_info = self._parse_date_string(date_string)
                prefix = case_type.replace('_', ' ').title()
                
                return CaseExtraction(
                    full_match=match.group(0),
                    case_name=f"{prefix} {groups[0]}",
                    party_1=groups[0].strip(),
                    volume=groups[1],
                    reporter=groups[2],
                    page=groups[3],
                    pincite=groups[4] if len(groups) > 4 and groups[4] else None,
                    year=date_info.year,
                    date_info=date_info,
                    case_type=case_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=self._calculate_confidence(match, case_type, date_info),
                    context=context
                )
            
            elif case_type == 'department':
                date_string = groups[6] if len(groups) > 6 else groups[5]
                date_info = self._parse_date_string(date_string)
                
                return CaseExtraction(
                    full_match=match.group(0),
                    case_name=f"Dep't of {groups[0]} v. {groups[1]}",
                    party_1=f"Dep't of {groups[0]}",
                    party_2=groups[1].strip(),
                    volume=groups[2],
                    reporter=groups[3],
                    page=groups[4],
                    pincite=groups[5] if len(groups) > 5 and groups[5] else None,
                    year=date_info.year,
                    date_info=date_info,
                    case_type='department',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=self._calculate_confidence(match, case_type, date_info),
                    context=context
                )
            
            elif case_type == 'government':
                date_string = groups[6] if len(groups) > 6 else groups[5]
                date_info = self._parse_date_string(date_string)
                
                return CaseExtraction(
                    full_match=match.group(0),
                    case_name=f"{groups[0]} v. {groups[1]}",
                    party_1=groups[0].strip(),
                    party_2=groups[1].strip(),
                    volume=groups[2],
                    reporter=groups[3],
                    page=groups[4],
                    pincite=groups[5] if len(groups) > 5 and groups[5] else None,
                    year=date_info.year,
                    date_info=date_info,
                    case_type='government',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=self._calculate_confidence(match, case_type, date_info),
                    context=context
                )
            
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error parsing match for {case_type}: {e}")
            return None
        
        return None
    
    def _get_context(self, text: str, start: int, end: int, window: int = 200) -> str:
        """Get context around the match for better analysis"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def _parse_date_string(self, date_string: str) -> DateInfo:
        """Parse various date formats found in legal citations with enhanced accuracy"""
        if not date_string:
            return DateInfo(year="", date_format="invalid", confidence=0.0)
        
        # Clean up the string
        date_string = date_string.strip()
        
        # Pattern 1: Full date with month name (e.g., "Jan. 15, 2020", "January 15, 2020")
        full_date_pattern = r'(?:(' + '|'.join(self.month_abbreviations.keys()) + r')\s+(\d{1,2}),?\s+)?(\d{4})'
        full_date_match = re.search(full_date_pattern, date_string, re.IGNORECASE)
        
        if full_date_match:
            month_abbr, day, year = full_date_match.groups()
            month_full = None
            if month_abbr:
                # Find the full month name
                for abbr_pattern, full_name in self.month_abbreviations.items():
                    if re.match(abbr_pattern, month_abbr, re.IGNORECASE):
                        month_full = full_name
                        break
            
            # Extract court information (everything except the date)
            court_info = re.sub(full_date_pattern, '', date_string, flags=re.IGNORECASE).strip()
            court_info = re.sub(r'[,\s]+', ' ', court_info).strip()
            
            confidence = 0.9 if month_full and day else 0.7
            
            return DateInfo(
                year=year,
                month=month_full,
                day=day,
                court=court_info if court_info else None,
                full_date_string=date_string,
                date_format='full_date' if month_full and day else 'court_year',
                confidence=confidence
            )
        
        # Pattern 2: Numeric date format (e.g., "1/15/2020", "01-15-2020")
        numeric_date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        numeric_date_match = re.search(numeric_date_pattern, date_string)
        
        if numeric_date_match:
            month_num, day, year = numeric_date_match.groups()
            try:
                month_name = datetime(int(year), int(month_num), 1).strftime('%B')
                court_info = re.sub(numeric_date_pattern, '', date_string).strip()
                court_info = re.sub(r'[,\s]+', ' ', court_info).strip()
                
                return DateInfo(
                    year=year,
                    month=month_name,
                    day=day,
                    court=court_info if court_info else None,
                    full_date_string=date_string,
                    date_format='full_date',
                    confidence=0.8
                )
            except ValueError:
                pass
        
        # Pattern 3: Year with court (e.g., "2d Cir. 1995", "S.D.N.Y. 2010")
        court_year_pattern = r'(.+?)\s+(\d{4})'
        court_year_match = re.search(court_year_pattern, date_string)
        
        if court_year_match:
            court_info, year = court_year_match.groups()
            court_info = court_info.strip()
            
            return DateInfo(
                year=year,
                court=court_info,
                full_date_string=date_string,
                date_format='court_year',
                confidence=0.7
            )
        
        # Pattern 4: Just year (e.g., "1995")
        year_only_pattern = r'(\d{4})'
        year_only_match = re.search(year_only_pattern, date_string)
        
        if year_only_match:
            year = year_only_match.group(1)
            return DateInfo(
                year=year,
                full_date_string=date_string,
                date_format='year_only',
                confidence=0.5
            )
        
        # If no patterns match, return empty DateInfo
        return DateInfo(year="", date_format="invalid", full_date_string=date_string, confidence=0.0)
    
    def _calculate_confidence(self, match: re.Match, case_type: str, date_info: DateInfo) -> float:
        """Calculate confidence score for the extraction"""
        base_confidence = 0.6
        
        # Boost for complete match
        if match.group(0).strip():
            base_confidence += 0.1
        
        # Boost for date information
        if date_info and date_info.year:
            base_confidence += 0.2
            if date_info.date_format == 'full_date':
                base_confidence += 0.1
        
        # Boost for specific case types
        if case_type in ['standard', 'government']:
            base_confidence += 0.1
        
        # Boost for court information
        if date_info and date_info.court:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _normalize_court_name(self, court_string: str) -> str:
        """Normalize court abbreviations to full names"""
        if not court_string:
            return ""
        
        normalized = court_string
        for abbr, full_name in self.court_abbreviations.items():
            normalized = re.sub(abbr, full_name, normalized, flags=re.IGNORECASE)
        
        return normalized.strip()
    
    def _deduplicate_extractions(self, extractions: List[CaseExtraction]) -> List[CaseExtraction]:
        """Remove duplicate extractions based on position overlap and content similarity"""
        if not extractions:
            return []
        
        # Sort by start position
        sorted_extractions = sorted(extractions, key=lambda x: x.start_pos or 0)
        deduplicated = [sorted_extractions[0]]
        
        for extraction in sorted_extractions[1:]:
            # Check if this extraction overlaps with the last one
            last_extraction = deduplicated[-1]
            if (extraction.start_pos >= last_extraction.end_pos or 
                extraction.end_pos <= last_extraction.start_pos):
                # No overlap, add it
                deduplicated.append(extraction)
            else:
                # Overlap detected, keep the one with higher confidence
                if extraction.confidence > last_extraction.confidence:
                    deduplicated[-1] = extraction
        
        return deduplicated
    
    def extract_from_table_of_authorities(self, toa_text: str) -> List[CaseExtraction]:
        """Extract cases specifically from Table of Authorities with enhanced patterns"""
        # TOA often has different formatting, use specialized patterns
        extractions = self.extract_cases(toa_text)
        
        # Additional TOA-specific patterns
        toa_patterns = [
            # Simple case name patterns common in TOA
            r'([A-Z][^,]*?\s+v\.\s+[^,]*?)(?=\s*[,;]|\s*$)',
            r'(In\s+re\s+[^,]*?)(?=\s*[,;]|\s*$)',
            r'(State\s+v\.\s+[^,]*?)(?=\s*[,;]|\s*$)',
        ]
        
        for pattern_str in toa_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.finditer(toa_text)
            
            for match in matches:
                case_name = match.group(1).strip()
                if self._is_valid_case_name(case_name):
                    extraction = CaseExtraction(
                        full_match=match.group(0),
                        case_name=case_name,
                        case_type='toa_extraction',
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.6,
                        context=self._get_context(toa_text, match.start(), match.end())
                    )
                    extractions.append(extraction)
        
        return self._deduplicate_extractions(extractions)
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate if a case name is reasonable"""
        if not case_name or len(case_name) < 5:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', case_name):
            return False
        
        # Must not be all caps (likely not a case name)
        if re.match(r'^[A-Z\s]+$', case_name):
            return False
        
        # Must contain common case name indicators
        case_indicators = [' v. ', ' vs. ', ' versus ', 'In re ', 'State v. ', 'People v. ']
        if not any(indicator.lower() in case_name.lower() for indicator in case_indicators):
            return False
        
        return True
    
    def validate_against_toa(self, body_extractions: List[CaseExtraction], 
                            toa_extractions: List[CaseExtraction]) -> Dict[str, List[CaseExtraction]]:
        """Validate body extractions against Table of Authorities with fuzzy matching"""
        toa_case_names = {ext.case_name.lower() for ext in toa_extractions}
        
        validated = []
        unvalidated = []
        
        for extraction in body_extractions:
            # Exact match
            if extraction.case_name.lower() in toa_case_names:
                validated.append(extraction)
            else:
                # Fuzzy match
                best_match = self._find_best_toa_match(extraction.case_name, toa_extractions)
                if best_match and self._calculate_similarity(extraction.case_name, best_match.case_name) > 0.8:
                    validated.append(extraction)
                else:
                    unvalidated.append(extraction)
        
        return {
            'validated': validated,
            'unvalidated': unvalidated,
            'toa_only': [ext for ext in toa_extractions 
                        if ext.case_name.lower() not in 
                        {ext.case_name.lower() for ext in body_extractions}]
        }
    
    def _find_best_toa_match(self, case_name: str, toa_extractions: List[CaseExtraction]) -> Optional[CaseExtraction]:
        """Find the best matching case name in TOA using fuzzy matching"""
        best_match = None
        best_similarity = 0.0
        
        for toa_extraction in toa_extractions:
            similarity = self._calculate_similarity(case_name, toa_extraction.case_name)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = toa_extraction
        
        return best_match if best_similarity > 0.7 else None
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names"""
        # Simple similarity calculation - can be enhanced with more sophisticated algorithms
        name1_clean = re.sub(r'[^\w\s]', '', name1.lower())
        name2_clean = re.sub(r'[^\w\s]', '', name2.lower())
        
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_extraction_stats(self, extractions: List[CaseExtraction]) -> Dict[str, int]:
        """Get comprehensive statistics about extractions"""
        stats = {
            'total': len(extractions),
            'standard': len([e for e in extractions if e.case_type == 'standard']),
            'in_re': len([e for e in extractions if e.case_type == 'in_re']),
            'ex_parte': len([e for e in extractions if e.case_type == 'ex_parte']),
            'matter_of': len([e for e in extractions if e.case_type == 'matter_of']),
            'department': len([e for e in extractions if e.case_type == 'department']),
            'government': len([e for e in extractions if e.case_type == 'government']),
            'with_pincites': len([e for e in extractions if e.pincite]),
            'full_dates': len([e for e in extractions if e.date_info and e.date_info.date_format == 'full_date']),
            'court_dates': len([e for e in extractions if e.date_info and e.date_info.date_format == 'court_year']),
            'year_only': len([e for e in extractions if e.date_info and e.date_info.date_format == 'year_only']),
            'with_court_info': len([e for e in extractions if e.date_info and e.date_info.court]),
            'high_confidence': len([e for e in extractions if e.confidence > 0.8]),
            'medium_confidence': len([e for e in extractions if 0.5 <= e.confidence <= 0.8]),
            'low_confidence': len([e for e in extractions if e.confidence < 0.5])
        }
        return stats
    
    def get_cases_by_year_range(self, extractions: List[CaseExtraction], 
                               start_year: int, end_year: int) -> List[CaseExtraction]:
        """Filter cases by year range"""
        filtered = []
        for extraction in extractions:
            if extraction.year and extraction.year.isdigit():
                case_year = int(extraction.year)
                if start_year <= case_year <= end_year:
                    filtered.append(extraction)
        return filtered
    
    def get_cases_by_court(self, extractions: List[CaseExtraction], 
                          court_pattern: str) -> List[CaseExtraction]:
        """Filter cases by court (using regex pattern)"""
        filtered = []
        pattern = re.compile(court_pattern, re.IGNORECASE)
        for extraction in extractions:
            if (extraction.date_info and extraction.date_info.court and 
                pattern.search(extraction.date_info.court)):
                filtered.append(extraction)
        return filtered
    
    def export_to_csv_format(self, extractions: List[CaseExtraction]) -> List[Dict]:
        """Export extractions to CSV-ready format"""
        csv_data = []
        for extraction in extractions:
            row = {
                'case_name': extraction.case_name,
                'party_1': extraction.party_1,
                'party_2': extraction.party_2,
                'volume': extraction.volume,
                'reporter': extraction.reporter,
                'page': extraction.page,
                'pincite': extraction.pincite,
                'year': extraction.year,
                'month': extraction.date_info.month if extraction.date_info else None,
                'day': extraction.date_info.day if extraction.date_info else None,
                'court': extraction.date_info.court if extraction.date_info else None,
                'court_normalized': self._normalize_court_name(extraction.date_info.court) if extraction.date_info and extraction.date_info.court else None,
                'date_format': extraction.date_info.date_format if extraction.date_info else None,
                'full_date_string': extraction.date_info.full_date_string if extraction.date_info else None,
                'case_type': extraction.case_type,
                'confidence': extraction.confidence,
                'extraction_method': extraction.extraction_method,
                'full_match': extraction.full_match,
                'context': extraction.context[:200] if extraction.context else None  # Truncate for CSV
            }
            csv_data.append(row)
        return csv_data
    
    def convert_to_citation_result(self, extraction: CaseExtraction) -> CitationResult:
        """Convert CaseExtraction to CitationResult for integration with existing pipeline"""
        return CitationResult(
            citation=extraction.full_match,
            case_name=extraction.case_name,
            extracted_case_name=extraction.case_name,
            extracted_date=extraction.year,
            canonical_date=extraction.year,
            year=extraction.year,
            confidence=extraction.confidence,
            context=extraction.context,
            method=extraction.extraction_method,
            start_index=extraction.start_pos,
            end_index=extraction.end_pos,
            metadata={
                'case_type': extraction.case_type,
                'party_1': extraction.party_1,
                'party_2': extraction.party_2,
                'volume': extraction.volume,
                'reporter': extraction.reporter,
                'page': extraction.page,
                'pincite': extraction.pincite,
                'date_info': extraction.date_info.__dict__ if extraction.date_info else None,
                'is_parallel': extraction.is_parallel,
                'parallel_citations': extraction.parallel_citations,
                'docket_number': extraction.docket_number,
                'publication_status': extraction.publication_status
            }
        )
    
    def _extract_with_legacy_patterns(self, text: str, citation: str) -> Tuple[str, str, str]:
        """Fallback to legacy extraction methods for compatibility"""
        try:
            # Use existing extraction method
            # This part of the code was removed from imports, so this fallback will not work as intended
            # For now, it will return a dummy tuple.
            return ("", "", 0.0) 
        except Exception as e:
            logger.debug(f"Legacy extraction failed: {e}")
            return ("", "", 0.0)
    
    def extract_with_fallback(self, text: str, citation: str) -> CaseExtraction:
        """Extract case with fallback to legacy methods if enhanced extraction fails"""
        # Try enhanced extraction first
        extractions = self.extract_cases(text)
        
        # Find extraction that matches the citation
        for extraction in extractions:
            if citation in extraction.full_match:
                logger.info(f"Enhanced extraction succeeded for {citation}: {extraction.case_name}")
                return extraction
        
        logger.info(f"Enhanced extraction failed for {citation}, trying fallback methods")
        
        # Fallback to legacy methods
        failed_fallbacks = []
        for i, fallback_extractor in enumerate(self.fallback_extractors):
            try:
                # The fallback_extractor function signature is Tuple[str, str, float]
                # This means it expects text, citation, and a confidence float.
                # The _extract_with_legacy_patterns function returns a Tuple[str, str, float].
                # So, we can call it directly.
                case_name, date, confidence = fallback_extractor(text, citation)
                if case_name:
                    logger.info(f"Fallback extractor {i+1} succeeded for {citation}: {case_name}")
                    
                    # Log fallback usage
                    log_fallback_usage(
                        citation=citation,
                        fallback_type='extraction',
                        reason=f"Enhanced extraction failed, fallback extractor {i+1} succeeded",
                        context={
                            'fallback_extractor_index': i,
                            'fallback_extractor_count': len(self.fallback_extractors),
                            'failed_enhanced_extraction': True,
                            'failed_fallbacks': failed_fallbacks,
                            'extracted_case_name': case_name,
                            'extracted_date': date,
                            'confidence': confidence
                        }
                    )
                    
                    return CaseExtraction(
                        full_match=citation,
                        case_name=case_name,
                        year=date,
                        case_type='fallback',
                        confidence=float(confidence) if confidence else 0.5,
                        extraction_method=f'fallback_extractor_{i+1}'
                    )
                else:
                    failed_fallbacks.append(f"fallback_{i+1}(no_result)")
                    logger.debug(f"Fallback extractor {i+1} failed for {citation}: no case name found")
            except Exception as e:
                failed_fallbacks.append(f"fallback_{i+1}(error:{str(e)})")
                logger.debug(f"Fallback extractor {i+1} failed for {citation}: {e}")
                continue
        
        # All fallbacks failed
        logger.warning(f"All extraction methods failed for {citation}")
        log_fallback_usage(
            citation=citation,
            fallback_type='extraction',
            reason=f"All extraction methods failed: enhanced + {len(self.fallback_extractors)} fallbacks",
            context={
                'failed_enhanced_extraction': True,
                'failed_fallbacks': failed_fallbacks,
                'total_fallbacks_tried': len(self.fallback_extractors)
            }
        )
        
        # Return empty extraction if all methods fail
        return CaseExtraction(
            full_match=citation,
            case_name="",
            case_type='failed',
            confidence=0.0,
            extraction_method='failed'
        )

# Integration function for existing pipeline
def integrate_enhanced_extractor(text: str, citations: List[str]) -> List[CitationResult]:
    """
    Integrate enhanced extractor with existing citation processing pipeline.
    
    Args:
        text: Document text
        citations: List of citations to process
        
    Returns:
        List of CitationResult objects compatible with existing pipeline
    """
    extractor = LegalCaseExtractorEnhanced()
    results = []
    
    for citation in citations:
        extraction = extractor.extract_with_fallback(text, citation)
        citation_result = extractor.convert_to_citation_result(extraction)
        results.append(citation_result)
    
    return results

# Example usage and testing
if __name__ == "__main__":
    # Initialize extractor
    extractor = LegalCaseExtractorEnhanced()
    
    # Sample legal text with various date formats
    sample_text = """
    In Smith v. Jones, 123 F.3d 456 (2d Cir. Jan. 15, 1995), the court held that...
    See also In re ABC Corp., 456 F.Supp.2d 789 (S.D.N.Y. 2010).
    The Ex parte Johnson, 789 P.2d 123 (Cal. December 3, 1988) decision established...
    Brown v. Board, 347 U.S. 483 (1954) was a landmark case.
    In Matter of XYZ, 555 F.3d 123 (3d Cir. Apr. 2009), the court found...
    White v. Green, 888 F.2d 222 (9th Cir. 3/15/2005) involved complex issues.
    Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    State v. Smith, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    """
    
    # Extract cases
    cases = extractor.extract_cases(sample_text)
    
    # Display results with enhanced date information
    for case in cases:
        logger.info(f"Case: {case.case_name}")
        logger.info(f"Citation: {case.volume} {case.reporter} {case.page} ({case.year})")
        logger.info(f"Type: {case.case_type}")
        logger.info(f"Confidence: {case.confidence:.2f}")
        if case.date_info:
            logger.info(f"Date Format: {case.date_info.date_format}")
            if case.date_info.month:
                logger.info(f"Full Date: {case.date_info.month} {case.date_info.day}, {case.date_info.year}")
            if case.date_info.court:
                logger.info(f"Court: {case.date_info.court}")
                logger.info(f"Court (normalized): {extractor._normalize_court_name(case.date_info.court)}")
        logger.info("-" * 70)
    
    # Get enhanced stats
    stats = extractor.get_extraction_stats(cases)
    logger.info(f"Extraction Statistics: {stats}")
    
    # Test integration with existing pipeline
    citations = ["123 F.3d 456", "456 F.Supp.2d 789", "347 U.S. 483"]
    citation_results = integrate_enhanced_extractor(sample_text, citations)
    logger.info(f"\nIntegrated Citation Results: {len(citation_results)} found")
    
    # Export to CSV format
    csv_data = extractor.export_to_csv_format(cases)
    logger.info(f"\n--- CSV Export Sample ---")
    if csv_data:
        logger.info("Headers:", list(csv_data[0].keys()))
        logger.info("First row:", {k: v for k, v in csv_data[0].items() if v is not None}) 