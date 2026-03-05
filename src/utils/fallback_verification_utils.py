"""
Shared utilities for fallback citation verification.
Eliminates redundancy across _verify_with_* functions.
"""

import re
import html
import logging
from typing import Optional, Dict, Any, List, Tuple, Set
from urllib.parse import quote

logger = logging.getLogger(__name__)


class PatternLibrary:
    """Centralized regex patterns for HTML parsing."""
    
    # Case name extraction patterns
    CASE_NAME_PATTERNS = [
        r"<h1[^>]*>([^<]+v\.?[^<]+)</h1>",
        r"<title>([^<]+v\.?[^<]+)\s*\|",
        r'<meta\s+property="og:title"\s+content="([^"]+v\.?[^"]+)"',
        r"<h2[^>]*>([^<]+v\.?[^<]+)</h2>",
    ]
    
    # Year extraction patterns
    YEAR_PATTERNS = [
        r"\b(19|20)\d{2}\b",  # Standard 4-digit year
    ]
    
    # Date extraction patterns
    DATE_PATTERNS = [
        r"Decided:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"Date Filed:\s*(\d{2}/\d{2}/\d{4})",
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})\b",
    ]
    
    # Citation patterns for validation
    CITATION_VARIATIONS = [
        lambda c: c,  # Exact
        lambda c: c.replace(" ", r"\s+"),  # Flexible spacing
        lambda c: c.replace(".", r"\.?"),  # Optional periods
        lambda c: c.replace(" ", "").lower(),  # No spaces, lowercase
    ]


class CitationNormalizer:
    """Normalize citations for comparison."""
    
    @staticmethod
    def normalize(citation: str) -> str:
        """Normalize citation for comparison."""
        return citation.replace(" ", "").lower()
    
    @staticmethod
    def create_variations(citation: str) -> List[str]:
        """Create regex patterns for citation matching."""
        return [
            re.escape(citation),
            citation.replace(" ", r"\s+"),
            citation.replace(".", r"\.?"),
        ]


class NameValidator:
    """Validate case name matches between extracted and canonical."""
    
    COMMON_WORDS = {
        "v", "v.", "vs", "vs.", "the", "of", "in", "a", "an", "&", "and",
        "inc", "inc.", "llc", "ltd", "ltd.", "co", "co.", "corp", "corp.",
    }
    
    @classmethod
    def calculate_overlap(cls, extracted_name: str, canonical_name: str) -> float:
        """Calculate word overlap ratio between two case names."""
        if not extracted_name or not canonical_name:
            return 0.0
        
        extracted_words = set(extracted_name.lower().split())
        canonical_words = set(canonical_name.lower().split())
        
        # Remove common words
        extracted_words -= cls.COMMON_WORDS
        canonical_words -= cls.COMMON_WORDS
        
        if not extracted_words:
            return 0.0
        
        return len(extracted_words & canonical_words) / len(extracted_words)
    
    @classmethod
    def validate_match(
        cls,
        extracted_name: Optional[str],
        canonical_name: str,
        min_overlap: float = 0.3
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Validate case name match.
        
        Returns:
            (is_valid, overlap_score, warning_message)
        """
        if not extracted_name or extracted_name == "N/A":
            return True, 0.0, None  # No extracted name to validate against
        
        overlap = cls.calculate_overlap(extracted_name, canonical_name)
        
        if overlap == 0:
            return False, overlap, f"No unusual words match between extracted '{extracted_name}' and canonical '{canonical_name}'"
        elif overlap < min_overlap:
            return True, overlap, f"Low overlap ({overlap:.0%}) between extracted '{extracted_name}' and canonical '{canonical_name}'"
        
        return True, overlap, None


class HTMLExtractor:
    """Extract data from HTML content."""
    
    @staticmethod
    def extract_case_name(content: str, patterns: Optional[List[str]] = None) -> Optional[str]:
        """Extract case name from HTML content."""
        patterns = patterns or PatternLibrary.CASE_NAME_PATTERNS
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up HTML entities and whitespace
                name = html.unescape(name)
                name = re.sub(r"\s+", " ", name)
                return name
        
        return None
    
    @staticmethod
    def extract_year(content: str, max_chars: int = 4000) -> Optional[str]:
        """Extract year from HTML content."""
        search_content = content[:max_chars]
        
        for pattern in PatternLibrary.YEAR_PATTERNS:
            match = re.search(pattern, search_content)
            if match:
                return match.group(0)
        
        return None
    
    @staticmethod
    def extract_date(content: str) -> Optional[str]:
        """Extract full date from HTML content."""
        for pattern in PatternLibrary.DATE_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback to year only
        return HTMLExtractor.extract_year(content)
    
    @staticmethod
    def citation_found(content: str, citation: str) -> bool:
        """Check if citation appears in content."""
        content_normalized = content.replace(" ", "").lower()
        citation_normalized = citation.replace(" ", "").lower()
        
        if citation_normalized in content_normalized:
            return True
        
        # Try regex variations
        variations = CitationNormalizer.create_variations(citation)
        for pattern in variations:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False


def _extract_citation_token(citation: str) -> str:
    """
    Extract the reporter citation from a string that may include a case name prefix.
    "Susan B. Anthony List v. Driehaus, 573 U.S. 149 (2014)" -> "573 U.S. 149"
    "Swindle v. State, 10 Tenn. 581 (1831)" -> "10 Tenn. 581"
    """
    s = (citation or "").strip()
    if not s:
        return s
    # Find last comma before a citation pattern (case name, citation)
    m = re.search(r",\s*(\d+\s+[A-Za-z][A-Za-z.\s]*?\s+\d+(?:\s*,\s*\d+)?)", s)
    if m:
        return m.group(1).strip()
    return s


class URLBuilder:
    """Build URLs for legal databases. Uses re.search to handle citations with case name prefix."""

    @staticmethod
    def build_justia_url(citation: str) -> Optional[str]:
        """Build Justia URL from citation. Handles 'Case Name, 573 U.S. 149' format."""
        tok = _extract_citation_token(citation)
        us_match = re.search(r"(\d+)\s+U\.?S\.?\s+(\d+)", tok, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://supreme.justia.com/us/{volume}/{page}/"

        federal_match = re.search(r"(\d+)\s+F\.?(\d+)d?\s+(\d+)", tok, re.IGNORECASE)
        if federal_match:
            volume, reporter_vol, page = federal_match.groups()
            reporter = f"F.{reporter_vol}d"
            return f"https://law.justia.com/cases/federal/appellate-courts/{reporter}/{volume}/{page}/"

        fsupp_match = re.search(r"(\d+)\s+F\.?\s*Supp\.?\s*(\d+)?d?\s+(\d+)", tok, re.IGNORECASE)
        if fsupp_match:
            volume = fsupp_match.group(1)
            series = fsupp_match.group(2)
            page = fsupp_match.group(3)
            reporter_slug = f"FSupp{series}" if series else "FSupp"
            return f"https://law.justia.com/cases/federal/district-courts/{reporter_slug}/{volume}/{page}/"

        return None

    @staticmethod
    def build_cornell_lii_url(citation: str) -> Optional[str]:
        """Build Cornell LII URL from citation."""
        tok = _extract_citation_token(citation)
        us_match = re.search(r"(\d+)\s+U\.?S\.?\s+(\d+)", tok, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://www.law.cornell.edu/supremecourt/text/{volume}/{page}"
        return None

    @staticmethod
    def build_openjurist_url(citation: str) -> Optional[str]:
        """Build OpenJurist URL from citation."""
        tok = _extract_citation_token(citation)
        us_match = re.search(r"(\d+)\s+U\.?S\.?\s+(\d+)", tok, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://openjurist.org/{volume}/us/{page}"
        federal_match = re.search(r"(\d+)\s+F\.?(\d+)d?\s+(\d+)", tok, re.IGNORECASE)
        if federal_match:
            volume, reporter_vol, page = federal_match.groups()
            return f"https://openjurist.org/{volume}/f{reporter_vol}d/{page}"
        return None

    @staticmethod
    def build_findlaw_url(citation: str) -> Optional[str]:
        """Build FindLaw URL from citation."""
        tok = _extract_citation_token(citation)
        us_match = re.search(r"(\d+)\s+U\.?S\.?\s+(\d+)", tok, re.IGNORECASE)
        if us_match:
            volume, page = us_match.groups()
            return f"https://caselaw.findlaw.com/us-supreme-court/{volume}/{page}.html"
        return None


class HTTPClient:
    """Shared HTTP client configuration."""
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    @classmethod
    def get_headers(cls, additional: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get default headers with optional additions."""
        headers = cls.DEFAULT_HEADERS.copy()
        if additional:
            headers.update(additional)
        return headers


def parse_citation(citation: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse citation into (volume, reporter, page).
    
    Returns:
        Tuple of (volume, reporter, page) or None if invalid
    """
    parts = re.split(r"\s+", citation.strip())
    if len(parts) < 3:
        return None
    
    volume, reporter, page = parts[0], parts[1], parts[2]
    
    if not (volume.isdigit() and reporter and page.isdigit()):
        return None
    
    return volume, reporter, page


def year_from_date(date_str: Optional[str]) -> Optional[int]:
    """Extract 4-digit year from date string."""
    if not date_str:
        return None
    
    match = re.search(r"(19|20)\d{2}", str(date_str))
    if match:
        return int(match.group(0))
    
    return None


def citation_type_detector(citation: str) -> Dict[str, bool]:
    """
    Detect citation type for source prioritization.
    
    Returns:
        Dict with boolean flags for citation types
    """
    return {
        "is_us_supreme_court": bool(re.search(r"\b(\d+)\s+U\.?S\.?\s+(\d+)\b", citation, re.IGNORECASE)),
        "is_slip": bool(re.search(r"\d+\s+U\.?\s*S\.?\s+[_\-\s]+", citation, re.IGNORECASE)),
        "is_federal_reporter": bool(re.search(r"\bF\.?(2|3|4)d?\b", citation, re.IGNORECASE)),
        "is_federal_supp": bool(re.search(r"\bF\.\s*Supp\.?\s*(?:2d|3d)?\b", citation, re.IGNORECASE)),
        "is_federal_appx": bool(re.search(r"\bF\.?\s*App[']?x\b", citation, re.IGNORECASE)),
        "is_state_citation": bool(re.search(r"\b[A-Z][a-z]+\.[A-Z][a-z]+\b", citation)),
    }
