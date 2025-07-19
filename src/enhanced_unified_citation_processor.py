"""
Enhanced Unified Citation Processor - Integrated Version
Combines UnifiedCitationProcessorV2 + CitationServices + Streamlined Extraction
"""

import re
import logging
import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

# Import the streamlined extraction
from src.case_name_extraction_core import extract_case_name_and_date

logger = logging.getLogger(__name__)

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
    enable_verification: bool = True
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
    """Enhanced confidence scoring system from CitationServices"""
    
    def calculate_weighted_confidence(self, citation: EnhancedCitationResult, 
                                    extraction_result: Dict[str, Any],
                                    text: str) -> Dict[str, float]:
        """Calculate detailed confidence breakdown"""
        
        breakdown = {}
        
        # 1. Case name confidence (30%)
        if citation.extracted_case_name and citation.extracted_case_name != "N/A":
            case_name_score = extraction_result.get('confidence', 0.5) if extraction_result else 0.5
            # Boost for standard adversarial format
            if ' v. ' in citation.extracted_case_name:
                case_name_score += 0.1
            # Boost for government cases
            if any(gov in citation.extracted_case_name for gov in ['State', 'United States', 'People']):
                case_name_score += 0.05
            breakdown['case_name'] = min(1.0, case_name_score)
        else:
            breakdown['case_name'] = 0.0
        
        # 2. Citation structure confidence (35%)
        structure_score = self._calculate_structure_confidence(citation.citation)
        breakdown['citation_structure'] = structure_score
        
        # 3. Date/year confidence (20%)
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
        
        # 4. Verification confidence (10%)
        if citation.verified:
            breakdown['verification'] = 1.0
        else:
            breakdown['verification'] = 0.2
        
        # 5. Context quality (5%)
        context_score = min(1.0, len(citation.context) / 200) if citation.context else 0.0
        breakdown['context'] = context_score
        
        return breakdown
    
    def _calculate_structure_confidence(self, citation: str) -> float:
        """Calculate confidence based on citation structure"""
        if not citation:
            return 0.0
        
        score = 0.0
        
        # Check for valid volume-reporter-page pattern
        if re.match(r'^\d+\s+[A-Za-z\.]+\s*\d*[a-z]*\s+\d+', citation):
            score += 0.7
        
        # Check for known reporters
        known_reporters = ['Wn.2d', 'P.3d', 'P.2d', 'F.3d', 'F.2d', 'U.S.', 'S.Ct.']
        for reporter in known_reporters:
            if reporter in citation:
                score += 0.2
                break
        
        # Check for reasonable numbers
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
    """Professional Bluebook citation formatting"""
    
    def format_citation(self, citation: EnhancedCitationResult) -> str:
        """Format citation according to Bluebook rules"""
        
        # Start with the basic citation
        formatted = self._normalize_citation_spacing(citation.citation)
        
        # Add case name if available
        if citation.extracted_case_name and citation.extracted_case_name != "N/A":
            case_name = citation.extracted_case_name
            
            # Add year if available
            if citation.extracted_date and citation.extracted_date != "N/A":
                formatted = f"{case_name}, {formatted} ({citation.extracted_date})"
            else:
                formatted = f"{case_name}, {formatted}"
        
        return formatted
    
    def _normalize_citation_spacing(self, citation: str) -> str:
        """Normalize spacing according to Bluebook rules"""
        if not citation:
            return citation
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', citation.strip())
        
        # Fix common spacing issues
        # Close up adjacent single capitals (F.3d, S.E.2d)
        normalized = re.sub(r'\b([A-Z])\.\s*([A-Z])\.\s*(\d+[a-z]*)\b', r'\1.\2.\3', normalized)
        
        # Proper spacing for longer abbreviations (So. 2d, Cal. App. 3d)
        normalized = re.sub(r'\b([A-Z][a-z]+)\.\s*(\d+[a-z]*)\b', r'\1. \2', normalized)
        
        return normalized

class CitationValidator:
    """Advanced citation validation from CitationServices"""
    
    def validate_citation(self, citation: EnhancedCitationResult) -> Dict[str, Any]:
        """Comprehensive citation validation"""
        
        result = {
            'is_valid': True,
            'warnings': [],
            'suggestions': [],
            'validation_score': 1.0
        }
        
        # Validate citation format
        if not self._validate_format(citation.citation):
            result['is_valid'] = False
            result['suggestions'].append("Invalid citation format")
            result['validation_score'] -= 0.3
        
        # Validate case name
        if citation.extracted_case_name == "N/A" or not citation.extracted_case_name:
            result['warnings'].append("Missing case name")
            result['validation_score'] -= 0.2
        
        # Validate date
        if citation.extracted_date == "N/A" or not citation.extracted_date:
            result['warnings'].append("Missing date")
            result['validation_score'] -= 0.1
        
        # Check for verification
        if not citation.verified:
            result['warnings'].append("Citation not verified against legal databases")
            result['validation_score'] -= 0.2
        
        result['validation_score'] = max(0.0, result['validation_score'])
        
        return result
    
    def _validate_format(self, citation: str) -> bool:
        """Validate basic citation format"""
        if not citation:
            return False
        
        # Check for volume-reporter-page pattern
        pattern = r'\d+\s+[A-Za-z\.]+\s*\d*[a-z]*\s+\d+'
        return bool(re.search(pattern, citation))

class PrecedentAnalyzer:
    """Analyze precedent strength and legal context"""
    
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
        """Calculate precedent strength: binding, persuasive, or weak"""
        
        # Determine court level from reporter
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
        """Determine court level from citation"""
        
        for system, levels in self.court_hierarchy.items():
            for level, reporters in levels.items():
                for reporter in reporters:
                    if reporter in citation:
                        return level
        
        return 'unknown'

class EnhancedUnifiedCitationProcessor:
    """
    Enhanced processor combining all the best features:
    - UnifiedCitationProcessorV2 (verification, clustering)
    - CitationServices (confidence, validation, formatting) 
    - Streamlined extraction (clean API, patterns)
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        
        # Initialize components
        self.confidence_calculator = ConfidenceCalculator()
        self.bluebook_formatter = BluebookFormatter()
        self.citation_validator = CitationValidator()
        self.precedent_analyzer = PrecedentAnalyzer()
        
        # Initialize patterns from UnifiedProcessorV2
        self._init_patterns()
        
        # Initialize verification
        from src.config import get_config_value
        self.courtlistener_api_key = get_config_value("COURTLISTENER_API_KEY")
        
        logger.info(f"Enhanced processor initialized with verification: {bool(self.courtlistener_api_key)}")
    
    def _init_patterns(self):
        """Initialize citation patterns"""
        self.citation_patterns = {
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            'us': re.compile(r'\b(\d+)\s+U\.S\.\s+(\d+)\b', re.IGNORECASE),
            'f3d': re.compile(r'\b(\d+)\s+F\.3d\s+(\d+)\b', re.IGNORECASE),
            'f2d': re.compile(r'\b(\d+)\s+F\.2d\s+(\d+)\b', re.IGNORECASE),
            # Add more patterns as needed
        }
    
    def process_text(self, text: str) -> List[EnhancedCitationResult]:
        """
        Main processing method combining all features
        """
        logger.info(f"Processing text with enhanced processor ({len(text)} chars)")
        
        if not text or not text.strip():
            return []
        
        # Step 1: Extract citations using regex patterns
        citations = self._extract_with_regex(text)
        logger.info(f"Found {len(citations)} citations via regex")
        
        # Step 2: Add eyecite extraction if available
        if self.config.use_eyecite:
            try:
                eyecite_citations = self._extract_with_eyecite(text)
                citations.extend(eyecite_citations)
                logger.info(f"Added {len(eyecite_citations)} citations via eyecite")
            except Exception as e:
                logger.warning(f"Eyecite extraction failed: {e}")
        
        # Step 3: Deduplicate
        citations = self._deduplicate_citations(citations)
        logger.info(f"After deduplication: {len(citations)} citations")
        
        # Step 4: Enhance each citation
        for citation in citations:
            self._enhance_citation(citation, text)
        
        # Step 5: Verify citations if enabled
        if self.config.enable_verification:
            self._verify_citations(citations, text)
        
        # Step 6: Apply clustering if enabled
        if self.config.enable_clustering:
            citations = self._apply_clustering(citations, text)
        
        logger.info(f"Final result: {len(citations)} enhanced citations")
        return citations
    
    def _extract_with_regex(self, text: str) -> List[EnhancedCitationResult]:
        """Extract citations using regex patterns"""
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
        """Extract citations using eyecite if available"""
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
                        context=text[:200]  # Eyecite doesn't provide position
                    )
                    citations.append(citation)
            
            return citations
        except ImportError:
            return []
    
    def _is_valid_eyecite_citation(self, citation_str: str) -> bool:
        """Validate eyecite citation"""
        # Filter out short forms and invalid citations
        invalid_patterns = ['Id.', 'id.', 'Ibid.', 'ibid.', 'U.S.C.', 'C.F.R.']
        return not any(pattern in citation_str for pattern in invalid_patterns)
    
    def _enhance_citation(self, citation: EnhancedCitationResult, text: str):
        """Enhance citation with all integrated features"""
        
        # Step 1: Extract case name and date using streamlined extractor
        extraction_result = extract_case_name_and_date(text=text, citation=citation.citation)
        citation.extracted_case_name = extraction_result.get('case_name', 'N/A') if extraction_result else 'N/A'
        citation.extracted_date = extraction_result.get('year', 'N/A') if extraction_result else 'N/A'
        
        # Step 2: Calculate enhanced confidence
        if self.config.enable_confidence_breakdown:
            citation.confidence_breakdown = self.confidence_calculator.calculate_weighted_confidence(
                citation, extraction_result, text
            )
            # Calculate overall confidence from breakdown
            weights = {'case_name': 0.3, 'citation_structure': 0.35, 'date': 0.2, 
                      'verification': 0.1, 'context': 0.05}
            citation.confidence = sum(
                citation.confidence_breakdown.get(factor, 0) * weight 
                for factor, weight in weights.items()
            )
        
        # Step 3: Format Bluebook citation
        if self.config.enable_bluebook_formatting:
            citation.bluebook_format = self.bluebook_formatter.format_citation(citation)
        
        # Step 4: Validate citation
        if self.config.enable_validation:
            citation.validation_result = self.citation_validator.validate_citation(citation)
        
        # Step 5: Analyze precedent strength
        citation.precedent_strength = self.precedent_analyzer.calculate_precedent_strength(citation)
        
        # Step 6: Extract reporter info
        citation.reporter_info = self._extract_reporter_info(citation.citation)
    
    def _extract_reporter_info(self, citation: str) -> Dict[str, str]:
        """Extract reporter information"""
        reporter_map = {
            'Wn.2d': {'name': 'Washington Reports, Second Series', 'jurisdiction': 'Washington', 'level': 'Supreme'},
            'Wn.App.': {'name': 'Washington Appellate Reports', 'jurisdiction': 'Washington', 'level': 'Appellate'},
            'P.3d': {'name': 'Pacific Reporter, Third Series', 'jurisdiction': 'Regional', 'level': 'Various'},
            'P.2d': {'name': 'Pacific Reporter, Second Series', 'jurisdiction': 'Regional', 'level': 'Various'},
            'U.S.': {'name': 'United States Reports', 'jurisdiction': 'Federal', 'level': 'Supreme'},
            'F.3d': {'name': 'Federal Reporter, Third Series', 'jurisdiction': 'Federal', 'level': 'Appellate'},
            'F.2d': {'name': 'Federal Reporter, Second Series', 'jurisdiction': 'Federal', 'level': 'Appellate'},
        }
        
        for reporter, info in reporter_map.items():
            if reporter in citation:
                return info
        
        return {'name': 'Unknown', 'jurisdiction': 'Unknown', 'level': 'Unknown'}
    
    def _verify_citations(self, citations: List[EnhancedCitationResult], text: str):
        """Verify citations using CourtListener and fallback services"""
        if not self.courtlistener_api_key:
            logger.warning("No CourtListener API key - skipping verification")
            return
        
        logger.info(f"Verifying {len(citations)} citations")
        
        for citation in citations:
            try:
                # Try CourtListener first
                cl_result = self._verify_with_courtlistener(citation.citation)
                if cl_result.get('verified'):
                    citation.canonical_name = cl_result.get('canonical_name')
                    citation.canonical_date = cl_result.get('canonical_date')
                    citation.url = cl_result.get('url')
                    citation.verified = True
                    citation.source = "CourtListener"
                    continue
                
                # Try canonical service as fallback
                canonical_result = self._verify_with_canonical_service(citation.citation)
                if canonical_result and canonical_result.get('case_name'):
                    citation.canonical_name = canonical_result.get('case_name')
                    citation.canonical_date = canonical_result.get('date')
                    citation.url = canonical_result.get('url')
                    citation.verified = True
                    citation.source = f"fallback: {canonical_result.get('source', 'canonical')}"
                
            except Exception as e:
                logger.error(f"Error verifying {citation.citation}: {e}")
    
    def _verify_with_courtlistener(self, citation: str) -> Dict[str, Any]:
        """Verify with CourtListener API"""
        try:
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            headers = {"Authorization": f"Token {self.courtlistener_api_key}"}
            data = {"text": citation}
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                # Process CourtListener response
                # (Implementation details from UnifiedProcessorV2)
                return {"verified": False}  # Simplified for example
            
        except Exception as e:
            logger.error(f"CourtListener verification failed: {e}")
        
        return {"verified": False}
    
    def _verify_with_canonical_service(self, citation: str) -> Optional[Dict[str, Any]]:
        """Verify with canonical service"""
        try:
            from src.canonical_case_name_service import get_canonical_case_name_with_date
            return get_canonical_case_name_with_date(citation)
        except ImportError:
            return None
    
    def _apply_clustering(self, citations: List[EnhancedCitationResult], text: str) -> List[EnhancedCitationResult]:
        """Apply intelligent clustering"""
        # Group citations by case (simplified implementation)
        clusters = defaultdict(list)
        
        for citation in citations:
            # Use case name for clustering
            cluster_key = citation.canonical_name or citation.extracted_case_name or "unknown"
            clusters[cluster_key].append(citation)
        
        # Add cluster metadata
        for cluster_id, (cluster_key, cluster_citations) in enumerate(clusters.items()):
            if len(cluster_citations) > 1:
                for citation in cluster_citations:
                    citation.cluster_id = f"cluster_{cluster_id}"
                    citation.parallel_citations = [c.citation for c in cluster_citations if c != citation]
        
        return citations
    
    def _deduplicate_citations(self, citations: List[EnhancedCitationResult]) -> List[EnhancedCitationResult]:
        """Remove duplicate citations"""
        seen = set()
        unique = []
        
        for citation in citations:
            normalized = self._normalize_citation(citation.citation)
            if normalized not in seen:
                seen.add(normalized)
                unique.append(citation)
        
        return unique
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison"""
        return re.sub(r'\s+', ' ', citation.strip().lower())
    
    def _extract_context(self, text: str, start: int, end: int) -> str:
        """Extract context around citation"""
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

# Example usage
if __name__ == "__main__":
    # Test the enhanced processor
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)."""
    
    # Enhanced extraction
    config = ProcessingConfig(
        enable_verification=True,
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