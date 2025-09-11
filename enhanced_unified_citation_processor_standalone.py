"""
Enhanced Unified Citation Processor - Fixed Standalone Version
Removes external dependencies to work with your test script
"""

import re
import logging
import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import os

print("[DEBUG] Script started (top of file)")

# Set up logging to file and console
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'enhanced_processor_standalone.log')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in logger.handlers):
    logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(console_handler)

logger.info("[DEBUG] Script started (after logging setup)")

@dataclass
class EnhancedCitationResult:
    """Enhanced citation result with all integrated features"""
    # Core citation data
    citation: str
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
    court: Optional[str] = None
    
    # Enhanced features from CitationServices
    confidence_breakdown: Dict[str, float] = None
    bluebook_format: str = ""
    validation_result: Dict[str, Any] = None
    reporter_info: Dict[str, str] = None
    precedent_strength: str = "unknown"  # binding, persuasive, weak
    
    # Technical metadata
    confidence: float = 0.0
    method: str = "enhanced_unified"
    pattern: str = ""
    context: str = ""
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    source: str = "Enhanced Processor"
    metadata: Dict[str, Any] = None
    
    # Clustering and parallel citations
    is_parallel: bool = False
    parallel_citations: List[str] = None
    cluster_id: Optional[str] = None
    
    def __post_init__(self):
        if self.confidence_breakdown is None:
            self.confidence_breakdown = {}
        if self.validation_result is None:
            self.validation_result = {}
        if self.reporter_info is None:
            self.reporter_info = {}
        if self.metadata is None:
            self.metadata = {}
        if self.parallel_citations is None:
            self.parallel_citations = []
    
    def get_professional_citation(self) -> str:
        """Get properly formatted Bluebook citation"""
        return self.bluebook_format or self.citation
    
    def get_confidence_explanation(self) -> str:
        """Explain confidence score breakdown"""
        if not self.confidence_breakdown:
            return f"Overall confidence: {self.confidence:.1%}"
        
        explanations = []
        for factor, score in self.confidence_breakdown.items():
            explanations.append(f"{factor}: {score:.1%}")
        return "; ".join(explanations)

@dataclass
class ProcessingConfig:
    """Enhanced processing configuration"""
    # Core extraction
    use_eyecite: bool = True
    use_regex: bool = True
    extract_case_names: bool = True
    extract_dates: bool = True
    
    # Enhanced features
    enable_verification: bool = True  # Re-enabled for full functionality
    enable_bluebook_formatting: bool = True
    enable_confidence_breakdown: bool = True
    enable_validation: bool = True
    enable_clustering: bool = True
    
    # Processing options
    context_window: int = 300
    min_confidence: float = 0.5
    max_citations_per_text: int = 1000
    debug_mode: bool = False

class ConfidenceCalculator:
    """Enhanced confidence scoring system"""
    def calculate_weighted_confidence(self, citation: EnhancedCitationResult, extraction_result: Dict[str, Any], text: str) -> Dict[str, float]:
        breakdown = {}
        if citation.extracted_case_name and citation.extracted_case_name != "N/A":
            case_name_score = extraction_result.get('confidence', 0.5) if extraction_result else 0.5
            if ' v. ' in citation.extracted_case_name:
                case_name_score += 0.1
            if any(gov in citation.extracted_case_name for gov in ['State', 'United States', 'People']):
                case_name_score += 0.05
            breakdown['case_name'] = min(1.0, case_name_score)
        else:
            breakdown['case_name'] = 0.0
        structure_score = self._calculate_structure_confidence(citation.citation)
        breakdown['citation_structure'] = structure_score
        if citation.extracted_date and citation.extracted_date != "N/A":
            try:
                year = int(citation.extracted_date)
                if 1800 <= year <= 2030:
                    breakdown['date'] = 0.8
                else:
                    breakdown['date'] = 0.3
            except (ValueError, TypeError):
                breakdown['date'] = 0.5
        else:
            breakdown['date'] = 0.0
        if citation.verified:
            breakdown['verification'] = 1.0
        else:
            breakdown['verification'] = 0.2
        context_score = min(1.0, len(citation.context) / 200) if citation.context else 0.0
        breakdown['context'] = context_score
        return breakdown
    def _calculate_structure_confidence(self, citation: str) -> float:
        if not citation:
            return 0.0
        score = 0.0
        if re.match(r'^\d+\s+[A-Za-z\.]+\s*\d*[a-z]*\s+\d+', citation):
            score += 0.7
        known_reporters = ['Wn.2d', 'P.3d', 'P.2d', 'F.3d', 'F.2d', 'U.S.', 'S.Ct.']
        for reporter in known_reporters:
            if reporter in citation:
                score += 0.2
                break
        numbers = re.findall(r'\d+', citation)
        if len(numbers) >= 2:
            try:
                volume = int(numbers[0])
                page = int(numbers[1])
                if 1 <= volume <= 9999 and 1 <= page <= 9999:
                    score += 0.1
            except (ValueError, IndexError):
                pass
        return min(1.0, score)

class BluebookFormatter:
    def format_citation(self, citation: EnhancedCitationResult) -> str:
        formatted = self._normalize_citation_spacing(citation.citation)
        if citation.extracted_case_name and citation.extracted_case_name != "N/A":
            case_name = citation.extracted_case_name
            if citation.extracted_date and citation.extracted_date != "N/A":
                formatted = f"{case_name}, {formatted} ({citation.extracted_date})"
            else:
                formatted = f"{case_name}, {formatted}"
        return formatted
    def _normalize_citation_spacing(self, citation: str) -> str:
        if not citation:
            return citation
        normalized = re.sub(r'\s+', ' ', citation.strip())
        normalized = re.sub(r'\b([A-Z])\.\s*([A-Z])\.\s*(\d+[a-z]*)\b', r'\1.\2.\3', normalized)
        normalized = re.sub(r'\b([A-Z][a-z]+)\.\s*(\d+[a-z]*)\b', r'\1. \2', normalized)
        return normalized

class CitationValidator:
    def validate_citation(self, citation: EnhancedCitationResult) -> Dict[str, Any]:
        result = {
            'is_valid': True,
            'warnings': [],
            'suggestions': [],
            'validation_score': 1.0
        }
        if not self._validate_format(citation.citation):
            result['is_valid'] = False
            result['suggestions'].append("Invalid citation format")
            result['validation_score'] -= 0.3
        if citation.extracted_case_name == "N/A" or not citation.extracted_case_name:
            result['warnings'].append("Missing case name")
            result['validation_score'] -= 0.2
        if citation.extracted_date == "N/A" or not citation.extracted_date:
            result['warnings'].append("Missing date")
            result['validation_score'] -= 0.1
        if not citation.verified:
            result['warnings'].append("Citation not verified against legal databases")
            result['validation_score'] -= 0.2
        result['validation_score'] = max(0.0, result['validation_score'])
        return result
    def _validate_format(self, citation: str) -> bool:
        if not citation:
            return False
        pattern = r'\d+\s+[A-Za-z\.]+\s*\d*[a-z]*\s+\d+'
        return bool(re.search(pattern, citation))

class PrecedentAnalyzer:
    def __init__(self):
        self.court_hierarchy = {
            'federal': {
                'supreme': ['U.S.', 'S.Ct.', 'L.Ed.'],
                'appellate': ['F.3d', 'F.2d'],
                'district': ['F.Supp.', 'F.Supp.2d', 'F.Supp.3d']
            },
            'state': {
                'supreme': ['Wn.2d'],
                'appellate': ['Wn.App.', 'P.3d', 'P.2d'],
                'trial': []
            }
        }
    def calculate_precedent_strength(self, citation: EnhancedCitationResult) -> str:
        court_level = self._determine_court_level(citation.citation)
        if court_level == 'supreme':
            return 'binding'
        elif court_level == 'appellate':
            return 'persuasive'
        elif court_level == 'district':
            return 'weak'
        else:
            return 'unknown'
    def _determine_court_level(self, citation: str) -> str:
        for system, levels in self.court_hierarchy.items():
            for level, reporters in levels.items():
                for reporter in reporters:
                    if reporter in citation:
                        return level
        return 'unknown'

class EnhancedUnifiedCitationProcessor:
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.case_name_extractor = CaseNameExtractor()
        self.confidence_calculator = ConfidenceCalculator()
        self.bluebook_formatter = BluebookFormatter()
        self.citation_validator = CitationValidator()
        self.precedent_analyzer = PrecedentAnalyzer()
        self._init_patterns()
        logger.info(f"Enhanced processor initialized")
    def _init_patterns(self):
        self.citation_patterns = {
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            'us': re.compile(r'\b(\d+)\s+U\.S\.\s+(\d+)\b', re.IGNORECASE),
            'sct': re.compile(r'\b(\d+)\s+S\.Ct\.\s+(\d+)\b', re.IGNORECASE),
            'f3d': re.compile(r'\b(\d+)\s+F\.3d\s+(\d+)\b', re.IGNORECASE),
            'f2d': re.compile(r'\b(\d+)\s+F\.2d\s+(\d+)\b', re.IGNORECASE),
            'fsupp': re.compile(r'\b(\d+)\s+F\.Supp\.\s*(\d*[a-z]*)\s+(\d+)\b', re.IGNORECASE),
        }
    def process_text(self, text: str) -> List[EnhancedCitationResult]:
        logger.info(f"Processing text with enhanced processor ({len(text)} chars)")
        if not text or not text.strip():
            return []
        citations = self._extract_with_regex(text)
        logger.info(f"Found {len(citations)} citations via regex")
        if self.config.use_eyecite:
            try:
                eyecite_citations = self._extract_with_eyecite(text)
                citations.extend(eyecite_citations)
                logger.info(f"Added {len(eyecite_citations)} citations via eyecite")
            except Exception as e:
                logger.warning(f"Eyecite extraction failed: {e}")
        citations = self._deduplicate_citations(citations)
        logger.info(f"After deduplication: {len(citations)} citations")
        for citation in citations:
            self._enhance_citation(citation, text)
        if self.config.enable_clustering:
            citations = self._apply_clustering(citations, text)
        logger.info(f"Final result: {len(citations)} enhanced citations")
        return citations
    def _extract_with_regex(self, text: str) -> List[EnhancedCitationResult]:
        citations = []
        seen_citations = set()
        for pattern_name, pattern in self.citation_patterns.items():
            for match in pattern.finditer(text):
                citation_str = match.group(0).strip()
                if citation_str not in seen_citations:
                    seen_citations.add(citation_str)
                    citation = EnhancedCitationResult(
                        citation=citation_str,
                        start_index=match.start(),
                        end_index=match.end(),
                        method="enhanced_regex",
                        pattern=pattern_name,
                        context=self._extract_context(text, match.start(), match.end())
                    )
                    citations.append(citation)
        return citations
    def _extract_with_eyecite(self, text: str) -> List[EnhancedCitationResult]:
        try:
            import eyecite
            from eyecite import get_citations
            from eyecite.tokenizers import AhocorasickTokenizer
            citations = []
            tokenizer = AhocorasickTokenizer()
            eyecite_citations = get_citations(text, tokenizer=tokenizer)
            for citation_obj in eyecite_citations:
                citation_str = str(citation_obj)
                if self._is_valid_eyecite_citation(citation_str):
                    citation = EnhancedCitationResult(
                        citation=citation_str,
                        method="eyecite",
                        pattern="eyecite",
                        context=text[:200]
                    )
                    citations.append(citation)
            return citations
        except ImportError:
            logger.warning("Eyecite not available, skipping")
            return []
    def _is_valid_eyecite_citation(self, citation_str: str) -> bool:
        invalid_patterns = ['Id.', 'id.', 'Ibid.', 'ibid.', 'U.S.C.', 'C.F.R.']
        return not any(pattern in citation_str for pattern in invalid_patterns)
    def _enhance_citation(self, citation: EnhancedCitationResult, text: str):
        extraction_result = self.case_name_extractor.extract_case_name_and_date(text=text, citation=citation.citation)
        citation.extracted_case_name = extraction_result.get('case_name', 'N/A')
        citation.extracted_date = extraction_result.get('year', 'N/A')
        if self.config.enable_confidence_breakdown:
            citation.confidence_breakdown = self.confidence_calculator.calculate_weighted_confidence(
                citation, extraction_result, text
            )
            weights = {'case_name': 0.3, 'citation_structure': 0.35, 'date': 0.2, 'verification': 0.1, 'context': 0.05}
            citation.confidence = sum(
                citation.confidence_breakdown.get(factor, 0) * weight 
                for factor, weight in weights.items()
            )
        if self.config.enable_bluebook_formatting:
            citation.bluebook_format = self.bluebook_formatter.format_citation(citation)
        if self.config.enable_validation:
            citation.validation_result = self.citation_validator.validate_citation(citation)
        citation.precedent_strength = self.precedent_analyzer.calculate_precedent_strength(citation)
        citation.reporter_info = self._extract_reporter_info(citation.citation)
    def _extract_reporter_info(self, citation: str) -> Dict[str, str]:
        reporter_map = {
            'Wn.2d': {'name': 'Washington Reports, Second Series', 'jurisdiction': 'Washington', 'level': 'Supreme'},
            'Wn.App.': {'name': 'Washington Appellate Reports', 'jurisdiction': 'Washington', 'level': 'Appellate'},
            'P.3d': {'name': 'Pacific Reporter, Third Series', 'jurisdiction': 'Regional', 'level': 'Various'},
            'P.2d': {'name': 'Pacific Reporter, Second Series', 'jurisdiction': 'Regional', 'level': 'Various'},
            'U.S.': {'name': 'United States Reports', 'jurisdiction': 'Federal', 'level': 'Supreme'},
            'S.Ct.': {'name': 'Supreme Court Reporter', 'jurisdiction': 'Federal', 'level': 'Supreme'},
            'F.3d': {'name': 'Federal Reporter, Third Series', 'jurisdiction': 'Federal', 'level': 'Appellate'},
            'F.2d': {'name': 'Federal Reporter, Second Series', 'jurisdiction': 'Federal', 'level': 'Appellate'},
            'F.Supp.': {'name': 'Federal Supplement', 'jurisdiction': 'Federal', 'level': 'District'},
        }
        for reporter, info in reporter_map.items():
            if reporter in citation:
                return info
        return {'name': 'Unknown', 'jurisdiction': 'Unknown', 'level': 'Unknown'}
    def _apply_clustering(self, citations: List[EnhancedCitationResult], text: str) -> List[EnhancedCitationResult]:
        clusters = defaultdict(list)
        for citation in citations:
            cluster_key = citation.canonical_name or citation.extracted_case_name or "unknown"
            clusters[cluster_key].append(citation)
        for cluster_id, (cluster_key, cluster_citations) in enumerate(clusters.items()):
            if len(cluster_citations) > 1:
                for citation in cluster_citations:
                    citation.cluster_id = f"cluster_{cluster_id}"
                    citation.parallel_citations = [c.citation for c in cluster_citations if c != citation]
        return citations
    def _deduplicate_citations(self, citations: List[EnhancedCitationResult]) -> List[EnhancedCitationResult]:
        seen = set()
        unique = []
        for citation in citations:
            normalized = self._normalize_citation(citation.citation)
            if normalized not in seen:
                seen.add(normalized)
                unique.append(citation)
        return unique
    def _normalize_citation(self, citation: str) -> str:
        return re.sub(r'\s+', ' ', citation.strip().lower())
    def _extract_context(self, text: str, start: int, end: int) -> str:
        context_start = max(0, start - 150)
        context_end = min(len(text), end + 150)
        return text[context_start:context_end].strip()

# Convenience functions for easy use
def extract_citations_enhanced(text: str, config: Optional[ProcessingConfig] = None) -> List[EnhancedCitationResult]:
    """
    Main function for enhanced citation extraction
    Args:
        text: Text to extract citations from
        config: Optional processing configuration
    Returns:
        List of enhanced citation results
    """
    processor = EnhancedUnifiedCitationProcessor(config)
    return processor.process_text(text)

def extract_citations_simple(text: str) -> List[Dict[str, Any]]:
    """
    Simplified function that returns basic dictionaries
    """
    processor = EnhancedUnifiedCitationProcessor()
    citations = processor.process_text(text)
    # Convert to simple dictionaries
    return [
        {
            'citation': c.citation,
            'case_name': c.extracted_case_name,
            'year': c.extracted_date,
            'confidence': c.confidence,
            'verified': c.verified,
            'bluebook_format': c.bluebook_format,
            'precedent_strength': c.precedent_strength
        }
        for c in citations
    ]

class CaseNameExtractor:
    """Standalone case name extraction (replaces missing dependency)"""
    
    def extract_case_name_and_date(self, text: str, citation: str) -> Dict[str, Any]:
        """Extract case name and date from text around citation"""
        
        # Find citation position in text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return {'case_name': 'N/A', 'year': 'N/A', 'confidence': 0.0}
        
        # Look for case name before citation (common pattern)
        search_start = max(0, citation_pos - 200)
        search_text = text[search_start:citation_pos + len(citation) + 50]
        
        # Extract year from citation or context
        year = self._extract_year(citation, search_text)
        
        # Extract case name
        case_name = self._extract_case_name(search_text, citation)
        
        confidence = 0.7 if case_name != 'N/A' else 0.3
        
        return {
            'case_name': case_name,
            'year': year,
            'confidence': confidence
        }
    
    def _extract_year(self, citation: str, context: str) -> str:
        """Extract year from citation or context"""
        
        # Look for year in parentheses first (most common)
        year_match = re.search(r'\((\d{4})\)', context)
        if year_match:
            year = int(year_match.group(1))
            if 1800 <= year <= 2030:
                return str(year)
        
        # Look for standalone 4-digit year
        year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', context)
        if year_matches:
            return year_matches[-1]  # Take the last one found
        
        return 'N/A'
    
    def _extract_case_name(self, context: str, citation: str) -> str:
        """Extract case name from context"""
        
        # Look for "X v. Y" pattern before citation
        case_pattern = r'([A-Z][A-Za-z\s&,\.]+)\s+v\.\s+([A-Z][A-Za-z\s&,\.]+)'
        
        # Search in the text before the citation
        citation_pos = context.find(citation)
        if citation_pos > 0:
            before_citation = context[:citation_pos]
            
            # Find the last case name pattern before citation
            matches = list(re.finditer(case_pattern, before_citation))
            if matches:
                last_match = matches[-1]
                plaintiff = last_match.group(1).strip()
                defendant = last_match.group(2).strip()
                
                # Clean up the names
                plaintiff = self._clean_party_name(plaintiff)
                defendant = self._clean_party_name(defendant)
                
                if plaintiff and defendant:
                    return f"{plaintiff} v. {defendant}"
        
        # Look for other patterns
        # Government cases
        gov_pattern = r'\b(State|United States|People|City|County)\s+[^,]*?\s+v\.\s+([A-Z][A-Za-z\s]+)'
        gov_match = re.search(gov_pattern, context)
        if gov_match:
            return f"{gov_match.group(1)} v. {self._clean_party_name(gov_match.group(2))}"
        
        return 'N/A'
    
    def _clean_party_name(self, name: str) -> str:
        """Clean up party name"""
        if not name:
            return ""
        
        # Remove common suffixes that aren't part of party name
        suffixes = [', LLC', ', Inc.', ', Corp.', ', Ltd.', ' et al.']
        cleaned = name.strip()
        
        # Remove trailing punctuation and whitespace
        cleaned = re.sub(r'[,.\s]+$', '', cleaned)
        
        # Limit length
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."
        
        return cleaned 

if __name__ == "__main__":
    try:
        print("[DEBUG] Script main starting")
        logging.info("[DEBUG] Script main starting")
        # Test the enhanced processor
        test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)."""
        # Enhanced extraction
        config = ProcessingConfig(
            enable_verification=True,  # Re-enabled for full testing
            enable_bluebook_formatting=True,
            enable_confidence_breakdown=True
        )
        citations = extract_citations_enhanced(test_text, config)
        for citation in citations:
            print(f"Citation: {citation.citation}")
            print(f"Case Name: {citation.extracted_case_name}")
            print(f"Year: {citation.extracted_date}")
            print(f"Confidence: {citation.confidence:.2f}")
            print(f"Bluebook: {citation.bluebook_format}")
            print(f"Verified: {citation.verified}")
            print(f"Precedent: {citation.precedent_strength}")
            print("---")
        logging.info("[DEBUG] Script main completed successfully")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        logging.error(f"[DEBUG] Exception: {e}", exc_info=True) 