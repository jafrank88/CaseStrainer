"""
CITATION PATTERNS - Single Source of Truth
==========================================

This module contains ALL citation regex patterns used throughout CaseStrainer.

IMPORTANT: This is the ONLY place where citation patterns should be defined.
Any changes to citation patterns should ONLY be made here.

Usage:
    from src.citation_patterns import CitationPatterns
    patterns = CitationPatterns.get_compiled_patterns()
"""

import re
from typing import Dict


class CitationPatterns:
    """
    Centralized citation pattern definitions.
    
    All patterns are defined as raw strings and compiled on demand.
    This ensures consistency across all extraction pipelines.
    """
    
    # ============================================================================
    # FEDERAL REPORTERS
    # ============================================================================
    
    US_SUPREME = r'\b\d+\s+U\.S\.\s+\d+\b'
    US_SUPREME_ALT = r'\b\d+\s+U\.\s*S\.\s+\d+\b'  # Alternate spacing
    S_CT = r'\b\d+\s+S\.\s*Ct\.\s+\d+\b'
    L_ED = r'\b\d+\s+L\.\s*Ed\.\s+\d+\b'
    L_ED_2D = r'\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+\b'
    
    F_2D = r'\b\d+\s+F\.\s*2d\s+\d+\b'
    F_3D = r'\b\d+\s+F\.\s*3d\s+\d+\b'
    F_4TH = r'\b\d+\s+F\.\s*4th\s+\d+\b'
    F_SUPP = r'\b\d+\s+F\.\s*Supp\.\s+\d+\b'
    F_SUPP_2D = r'\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+\b'
    F_SUPP_3D = r'\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+\b'
    
    # ============================================================================
    # STATE REPORTERS - PACIFIC
    # ============================================================================
    
    P_GENERAL = r'\b\d+\s+P\.\s+\d+\b'  # Older Pacific Reporter
    P_2D = r'\b\d+\s+P\.\s*2d\s+\d+\b'
    P_3D = r'\b\d+\s+P\.\s*3d\s+\d+\b'
    
    # ============================================================================
    # STATE REPORTERS - WASHINGTON
    # ============================================================================
    
    WN_FIRST = r'\b\d+\s+Wn\.\s+\d+\b'  # Washington First Series
    WASH_FIRST = r'\b\d+\s+Wash\.\s+\d+\b'  # Alternate format
    WN_2D = r'\b\d+\s+Wn\.2d\s+\d+\b'
    WN_2D_SPACE = r'\b\d+\s+Wn\.\s*2d\s+\d+\b'  # With optional space
    WASH_2D = r'\b\d+\s+Wash\.2d\s+\d+\b'
    WN_3D = r'\b\d+\s+Wn\.\s*3d\s+\d+\b'
    
    WN_APP = r'\b\d+\s+Wn\.\s*App\.?\s*2d\s+\d+\b'
    WASH_APP = r'\b\d+\s+Wash\.\s*App\.?\s*2d\s+\d+\b'
    
    # ============================================================================
    # STATE REPORTERS - CALIFORNIA
    # ============================================================================
    
    CAL_2D = r'\b\d+\s+Cal\.\s*2d\s+\d+\b'
    CAL_3D = r'\b\d+\s+Cal\.\s*3d\s+\d+\b'
    CAL_4TH = r'\b\d+\s+Cal\.\s*4th\s+\d+\b'
    CAL_5TH = r'\b\d+\s+Cal\.\s*5th\s+\d+\b'
    CAL_APP = r'\b\d+\s+Cal\.\s*App\.?\s*(2d|3d|4th|5th)?\s+\d+\b'
    
    # ============================================================================
    # NEUTRAL/PUBLIC DOMAIN CITATIONS (Official State Citations)
    # ============================================================================
    
    # New Mexico: 2017-NM-007, 2017-NMCA-042 (Court of Appeals)
    NEUTRAL_NM = r'\b20\d{2}-NM(?:CA)?-\d{1,5}\b'
    
    # Other states (space-separated format): 2017 ND 123
    NEUTRAL_ND = r'\b20\d{2}\s+ND\s+\d{1,5}\b'  # North Dakota
    NEUTRAL_OK = r'\b20\d{2}\s+OK\s+\d{1,5}\b'  # Oklahoma  
    NEUTRAL_SD = r'\b20\d{2}\s+SD\s+\d{1,5}\b'  # South Dakota
    NEUTRAL_UT = r'\b20\d{2}\s+UT\s+\d{1,5}\b'  # Utah
    NEUTRAL_WI = r'\b20\d{2}\s+WI\s+\d{1,5}\b'  # Wisconsin
    NEUTRAL_WY = r'\b20\d{2}\s+WY\s+\d{1,5}\b'  # Wyoming
    NEUTRAL_MT = r'\b20\d{2}\s+MT\s+\d{1,5}\b'  # Montana
    
    # ============================================================================
    # ONLINE DATABASES
    # ============================================================================
    
    WESTLAW = r'\b\d{4}\s+WL\s+\d{1,12}\b'
    WESTLAW_ALT = r'\b\d{4}\s+Westlaw\s+\d{1,12}\b'
    LEXIS = r'\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d{1,12}\b'
    LEXIS_ALT = r'\b\d{4}\s+LEXIS\s+\d{1,12}\b'
    
    # ============================================================================
    # LEGACY PATTERNS (kept for compatibility)
    # ============================================================================
    
    FEDERAL_REPORTER = r"\b(\d{1,5})\s+F\.(?:\s*(\d*(?:st|nd|rd|th|d)))?\s+(\d{1,12})\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    US_REPORTS = r"\b\d{1,5}\s+U\.?\s*S\.?\s*\d{1,12}\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    SUPREME_COURT_REPORTER = r"\b\d{1,5}\s+S\.?\s*Ct\.?\s*\d{1,12}\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    WASHINGTON_REPORTS = r"\b(\d{1,5})\s+Wn\.(?:\s*(\d*(?:d|nd|rd|th)))?(?:\s+App\.)?[\s\r\n]+(\d{1,12})\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    STATE_REPORTER_DASHED = r"\b(\d{1,5})-([A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?)-(\d{1,12})\b"
    
    @classmethod
    def get_compiled_patterns(cls) -> Dict[str, re.Pattern]:
        """
        Get all citation patterns as compiled regex objects.
        
        Returns:
            Dict mapping pattern names to compiled regex patterns
        """
        return {
            # Federal reporters
            'us_supreme': re.compile(cls.US_SUPREME, re.IGNORECASE),
            'us_supreme_alt': re.compile(cls.US_SUPREME_ALT, re.IGNORECASE),
            's_ct': re.compile(cls.S_CT, re.IGNORECASE),
            'l_ed': re.compile(cls.L_ED, re.IGNORECASE),
            'l_ed_2d': re.compile(cls.L_ED_2D, re.IGNORECASE),
            'f_2d': re.compile(cls.F_2D, re.IGNORECASE),
            'f_3d': re.compile(cls.F_3D, re.IGNORECASE),
            'f_4th': re.compile(cls.F_4TH, re.IGNORECASE),
            'f_supp': re.compile(cls.F_SUPP, re.IGNORECASE),
            'f_supp_2d': re.compile(cls.F_SUPP_2D, re.IGNORECASE),
            'f_supp_3d': re.compile(cls.F_SUPP_3D, re.IGNORECASE),
            
            # State reporters - Pacific
            'p_general': re.compile(cls.P_GENERAL, re.IGNORECASE),
            'p_2d': re.compile(cls.P_2D, re.IGNORECASE),
            'p_3d': re.compile(cls.P_3D, re.IGNORECASE),
            
            # State reporters - Washington
            'wn_first': re.compile(cls.WN_FIRST, re.IGNORECASE),
            'wash_first': re.compile(cls.WASH_FIRST, re.IGNORECASE),
            'wn_2d': re.compile(cls.WN_2D, re.IGNORECASE),
            'wn_2d_space': re.compile(cls.WN_2D_SPACE, re.IGNORECASE),
            'wash_2d': re.compile(cls.WASH_2D, re.IGNORECASE),
            'wn_3d': re.compile(cls.WN_3D, re.IGNORECASE),
            'wn_app': re.compile(cls.WN_APP, re.IGNORECASE),
            'wash_app': re.compile(cls.WASH_APP, re.IGNORECASE),
            
            # State reporters - California
            'cal_2d': re.compile(cls.CAL_2D, re.IGNORECASE),
            'cal_3d': re.compile(cls.CAL_3D, re.IGNORECASE),
            'cal_4th': re.compile(cls.CAL_4TH, re.IGNORECASE),
            'cal_5th': re.compile(cls.CAL_5TH, re.IGNORECASE),
            'cal_app': re.compile(cls.CAL_APP, re.IGNORECASE),
            
            # Neutral/Public Domain Citations
            'neutral_nm': re.compile(cls.NEUTRAL_NM, re.IGNORECASE),
            'neutral_nd': re.compile(cls.NEUTRAL_ND, re.IGNORECASE),
            'neutral_ok': re.compile(cls.NEUTRAL_OK, re.IGNORECASE),
            'neutral_sd': re.compile(cls.NEUTRAL_SD, re.IGNORECASE),
            'neutral_ut': re.compile(cls.NEUTRAL_UT, re.IGNORECASE),
            'neutral_wi': re.compile(cls.NEUTRAL_WI, re.IGNORECASE),
            'neutral_wy': re.compile(cls.NEUTRAL_WY, re.IGNORECASE),
            'neutral_mt': re.compile(cls.NEUTRAL_MT, re.IGNORECASE),
            
            # Online databases
            'westlaw': re.compile(cls.WESTLAW, re.IGNORECASE),
            'westlaw_alt': re.compile(cls.WESTLAW_ALT, re.IGNORECASE),
            'lexis': re.compile(cls.LEXIS, re.IGNORECASE),
            'lexis_alt': re.compile(cls.LEXIS_ALT, re.IGNORECASE),
        }
    
    @classmethod
    def get_legacy_patterns(cls) -> Dict[str, str]:
        """
        Get legacy pattern definitions (for backwards compatibility).
        
        Returns:
            Dict mapping pattern names to raw regex strings
        """
        return {
            "federal_reporter": cls.FEDERAL_REPORTER,
            "us_reports": cls.US_REPORTS,
            "supreme_court_reporter": cls.SUPREME_COURT_REPORTER,
            "westlaw": cls.WESTLAW,
            "lexis": cls.LEXIS,
            "washington_reports": cls.WASHINGTON_REPORTS,
            "state_reporter_dashed": cls.STATE_REPORTER_DASHED,
        }


# Maintain old CITATION_PATTERNS dict for backwards compatibility
CITATION_PATTERNS = CitationPatterns.get_legacy_patterns()

COMMON_CITATION_FORMATS = [
    r"\b[A-Z][A-Za-z]+\s+v\.\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\b",
    r"\b\d{1,5}\s+[A-Za-z\.\s]+\d{1,12}\b",
    r"\b\d{1,5}\s+[A-Za-z\.\s]+\d{1,12}\s*,\s*\d+\b",
    r"\b\d{1,5}\s+[A-Za-z\.\s]+\d{1,12}\s*\(\d{4}\)",
    r"\b\d{4}\s+WL\s+\d{1,12}\b",
    r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d{1,12}\b",
    # Dash-separated state reporters
    r"\b\d{1,5}-[A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?-\d{1,12}\b",
]

LEGAL_REPORTERS = {
    "U.S.": "United States Reports",
    "S. Ct.": "Supreme Court Reporter",
    "L. Ed.": "Lawyers Edition",
    "L. Ed. 2d": "Lawyers Edition, Second Series",
    "F.": "Federal Reporter",
    "F.2d": "Federal Reporter, Second Series",
    "F.3d": "Federal Reporter, Third Series",
    "F.4th": "Federal Reporter, Fourth Series",
    "F.5th": "Federal Reporter, Fifth Series",
    "F.6th": "Federal Reporter, Sixth Series",
    "F. Supp.": "Federal Supplement",
    "F. Supp. 2d": "Federal Supplement, Second Series",
    "F. Supp. 3d": "Federal Supplement, Third Series",
    "A.": "Atlantic Reporter",
    "A.2d": "Atlantic Reporter, Second Series",
    "A.3d": "Atlantic Reporter, Third Series",
    "N.E.": "Northeastern Reporter",
    "N.E.2d": "Northeastern Reporter, Second Series",
    "N.E.3d": "Northeastern Reporter, Third Series",
    "N.W.": "North Western Reporter",
    "N.W.2d": "North Western Reporter, Second Series",
    "P.": "Pacific Reporter",
    "P.2d": "Pacific Reporter, Second Series",
    "P.3d": "Pacific Reporter, Third Series",
    "S.E.": "Southeastern Reporter",
    "S.E.2d": "Southeastern Reporter, Second Series",
    "So.": "Southern Reporter",
    "So.2d": "Southern Reporter, Second Series",
    "So.3d": "Southern Reporter, Third Series",
    "S.W.": "South Western Reporter",
    "S.W.2d": "South Western Reporter, Second Series",
    "S.W.3d": "South Western Reporter, Third Series",
    "Wn.": "Washington Reports",
    "Wn.2d": "Washington Reports, Second Series",
    "Wash. App.": "Washington Appellate Reports",
    "WL": "Westlaw",
    # State Reporters (dash-separated format support)
    "Ohio": "Ohio Reports",
    "Ohio St.": "Ohio State Reports",
    "Ohio St. 2d": "Ohio State Reports, Second Series",
    "Ohio St. 3d": "Ohio State Reports, Third Series",
    "Ohio App.": "Ohio Appellate Reports",
    "Cal.": "California Reports",
    "Cal. 2d": "California Reports, Second Series",
    "Cal. 3d": "California Reports, Third Series",
    "Cal. 4th": "California Reports, Fourth Series",
    "Cal. 5th": "California Reports, Fifth Series",
    "N.Y.": "New York Reports",
    "N.Y.2d": "New York Reports, Second Series",
    "N.Y.3d": "New York Reports, Third Series",
    "Ill.": "Illinois Reports",
    "Ill. 2d": "Illinois Reports, Second Series",
    "Tex.": "Texas Reports",
    "Fla.": "Florida Reports",
}


def normalize_washington_citation(citation_text):
    """
    Normalize Washington state citations to standard format.
    Converts 'Wn.' to 'Wash.' and handles series indicators.

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text
    """
    import re

    pattern = r"(\d{1,3})\s+Wn\.(?:\s*(\d*[a-z]*))?(?:\s+App\.)?\s+(\d+)"

    def replacer(match):
        volume = match.group(1)
        series = (match.group(2) or "").lower()
        page = match.group(3)

        is_appellate = "app" in match.group(0).lower()

        if "2" in series:
            series = "2d"
        elif "3" in series:
            series = "3d"
        elif "4" in series:
            series = "4th"
        else:
            series = ""

        parts = [volume, "Wash."]
        if series:
            parts.append(series)
        if is_appellate:
            parts.append("App.")
        parts.append(page)

        return " ".join(parts)

    normalized = re.sub(pattern, replacer, citation_text, flags=re.IGNORECASE)

    normalized = re.sub(r"\\s+", " ", normalized).strip()

    return normalized


def normalize_federal_reporter_citation(citation_text):
    """
    Normalize Federal Reporter citations to standard format.
    Converts variations like '2nd' to '2d', '3rd' to '3d', etc.

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text
    """
    import re

    pattern = r"(\d{1,3}\s+F\.)\s*(\d*)(st|nd|rd|th|d)(\s+\d+)"

    def replacer(match):
        series_map = {
            "1st": "1st",
            "2nd": "2d",
            "3rd": "3d",
            "4th": "4th",
            "5th": "5th",
            "6th": "6th",
            "1th": "1st",  # Handle potential typos
            "2th": "2d",
            "3th": "3d",
        }

        prefix = match.group(1)
        number = match.group(2)
        suffix = match.group(3)
        rest = match.group(4)

        series = f"{number or ''}{suffix}"
        normalized_series = series_map.get(series.lower(), series)

        if normalized_series == "1st":
            return f"{prefix}{rest}"

        return f"{prefix} {normalized_series}{rest}"

    normalized = re.sub(pattern, replacer, citation_text, flags=re.IGNORECASE)

    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_dashed_citation(citation_text):
    """
    Normalize dash-separated state reporter citations to standard format.
    Converts '123-Ohio-456' to '123 Ohio 456'
    
    Args:
        citation_text (str): The citation text to normalize
        
    Returns:
        str: Normalized citation text with spaces instead of dashes
    """
    import re
    
    # Pattern: volume-reporter-page
    pattern = r'\b(\d{1,5})-([A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?)-(\d{1,12})\b'
    
    def replacer(match):
        volume = match.group(1)
        reporter = match.group(2)
        page = match.group(3)
        return f"{volume} {reporter} {page}"
    
    normalized = re.sub(pattern, replacer, citation_text)
    return normalized
