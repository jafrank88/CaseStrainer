import re
from typing import Optional, Tuple, Dict, List, Any
import logging
import string
from rapidfuzz import fuzz
import unicodedata
import difflib
import requests
from urllib.parse import urlparse, quote_plus
import html
import time
import json
from bs4 import BeautifulSoup
from src.citation_normalizer import normalize_citation, generate_citation_variants

# Set up debug logging
logging.basicConfig(filename='case_name_debug.log', level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Set up module logger
logger = logging.getLogger(__name__)

def log_debug(message):
    """Helper function to log debug messages to file"""
    logging.debug(message)
    print(f"[DEBUG] {message}")

# Add a global cache for recently extracted case names to handle "Id." citations and improve performance
_recent_case_names = []
_case_name_cache = {}  # Cache for citation to case name mapping
_parallel_citation_cache = {}  # Cache for mapping normalized citation keys to case name and date
_CACHE_SIZE_LIMIT = 1000  # Limit cache size to prevent memory issues

# Add comprehensive legal abbreviation mapping
ABBREVIATION_MAP = {
    'Dep': 'Department',
    'Emp': 'Employment',
    'Cent.': 'Central',
    'Reg': 'Regional',
    'Indus.': 'Industries',
    'Sec.': 'Security',
    'Ret.': 'Retirement',
    'Sys.': 'Systems',
    'Ass\'n': 'Association',
    'Inc.': 'Inc.',
    'Co.': 'Co.',
    'LLC': 'LLC',
    'Corp.': 'Corp.',
    'Ltd.': 'Ltd.',
    'L.L.C.': 'L.L.C.',
    'L.P.': 'L.P.',
    'P.S.': 'P.S.',
    'P.C.': 'P.C.',
    'P.A.': 'P.A.',
    'P.L.L.C.': 'P.L.L.C.',
    'L.L.P.': 'L.L.P.',
    'N.A.': 'N.A.',
    'N.V.': 'N.V.',
    'S.A.': 'S.A.',
    'S.p.A.': 'S.p.A.',
    'A.G.': 'A.G.',
    'B.V.': 'B.V.',
    'S.à r.l.': 'S.à r.l.',
    'PLC': 'PLC',
    'GmbH': 'GmbH',
    'SNC': 'SNC',
    'SCS': 'SCS',
    'SCA': 'SCA',
    'SAS': 'SAS',
    'S.A.S.': 'S.A.S.',
    'S.A.R.L.': 'S.A.R.L.',
    'S.A. de C.V.': 'S.A. de C.V.',
    'S.A.B. de C.V.': 'S.A.B. de C.V.'
}

def identify_site_type(url: str) -> str:
    """Identify the type of legal site from URL."""
    url_lower = url.lower()
    
    if 'courtlistener.com' in url_lower:
        return 'courtlistener'
    elif 'justia.com' in url_lower:
        return 'justia'
    elif 'findlaw.com' in url_lower:
        return 'findlaw'
    elif 'casetext.com' in url_lower:
        return 'casetext'
    elif 'leagle.com' in url_lower:
        return 'leagle'
    elif 'supremecourt.gov' in url_lower or 'supremecourtus.gov' in url_lower:
        return 'supreme_court'
    elif 'law.cornell.edu' in url_lower or 'lii.org' in url_lower:
        return 'cornell'
    elif 'scholar.google.com' in url_lower:
        return 'google_scholar'
    elif 'vlex.com' in url_lower:
        return 'vlex'
    elif 'westlaw.com' in url_lower or 'westlawnext.com' in url_lower:
        return 'westlaw'
    elif 'casemine.com' in url_lower:
        return 'casemine'
    elif 'fastcase.com' in url_lower:
        return 'fastcase'
    elif 'bloomberglaw.com' in url_lower:
        return 'bloomberglaw'
    else:
        return 'generic'

def extract_case_name_by_site(html_content: str, citation: str, site_type: str) -> str:
    """Extract case name using site-specific patterns."""
    
    if site_type == "courtlistener":
        return extract_case_name_courtlistener(html_content, citation)
    elif site_type == "justia":
        return extract_case_name_justia(html_content, citation)
    elif site_type == "findlaw":
        return extract_case_name_findlaw(html_content, citation)
    elif site_type == "casetext":
        return extract_case_name_casetext(html_content, citation)
    elif site_type == "leagle":
        return extract_case_name_leagle(html_content, citation)
    elif site_type == "supreme_court":
        return extract_case_name_supreme_court(html_content, citation)
    elif site_type == "cornell":
        return extract_case_name_cornell(html_content, citation)
    elif site_type == "google_scholar":
        return extract_case_name_google_scholar(html_content, citation)
    elif site_type == "vlex":
        return extract_case_name_vlex(html_content, citation)
    elif site_type == "westlaw":
        return extract_case_name_westlaw(html_content, citation)
    elif site_type == "casemine":
        return extract_case_name_casemine(html_content, citation)
    elif site_type == "fastcase":
        return extract_case_name_fastcase(html_content, citation)
    elif site_type == "bloomberglaw":
        return extract_case_name_bloomberglaw(html_content, citation)
    else:
        return extract_case_name_generic(html_content, citation)

def extract_case_name_courtlistener(html_content: str, citation: str) -> str:
    """Extract case name from CourtListener pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-name"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-name[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-name[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_justia(html_content: str, citation: str) -> str:
    """Extract case name from Justia pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_findlaw(html_content: str, citation: str) -> str:
    """Extract case name from FindLaw pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_casetext(html_content: str, citation: str) -> str:
    """Extract case name from CaseText pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_leagle(html_content: str, citation: str) -> str:
    """Extract case name from Leagle pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_supreme_court(html_content: str, citation: str) -> str:
    """Extract case name from Supreme Court pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_cornell(html_content: str, citation: str) -> str:
    """Extract case name from Cornell LII pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_google_scholar(html_content: str, citation: str) -> str:
    """Extract case name from Google Scholar pages."""
    patterns = [
        r'<h3[^>]*class="[^"]*gs_rt[^"]*"[^>]*>([^<]+)</h3>',
        r'<h3[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h3>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="gs_rt"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*gs_rt[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*gs_rt[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_vlex(html_content: str, citation: str) -> str:
    """Extract case name from vLex pages."""
    patterns = [
        # vLex specific patterns
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h2[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h2>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_westlaw(html_content: str, citation: str) -> str:
    """Extract case name from Westlaw pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_casemine(html_content: str, citation: str) -> str:
    """Extract case name from CaseMine pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_fastcase(html_content: str, citation: str) -> str:
    """Extract case name from FastCase pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_bloomberglaw(html_content: str, citation: str) -> str:
    """Extract case name from Bloomberg Law pages."""
    patterns = [
        r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'class="case-title"[^>]*>([^<]*)</',
        r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_generic(html_content: str, citation: str) -> str:
    """Extract case name using generic patterns for unknown sites."""
    patterns = [
        r'<h1[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h1>',
        r'<h2[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h2>',
        r'<h3[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</h3>',
        r'<title[^>]*>([^<]*' + re.escape(citation) + r'[^<]*)</title>',
        r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)</div>',
        r'<span[^>]*class="[^"]*case[^"]*"[^>]*>([^<]*)</span>',
        r'<div[^>]*class="[^"]*case[^"]*"[^>]*>([^<]*)</div>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            case_name = clean_case_name(match.group(1))
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_from_url_content(url: str, citation: str) -> str:
    """
    Extract case name from URL content when direct page access fails.
    This is a fallback method for cases where pages return 410, require authentication, etc.
    """
    try:
        # For Casetext URLs, we can extract some info from the URL itself
        if 'casetext.com/case/' in url:
            # Extract case name from URL path
            case_path = url.split('/case/')[-1]
            if case_path:
                # Convert URL slug to readable case name
                case_name = case_path.replace('-', ' ').replace('_', ' ')
                # Capitalize properly
                case_name = ' '.join(word.capitalize() for word in case_name.split())
                # Handle common abbreviations
                case_name = case_name.replace('Llc', 'LLC').replace('Inc', 'Inc.').replace('Corp', 'Corp.')
                return case_name
        
        return ""
        
    except Exception as e:
        log_debug(f"Error extracting case name from URL content: {e}")
        return ""

def extract_metadata_from_google_snippet(url: str, search_title: str = "", search_snippet: str = "") -> dict:
    """
    Extract metadata from Google search result snippets when the actual page is unavailable.
    This is a fallback method for cases where pages return 410, require authentication, etc.
    
    Args:
        url: The URL that was searched
        search_title: The title from Google search results
        search_snippet: The snippet from Google search results
        
    Returns:
        dict: Extracted metadata including case name, year, citation, etc.
    """
    try:
        extracted_data = {
            'canonical_name': '',
            'url': url,
            'parallel_citations': [],
            'year': '',
            'court': '',
            'docket': '',
            'source': 'google_snippet'
        }
        
        # Combine title and snippet for analysis
        combined_text = f"{search_title} {search_snippet}"
        
        # Extract case name from search title (most reliable)
        if search_title:
            # Remove site name suffixes like " - Casetext", " - Justia", etc.
            clean_title = re.sub(r'\s*-\s*(Casetext|Justia|FindLaw|Leagle|vLex|CaseMine|Google Scholar|Supreme Court|Court of Appeals|District Court).*$', '', search_title, flags=re.IGNORECASE)
            
            # Look for case name patterns in the title
            case_patterns = [
                r'([A-Z][A-Za-z\s,]+(?:\s+LLC|\s+Inc\.?|\s+Corp\.?)?\s+v\.\s+[A-Z][A-Za-z\s,]+(?:\s+LLC|\s+Inc\.?|\s+Corp\.?)?)',
                r'([A-Z][A-Za-z\s,]+(?:\s+LLC|\s+Inc\.?|\s+Corp\.?)?\s+vs\.\s+[A-Z][A-Za-z\s,]+(?:\s+LLC|\s+Inc\.?|\s+Corp\.?)?)',
                r'([A-Z][A-Za-z\s,]+(?:\s+LLC|\s+Inc\.?|\s+Corp\.?)?\s+versus\s+[A-Z][A-Za-z\s,]+(?:\s+LLC|\s+Inc\.?|\s+Corp\.?)?)'
            ]
            
            for pattern in case_patterns:
                match = re.search(pattern, clean_title)
                if match:
                    case_name = match.group(1).strip()
                    # Clean up the case name
                    case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
                    case_name = case_name.replace(' ,', ',')  # Fix spacing around commas
                    extracted_data['canonical_name'] = case_name
                    break
        
        # If no case name found in title, try URL extraction
        if not extracted_data['canonical_name']:
            extracted_data['canonical_name'] = extract_case_name_from_url_content(url, "")
        
        # Extract citation from snippet
        citation_patterns = [
            r'(\d+\s+[A-Z]\.\d+\s+\d+)',  # e.g., "546 P.3d 385"
            r'(\d+\s+[A-Z]\.\s*\d+\s*[a-z]+\s+\d+)',  # e.g., "546 P. 3d 385"
            r'(\d+\s+[A-Z][A-Za-z]+\s+\d+)',  # e.g., "546 Pacific 3d 385"
            r'(\d+\s+[A-Z]\.\s*\d+\s*\(\d+\))',  # e.g., "546 P. 3d (2024)"
        ]
        
        for pattern in citation_patterns:
            match = re.search(pattern, combined_text)
            if match:
                citation = match.group(1).strip()
                extracted_data['parallel_citations'].append(citation)
                break
        
        # Extract year from snippet or title
        year_patterns = [
            r'\b(19|20)\d{2}\b',  # Standard year format
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+(19|20)\d{2}',  # Date format
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                if len(match.group()) == 4:  # Just the year
                    extracted_data['year'] = match.group()
                else:  # Full date, extract year
                    year_match = re.search(r'(19|20)\d{2}', match.group())
                    if year_match:
                        extracted_data['year'] = year_match.group()
                break
        
        # Extract court information
        court_patterns = [
            r'(Supreme Court|Court of Appeals|District Court|Circuit Court|Superior Court)',
            r'([A-Z][a-z]+ Court)',
        ]
        
        for pattern in court_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                extracted_data['court'] = match.group(1)
                break
        
        return extracted_data
        
    except Exception as e:
        log_debug(f"Error extracting metadata from Google snippet: {e}")
        return {
            'canonical_name': '',
            'url': url,
            'parallel_citations': [],
            'year': '',
            'court': '',
            'docket': '',
            'source': 'google_snippet'
        }

def extract_case_name_from_page(html_content: str, citation: str, source_url: str = "") -> str:
    """
    Extract case name from HTML page content.
    
    Args:
        html_content: The HTML content of the page
        citation: The citation being searched for
        source_url: The source URL (optional, for site identification)
        
    Returns:
        str: The extracted case name or empty string if not found
    """
    import warnings
    warnings.warn('extract_case_name_from_page is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(html_content, citation, input_type='html', source_url=source_url)

def extract_case_name_from_context_split(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_best instead."""
    import warnings
    warnings.warn('extract_case_name_from_context_split is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(args[0] if args else "", args[1] if len(args) > 1 else "", input_type='text')

def extract_case_name_from_context(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_best instead."""
    import warnings
    warnings.warn('extract_case_name_from_context is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(args[0] if args else "", args[1] if len(args) > 1 else "", input_type='text')

def extract_case_name_from_context_context_based(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_best instead."""
    import warnings
    warnings.warn('extract_case_name_from_context_context_based is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(args[0] if args else "", args[1] if len(args) > 1 else "", input_type='text')

def extract_case_name_from_context_context_based_enhanced(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_best instead."""
    import warnings
    warnings.warn('extract_case_name_from_context_context_based_enhanced is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(args[0] if args else "", args[1] if len(args) > 1 else "", input_type='text')

def extract_case_name_from_citation_line(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_best instead."""
    import warnings
    warnings.warn('extract_case_name_from_citation_line is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(args[0] if args else "", args[1] if len(args) > 1 else "", input_type='text')

def extract_case_name_from_text(text: str, citation_text: str, all_citations: list = None, canonical_name: str = None) -> Optional[str]:
    """
    Extract case name from text using multiple strategies.
    
    Args:
        text: The full text
        citation_text: The specific citation to find case name for
        all_citations: List of all citations in the text (for context)
        canonical_name: Known canonical name for the case
        
    Returns:
        str: Extracted case name or empty string
    """
    if not text or not citation_text:
        return ""
    
    # Ensure citation_text is a string
    if not isinstance(citation_text, str):
        try:
            citation_text = str(citation_text)
        except Exception as e:
            logger.warning(f"Failed to convert citation_text to string: {e}")
            return ""
    
    # Strategy 1: Use canonical name if provided
    if canonical_name:
        return canonical_name
    
    # Strategy 2: Look for case name in context around the citation
    citation_index = text.find(citation_text)
    if citation_index != -1:
        context_before = text[max(0, citation_index - 1000):citation_index]
        case_name = extract_case_name_from_context(context_before, citation_text)
        if case_name:
            return case_name
    
    # Strategy 3: Look for case name in the entire text (global search)
    # This is useful for cases where the case name appears earlier in the document
    lines = text.split('\n')
    for line in lines:
        if citation_text in line:
            case_name = extract_case_name_from_citation_line(line, canonical_name=canonical_name)
            if case_name:
                return case_name
    
    # Strategy 4: Use shared case name detection if multiple citations are provided
    if all_citations:
        try:
            # Create citation objects for shared case name detection
            citation_objs = []
            for citation in all_citations:
                # Ensure citation is a string
                if not isinstance(citation, str):
                    citation = str(citation)
                idx = text.find(citation)
                if idx != -1:
                    citation_objs.append({
                        'citation': citation,
                        'start_index': idx,
                        'end_index': idx + len(citation)
                    })
            
            if citation_objs:
                shared_names = find_shared_case_name_for_citations(text, citation_objs)
                # Ensure shared_names is a dictionary and citation_text is a valid key
                if isinstance(shared_names, dict) and citation_text in shared_names and shared_names[citation_text]:
                    return shared_names[citation_text]
        except Exception as e:
            logger.warning(f"Error in shared case name detection: {e}")
    
    return ""

def is_citation_like(text: str) -> bool:
    """
    Check if text looks like a citation rather than a case name.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text looks like a citation
    """
    if not text:
        return False
    
    # Citation patterns
    citation_patterns = [
        r'\d+\s+[A-Z]\.\s*\d+',  # e.g., "123 F. 456"
        r'\d+\s+[A-Z]{2,}\.\s*\d+',  # e.g., "123 Wash. 456"
        r'\d+\s+U\.\s*S\.\s*\d+',  # e.g., "123 U. S. 456"
        r'\d+\s+S\.\s*Ct\.\s*\d+',  # e.g., "123 S. Ct. 456"
        r'\d+\s+L\.\s*Ed\.\s*\d+',  # e.g., "123 L. Ed. 456"
        r'\d{4}\s+WL\s+\d+',  # e.g., "2023 WL 123456"
        r'\d{4}\s+LEXIS\s+\d+',  # e.g., "2023 LEXIS 123456"
    ]
    
    for pattern in citation_patterns:
        if re.search(pattern, text):
            return True
    
    # Check if text is too short or too long for a case name
    if len(text) < 3 or len(text) > 200:
        return True
    
    # Check if text contains mostly numbers
    if re.match(r'^\d+\s*$', text):
        return True
    
    return False

def clean_case_name(case_name: str) -> str:
    """Clean and normalize a case name."""
    if not case_name:
        return ""
    
    # Remove HTML tags
    case_name = re.sub(r'<[^>]+>', '', case_name)
    
    # Clean up whitespace
    case_name = re.sub(r'\s+', ' ', case_name)
    case_name = case_name.strip()
    
    # Remove common unwanted text
    case_name = re.sub(r'^\s*-\s*', '', case_name)  # Remove leading dash
    case_name = re.sub(r'\s*-\s*$', '', case_name)  # Remove trailing dash
    
    # Remove common introductory phrases (more comprehensive)
    intro_patterns = [
        r'^(?:the\s+)?(?:case\s+of\s+|supreme\s+court\s+in\s+|court\s+of\s+appeals\s+in\s+)',
        r'^(?:the\s+)?(?:washington\s+supreme\s+court\s+in\s+|washington\s+court\s+of\s+appeals\s+in\s+)',
        r'^(?:in\s+the\s+case\s+of\s+|in\s+the\s+matter\s+of\s+)',
        r'^(?:the\s+)?(?:matter\s+of\s+|proceeding\s+of\s+)',
        r'^(?:in\s+(?!re\b)|the\s+case\s+)',  # Don't remove 'in' if it's followed by 're'
        r'^(?:and\s+the\s+court\s+of\s+appeals\s+in\s+)',
        # Add patterns for common legal writing phrases
        r'^(?:quoting\s+|cited\s+in\s+|referenced\s+in\s+|as\s+stated\s+in\s+|as\s+held\s+in\s+)',
        r'^(?:the\s+)?(?:court\s+in\s+|judge\s+in\s+|opinion\s+in\s+)',
        r'^(?:see\s+|cf\.\s+|e\.g\.,?\s+|i\.e\.,?\s+)',
        r'^(?:according\s+to\s+|per\s+|as\s+per\s+)',
    ]
    for pattern in intro_patterns:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
    
    # Remove citation from case name if present
    citation_patterns = [
        r'\d+\s+[A-Z]+\.[\d\w\.]+\s+\d+',  # e.g., "181 Wash.2d 391"
        r'\d+\s+[A-Z]+\s+\d+',  # e.g., "181 Wash 2d 391"
        r'\d+\s+[A-Z]+\.[\d\w\.]+',  # e.g., "181 Wash.2d"
    ]
    
    for pattern in citation_patterns:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
    
    # Clean up again after citation removal
    case_name = re.sub(r'\s+', ' ', case_name)
    case_name = case_name.strip()
    
    return case_name

def is_valid_case_name(case_name: str) -> bool:
    """Check if a case name is valid."""
    if not case_name or len(case_name) < 5:
        return False
    
    # Clean the case name first
    cleaned_case_name = clean_case_name(case_name)
    
    # Check for common invalid introductory phrases that might have been missed
    invalid_intro_patterns = [
        r'^(?:quoting\s+|cited\s+in\s+|referenced\s+in\s+|as\s+stated\s+in\s+|as\s+held\s+in\s+)',
        r'^(?:the\s+)?(?:court\s+in\s+|judge\s+in\s+|opinion\s+in\s+)',
        r'^(?:see\s+|cf\.\s+|e\.g\.,?\s+|i\.e\.,?\s+)',
        r'^(?:according\s+to\s+|per\s+|as\s+per\s+)',
        r'^(?:unknown\s+case|case\s+not\s+found|no\s+case\s+name)',
    ]
    
    for pattern in invalid_intro_patterns:
        if re.match(pattern, cleaned_case_name, re.IGNORECASE):
            return False
    
    # Must contain typical case name patterns
    case_patterns = [
        r'\b[A-Z][a-z]+\s+(?:v\.|vs\.|versus)\s+[A-Z][a-z]+',  # e.g., "Smith v. Jones"
        r'\bIn\s+re\s+[A-Z][a-z]+',  # e.g., "In re Smith"
        r'\b[A-Z][a-z]+\s+(?:ex\s+rel\.|ex\s+rel)\s+[A-Z][a-z]+',  # e.g., "State ex rel. Smith"
    ]
    
    for pattern in case_patterns:
        if re.search(pattern, cleaned_case_name, re.IGNORECASE):
            return True
    
    return False

def extract_case_name_from_citation_line(line: str, canonical_name: str = None) -> Optional[str]:
    """
    Extract case name from a line that contains a citation.
    Optionally, use canonical_name for fuzzy/abbreviation matching.
    
    Args:
        line: Line of text
        canonical_name: Canonical case name for fallback fuzzy matching
        
    Returns:
        str: Extracted case name or None
    """
    if not line:
        return None
    
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    # Expanded regex to allow abbreviations, all-caps, and 'In re' style names
    patterns = [
        r'(([A-Z][A-Z\.]+|[A-Z][A-Za-z\'\-\s,\.]+(?:\s+[A-Z])?)\s+v\.\s+[A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(([A-Z][A-Z\.]+|[A-Z][A-Za-z\'\-\s,\.]+(?:\s+[A-Z])?)\s+vs\.\s+[A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(In\s+re\s+[A-Za-z\'\-\s,\.]+)',
        r'(Estate\s+of\s+[A-Za-z\'\-\s,\.]+)',
        r'(Matter\s+of\s+[A-Za-z\'\-\s,\.]+)',
        r'(Ex\s+parte\s+[A-Za-z\'\-\s,\.]+)',
    ]
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, line, re.IGNORECASE))
        if matches:
            logger.info(f"[extract_case_name_from_citation_line] Pattern: {pattern} Matches: {[m.group(1) for m in matches]}")
            # Use the last match (closest to citation)
            match = matches[-1]
            case_name = clean_case_name(match.group(1))
            if case_name and not is_citation_like(case_name):
                return case_name
    
    # Fallback: fuzzy match abbreviations to canonical name
    if canonical_name:
        from rapidfuzz import fuzz
        v_matches = re.findall(r'([A-Z][A-Za-z\.\'\-\s,]+?(?:\s+[A-Z])?\s+v\.\s+[A-Z][A-Za-z\.\'\-\s,]+)', line)
        logger.info(f"[extract_case_name_from_citation_line] Fallback v_matches: {v_matches}")
        for candidate in v_matches:
            score = fuzz.ratio(candidate.lower(), canonical_name.lower())
            logger.info(f"[extract_case_name_from_citation_line] Fallback candidate: {candidate}, score: {score}")
            if score > 80:
                return candidate
    
    return None

def extract_case_name_from_context_context_based(context_before: str, citation: str) -> str:
    """Extract case name from context around a citation using pattern matching."""
    idx = context_before.find(citation)
    if idx == -1:
        return ""
    
    # Look for case name before the citation
    before_context = context_before[max(0, idx - 500):idx]
    
    # Look for patterns like "In [Case Name]," or "[Case Name] v. [Party]"
    patterns = [
        r'In\s+([^,]+?),\s*\d+',  # "In Case Name, 123"
        r'([^,]+?)\s+v\.\s+[^,]+?,\s*\d+',  # "Case Name v. Party, 123"
        r'([^,]+?)\s+vs\.\s+[^,]+?,\s*\d+',  # "Case Name vs. Party, 123"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, before_context, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def extract_case_name_from_context_context_based_enhanced(context_before: str, citation: str) -> str:
    """Enhanced context-based case name extraction with more patterns."""
    idx = context_before.find(citation)
    if idx == -1:
        return ""
    
    # Look for case name before the citation
    before_context = context_before[max(0, idx - 500):idx]
    
    # Enhanced patterns for case name extraction
    patterns = [
        # Standard v. patterns
        r'([A-Z][A-Za-z\s,\.]+?(?:\s+[A-Z])?\s+v\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'([A-Z][A-Za-z\s,\.]+?(?:\s+[A-Z])?\s+vs\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'([A-Z][A-Za-z\s,\.]+?(?:\s+[A-Z])?\s+versus\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        # In re patterns
        r'(?:^|\s)(In\s+re\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)(Estate\s+of\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)(Matter\s+of\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)(Ex\s+parte\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        # State/People patterns
        r'(?:^|\s)([A-Z][A-Za-z\s,\.]+\s+ex\s+rel\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)(People\s+v\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)(State\s+v\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)(United\s+States\s+v\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        # Multiple parties
        r'(?:^|\s)([A-Z][A-Za-z\s,\.]+\s+et\s+al\.\s+v\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
        r'(?:^|\s)([A-Z][A-Za-z\s,\.]+\s*&\s*[A-Z][A-Za-z\s,\.]+\s+v\.\s+[A-Z][A-Za-z\s,\.]+?)(?:\s*[,;]|\s*$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, before_context, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            case_name = clean_case_name(case_name)
            if is_valid_case_name(case_name):
                return case_name
    
    return ""

def expand_abbreviations(case_name: str) -> str:
    """Expand common legal abbreviations at the end of party names."""
    tokens = case_name.split()
    # Only expand the last token if it's in the map
    if tokens and tokens[-1] in ABBREVIATION_MAP:
        tokens[-1] = ABBREVIATION_MAP[tokens[-1]]
    # Also expand the last token before a comma (e.g., 'Co.,')
    if len(tokens) > 1 and tokens[-2] in ABBREVIATION_MAP and tokens[-1].startswith(','):
        tokens[-2] = ABBREVIATION_MAP[tokens[-2]]
    return ' '.join(tokens)

def normalize_citation_format(citation_text: str) -> str:
    """Normalize citation format to handle Bluebook variations."""
    # Remove extra spaces in common citation formats
    normalized = citation_text
    
    # Handle L.Ed. variations
    normalized = re.sub(r'L\.\s*Ed\.\s*(\d+)\s*(\w+)', r'L.Ed.\1\2', normalized)
    normalized = re.sub(r'L\.\s*Ed\.\s*(\d+)', r'L.Ed.\1', normalized)
    
    # Handle S.Ct. variations
    normalized = re.sub(r'S\.\s*Ct\.\s*(\d+)', r'S.Ct.\1', normalized)
    
    # Handle U.S. variations
    normalized = re.sub(r'U\.\s*S\.\s*(\d+)', r'U.S.\1', normalized)
    
    return normalized

def extract_case_name_hinted(text, citation, canonical_name, window=300):
    """
    Extract case name with hints from canonical name.
    
    Args:
        text: Full text
        citation: Citation text
        canonical_name: Known canonical name
        window: Context window size
        
    Returns:
        str: Extracted case name
    """
    if not canonical_name:
        return ""
    
    # Look for the canonical name in the text around the citation
    citation_index = text.find(citation)
    if citation_index == -1:
        return ""
    
    # Safeguard against window being None
    if window is None:
        window = 300
        logging.warning("Window parameter was None, defaulting to 300")
    
    start = max(0, citation_index - window)
    end = min(len(text), citation_index + len(citation) + window)
    context = text[start:end]
    
    # Look for the canonical name in the context
    if canonical_name.lower() in context.lower():
        return canonical_name
    
    return ""

def extract_case_name_triple_from_text(text: str, citation_text: str, canonical_name: str, window: int = 500, debug: bool = False) -> dict:
    """
    Extract canonical_name (from external source), extracted_name (verbatim before citation),
    and hinted_name (best fuzzy match to canonical_name, but verbatim from doc) for a citation.
    Always return the best possible line/block as the hinted name, even if the fuzzy match is weak.
    If debug is True, print context, blocks, scores, and final choices.
    """
    citation_index = text.find(citation_text)
    if citation_index == -1:
        if debug:
            print(f"[DEBUG] Citation '{citation_text}' not found in text.")
        return {
            'canonical_name': canonical_name,
            'extracted_name': '',
            'hinted_name': citation_text  # Use citation as fallback
        }
    
    # Increase context window to 500 characters, but stop early if another citation (year in parenthesis) is found
    start = max(0, citation_index - 500)
    context_before_full = text[start:citation_index]
    
    # Stop at the last occurrence of a year in parenthesis before the citation
    year_match = list(re.finditer(r'\((17|18|19|20)\d{2}\)', context_before_full))
    if year_match:
        # Only keep text after the last year in parenthesis
        last_year_end = year_match[-1].end()
        context_before = context_before_full[last_year_end:].strip()
    else:
        context_before = context_before_full.strip()
    
    if debug:
        print(f"[DEBUG] Context before citation (up to 500 chars, stops at year):\n{context_before}\n---")
    
    # Extract the last non-empty line as extracted_name
    lines = [line.strip() for line in context_before.split('\n') if line.strip()]
    # Only consider lines up to 100 characters long for case names
    lines = [line[:100] for line in lines]
    extracted_name = lines[-1] if lines else ''
    
    if debug:
        print(f"[DEBUG] Lines considered for extraction (up to 100 chars): {lines}")
        print(f"[DEBUG] Extracted name: {extracted_name}")
    
    hinted_name = ''
    best_ratio = 0
    threshold = 0.3
    blocks = []
    
    for line in lines:
        blocks.extend([block.strip() for block in line.split('.') if block.strip()])
    blocks.extend(lines)
    
    if debug:
        print(f"[DEBUG] Blocks considered for fuzzy match: {blocks}")
    
    for block in blocks:
        if len(block) < 3:
            continue
        ratio = difflib.SequenceMatcher(None, canonical_name.lower(), block.lower()).ratio()
        if debug:
            print(f"[DEBUG] Block: '{block}' | Similarity: {ratio:.2f}")
        if ratio > best_ratio:
            best_ratio = ratio
            hinted_name = block
    
    if best_ratio < threshold and lines:
        if debug:
            print(f"[DEBUG] No block above threshold {threshold}, using last non-empty line.")
        hinted_name = lines[-1]
    
    if not hinted_name:
        if debug:
            print(f"[DEBUG] No hinted name found, using citation string as fallback.")
        hinted_name = citation_text
    
    if debug:
        print(f"[DEBUG] Final hinted name: {hinted_name}")
    
    return {
        'canonical_name': canonical_name,
        'extracted_name': extracted_name,
        'hinted_name': hinted_name
    }

def extract_year_from_line(line, citation_text=None):
    """
    Extract the year (YYYY) from a citation line. Prefer the year in the last parenthetical after the citation, but fallback to any 4-digit year in the line.
    If citation_text is provided, search after the citation first. Also checks parallel citation cache.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    logger.debug(f"[extract_year_from_line] Processing line: {line}")
    
    # Step 0: Check parallel citation cache first
    if citation_text:
        cached_date = get_parallel_citation_date(citation_text)
        if cached_date:
            logger.debug(f"[extract_year_from_line] Cached date found for citation: {citation_text}, returning: {cached_date}")
            return cached_date
    
    # Use the same regex as context window: (17|18|19|20)\d{2}
    if citation_text and citation_text in line:
        # Split the line at the citation and search after first
        after = line.split(citation_text, 1)[1]
        logger.debug(f"[extract_year_from_line] Text after citation: {after}")
        years = re.findall(r'\((17|18|19|20)\d{2}\)', after)
        if years:
            logger.debug(f"[extract_year_from_line] Year found after citation in parentheses: {years[-1]}")
            if citation_text:
                update_parallel_citation_cache(citation_text, "", years[-1])
            return years[-1]
        # Fallback: look for any 4-digit year after citation
        match = re.findall(r'(17|18|19|20)\d{2}', after)
        if match:
            logger.debug(f"[extract_year_from_line] Year found after citation: {match[-1]}")
            if citation_text:
                update_parallel_citation_cache(citation_text, "", match[-1])
            return match[-1]
        logger.debug(f"[extract_year_from_line] No year found after citation, searching whole line")
        # If not found after, search the whole line
    # Search the whole line as fallback
    years = re.findall(r'\((17|18|19|20)\d{2}\)', line)
    if years:
        logger.debug(f"[extract_year_from_line] Year found in whole line in parentheses: {years[-1]}")
        if citation_text:
            update_parallel_citation_cache(citation_text, "", years[-1])
        return years[-1]
    match = re.findall(r'(17|18|19|20)\d{2}', line)
    if match:
        logger.debug(f"[extract_year_from_line] Year found in whole line: {match[-1]}")
        if citation_text:
            update_parallel_citation_cache(citation_text, "", match[-1])
        return match[-1]
    logger.debug(f"[extract_year_from_line] No year found in line")
    return ""

def extract_case_name_unified(context_before: str, citation: str, html_content: str = "", source_url: str = "") -> str:
    """
    Unified case name extraction that combines multiple approaches for maximum accuracy.
    
    Args:
        context_before: Text before the citation
        citation: The citation being searched for
        html_content: HTML content if available (for web pages)
        source_url: Source URL if available (for site-specific extraction)
        
    Returns:
        str: The extracted case name or empty string if not found
    """
    import warnings
    warnings.warn('extract_case_name_unified is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    input_data = html_content if html_content else context_before
    input_type = 'html' if html_content else 'text'
    return extract_case_name_best(input_data, citation, input_type=input_type, source_url=source_url)

def extract_case_name_from_context_unified(context_before: str, citation: str) -> str:
    """
    Unified context-based case name extraction that tries multiple approaches.
    This is a simplified version that doesn't require HTML content.
    
    Args:
        context_before: Text before the citation
        citation: The citation being searched for
        
    Returns:
        str: The extracted case name or empty string if not found
    """
    import warnings
    warnings.warn('extract_case_name_from_context_unified is deprecated. Use extract_case_name_best instead.', DeprecationWarning)
    return extract_case_name_best(context_before, citation, input_type='text')

def extract_case_name_best(input_data: str, citation: str, input_type: str = 'text', source_url: str = "") -> str:
    """
    The best unified case name extraction function combining all effective strategies.
    Handles different input types (text, HTML content) and prioritizes extraction methods
    based on input characteristics to maximize success rate. Includes caching and external API fallback.
    Supports inheritance of case name for parallel citations.
    
    Args:
        input_data: The input data (text or HTML content) to extract from
        citation: The citation being searched for
        input_type: Type of input ('text' for plain text, 'html' for web content)
        source_url: Source URL if available (for site-specific extraction or URL-based fallback)
        
    Returns:
        str: The extracted case name or empty string if not found
    """
    if not input_data or not citation:
        log_debug(f"[extract_case_name_best] Empty input data or citation provided.")
        return ""

    # Step 0: Check cache first to avoid redundant processing
    cache_key = f"{citation}:{input_type}:{source_url[:50] if source_url else ''}"
    if cache_key in _case_name_cache:
        cached_case_name = _case_name_cache[cache_key]
        log_debug(f"[extract_case_name_best] Cache hit for citation: {citation}, returning: {cached_case_name}")
        return cached_case_name

    # Step 0.5: Check parallel citation cache using a normalized key
    normalized_key = normalize_citation_key(citation)
    if normalized_key in _parallel_citation_cache:
        cached_data = _parallel_citation_cache[normalized_key]
        case_name = cached_data.get('case_name', '')
        log_debug(f"[extract_case_name_best] Parallel citation cache hit for normalized key: {normalized_key}, returning case name: {case_name}")
        _case_name_cache[cache_key] = case_name
        if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
            _case_name_cache.pop(next(iter(_case_name_cache)))
        return case_name

    # Step 1: If input is HTML content, prioritize HTML-based extraction
    if input_type == 'html':
        case_name = extract_case_name_from_page(input_data, citation, source_url)
        if case_name:
            log_debug(f"[extract_case_name_best] Extracted case name from HTML: {case_name}")
            _case_name_cache[cache_key] = case_name
            update_parallel_citation_cache(citation, case_name)
            # Manage cache size
            if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                _case_name_cache.pop(next(iter(_case_name_cache)))
            return case_name
        else:
            log_debug(f"[extract_case_name_best] HTML extraction failed for citation: {citation}")

    # Step 2: For text input or if HTML extraction failed, use context-based extraction
    citation_index = input_data.find(citation)
    if citation_index != -1:
        context_before = input_data[max(0, citation_index - 1000):citation_index]
        # Try enhanced context-based extraction
        case_name = extract_case_name_from_context_context_based_enhanced(context_before, citation)
        if case_name:
            log_debug(f"[extract_case_name_best] Extracted case name from enhanced context: {case_name}")
            _case_name_cache[cache_key] = case_name
            update_parallel_citation_cache(citation, case_name)
            if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                _case_name_cache.pop(next(iter(_case_name_cache)))
            return case_name

        # Try standard context-based extraction
        case_name = extract_case_name_from_context_context_based(context_before, citation)
        if case_name:
            log_debug(f"[extract_case_name_best] Extracted case name from standard context: {case_name}")
            _case_name_cache[cache_key] = case_name
            update_parallel_citation_cache(citation, case_name)
            if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                _case_name_cache.pop(next(iter(_case_name_cache)))
            return case_name
        
        # If no case name found yet, try to extract from the full context around citation
        full_context = input_data[max(0, citation_index - 500):min(len(input_data), citation_index + len(citation) + 500)]
        lines = full_context.split('\n')
        for line in lines:
            if citation in line:
                case_name = extract_case_name_from_citation_line(line)
                if case_name:
                    log_debug(f"[extract_case_name_best] Extracted case name from full context line: {case_name}")
                    _case_name_cache[cache_key] = case_name
                    update_parallel_citation_cache(citation, case_name)
                    if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                        _case_name_cache.pop(next(iter(_case_name_cache)))
                    return case_name
    else:
        log_debug(f"[extract_case_name_best] Citation not found in input data for context extraction: {citation}")

    # Step 3: Search through lines for citation and extract case name
    lines = input_data.split('\n')
    for line in lines:
        if citation in line:
            case_name = extract_case_name_from_citation_line(line)
            if case_name:
                log_debug(f"[extract_case_name_best] Extracted case name from citation line: {case_name}")
                _case_name_cache[cache_key] = case_name
                update_parallel_citation_cache(citation, case_name)
                if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                    _case_name_cache.pop(next(iter(_case_name_cache)))
                return case_name
    log_debug(f"[extract_case_name_best] No case name found in citation lines for: {citation}")

    # Step 4: Fallback to URL content extraction if source_url is provided
    if source_url:
        case_name = extract_case_name_from_url_content(source_url, citation)
        if case_name:
            log_debug(f"[extract_case_name_best] Extracted case name from URL content: {case_name}")
            _case_name_cache[cache_key] = case_name
            update_parallel_citation_cache(citation, case_name)
            if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                _case_name_cache.pop(next(iter(_case_name_cache)))
            return case_name
        log_debug(f"[extract_case_name_best] URL content extraction failed for: {source_url}")

    # Step 5: Fallback to external API lookup with CourtListener if available
    try:
        courtlistener_result = get_canonical_case_name_from_courtlistener(citation)
        if courtlistener_result and courtlistener_result.get('case_name'):
            case_name = courtlistener_result['case_name']
            log_debug(f"[extract_case_name_best] Extracted case name from CourtListener API: {case_name}")
            _case_name_cache[cache_key] = case_name
            if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
                _case_name_cache.pop(next(iter(_case_name_cache)))
            return case_name
        else:
            log_debug(f"[extract_case_name_best] CourtListener API returned no case name for: {citation}")
    except Exception as e:
        log_debug(f"[extract_case_name_best] Error with CourtListener API for citation {citation}: {str(e)}")

    # Final fallback: No case name found
    log_debug(f"[extract_case_name_best] No case name extracted for citation: {citation} after all attempts")
    _case_name_cache[cache_key] = ""
    if len(_case_name_cache) > _CACHE_SIZE_LIMIT:
        _case_name_cache.pop(next(iter(_case_name_cache)))
    return ""

def normalize_citation_key(citation: str) -> str:
    """
    Normalize a citation to create a key for grouping parallel citations.
    This function extracts core components like reporter and page, or year, to group related citations.
    It also cleans up the citation text to handle variations in formatting.
    
    Args:
        citation: The citation text to normalize
        
    Returns:
        str: A normalized key for grouping parallel citations
    """
    # Clean up the citation text to remove extra spaces and normalize periods
    cleaned_citation = re.sub(r'\s+', ' ', citation).strip()
    cleaned_citation = re.sub(r'\.(\d)', r'. \1', cleaned_citation)  # Ensure space after period before numbers
    
    # Try to extract reporter and page as primary grouping factors
    match = re.search(r'([A-Za-z\.]+)\s+(\d+)', cleaned_citation)
    if match:
        reporter, page = match.groups()
        # Normalize reporter by removing trailing periods for consistency
        reporter = reporter.rstrip('.')
        # Further normalize ordinal indicators like 2d., 3d., 4th., etc.
        reporter = re.sub(r'(\d+[a-z]+)\.', r'\1', reporter, flags=re.IGNORECASE)
        # Also try to extract year for better grouping
        year_match = re.search(r'\((17|18|19|20)\d{2}\)', cleaned_citation)
        year = year_match.group(1) if year_match else ""
        return f"{reporter}_{page}_{year}".replace(' ', '_').lower()
    # Fallback to extract just the year if available
    year_match = re.search(r'\((17|18|19|20)\d{2}\)', cleaned_citation)
    if year_match:
        year = year_match.group(1)
        return f"year_{year}".lower()
    # Final fallback to a cleaned version of the citation
    cleaned = re.sub(r'[^A-Za-z0-9]', '_', cleaned_citation).lower()
    return cleaned[:50]  # Limit length to avoid overly long keys

def update_parallel_citation_cache(citation: str, case_name: str, date: str = ""):
    """
    Update the parallel citation cache with an extracted case name and date for a citation.
    This allows parallel citations to inherit the same case name and date.
    
    Args:
        citation: The citation text
        case_name: The extracted case name to cache
        date: The extracted date to cache (optional)
    """
    if case_name:
        normalized_key = normalize_citation_key(citation)
        _parallel_citation_cache[normalized_key] = {
            'case_name': case_name,
            'date': date
        }
        log_debug(f"[update_parallel_citation_cache] Updated cache for key: {normalized_key} with case name: {case_name} and date: {date}")
        if len(_parallel_citation_cache) > _CACHE_SIZE_LIMIT:
            _parallel_citation_cache.pop(next(iter(_parallel_citation_cache)))

def get_parallel_citation_date(citation: str) -> str:
    """
    Retrieve the cached date for a citation from the parallel citation cache.
    
    Args:
        citation: The citation text to look up
        
    Returns:
        str: The cached date if available, otherwise empty string
    """
    normalized_key = normalize_citation_key(citation)
    if normalized_key in _parallel_citation_cache:
        cached_data = _parallel_citation_cache[normalized_key]
        date = cached_data.get('date', '')
        log_debug(f"[get_parallel_citation_date] Cache hit for normalized key: {normalized_key}, returning date: {date}")
        return date
    return ""

# CourtListener API Integration Functions

def get_canonical_case_name_from_courtlistener(citation: str, api_key: str = None) -> Optional[dict]:
    """
    Get canonical case name and date from CourtListener API.
    
    Args:
        citation: The citation to look up
        api_key: CourtListener API key (optional, will try to get from config)
        
    Returns:
        dict: Dictionary with 'case_name' and 'date' keys, or None if not found
    """
    if not api_key:
        try:
            from src.config import get_config_value
            api_key = get_config_value("COURTLISTENER_API_KEY")
        except ImportError:
            return None
    
    if not api_key:
        return None
    
    try:
        # Try citation-lookup endpoint first (most precise)
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CaseStrainer Enhanced Extractor"
        }
        response = requests.post(url, json={"text": citation}, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Parse citation-lookup response (returns a list)
        if isinstance(data, list) and len(data) > 0:
            citation_data = data[0]
            if citation_data.get('clusters') and len(citation_data['clusters']) > 0:
                cluster = citation_data['clusters'][0]
                case_name = cluster.get('case_name', '')
                date = cluster.get('date_filed', '')
                if case_name:
                    case_name = normalize_case_name(case_name)
                    return {
                        'case_name': case_name,
                        'date': date
                    }
        
        # If citation-lookup fails, try search endpoint
        search_url = "https://www.courtlistener.com/api/rest/v4/search/"
        search_params = {
            "q": citation,
            "type": "o",  # opinions only
            "stat_Precedential": "on"
        }
        search_response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        if search_data.get('results'):
            for result in search_data['results']:
                case_name = result.get('case_name', '')
                date = result.get('date_filed', '')
                if case_name:
                    case_name = normalize_case_name(case_name)
                    return {
                        'case_name': case_name,
                        'date': date
                    }
                    
    except Exception as e:
        log_debug(f"Error getting canonical case name from CourtListener for '{citation}': {e}")
    
    return None

def get_citation_url(citation: str, api_key: str = None) -> Optional[str]:
    """
    Get direct URL to citation in legal databases.
    
    Args:
        citation: The citation to get URL for
        api_key: CourtListener API key (optional)
        
    Returns:
        str: URL to the citation, or None if not found
    """
    try:
        # Try CourtListener first (most reliable)
        if api_key:
            try:
                # Try citation-lookup endpoint first
                url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "CaseStrainer Enhanced Extractor"
                }
                response = requests.post(url, json={"text": citation}, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Parse citation-lookup response
                if isinstance(data, list) and len(data) > 0:
                    citation_data = data[0]
                    if citation_data.get('clusters') and len(citation_data['clusters']) > 0:
                        cluster = citation_data['clusters'][0]
                        if cluster.get('absolute_url'):
                            return f"https://www.courtlistener.com{cluster['absolute_url']}"
                
                # If citation-lookup fails, try search endpoint
                search_url = "https://www.courtlistener.com/api/rest/v4/search/"
                search_params = {
                    "q": citation,
                    "type": "o",  # opinions only
                    "stat_Precedential": "on"
                }
                search_response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                if search_data.get('results'):
                    for result in search_data['results']:
                        if result.get('absolute_url'):
                            return f"https://www.courtlistener.com{result['absolute_url']}"
                            
            except Exception as e:
                log_debug(f"Error getting CourtListener URL for '{citation}': {e}")
        
        # Fallback to other legal databases
        # Justia - has good search
        justia_url = f"https://law.justia.com/search?query={quote_plus(citation)}"
        
        # FindLaw - has search
        findlaw_url = f"https://caselaw.findlaw.com/search?query={quote_plus(citation)}"
        
        # Casetext - has search
        casetext_url = f"https://casetext.com/search?q={quote_plus(citation)}"
        
        # Return Justia as primary fallback (most reliable)
        return justia_url
        
    except Exception as e:
        log_debug(f"Error generating citation URL for '{citation}': {e}")
        return None

def get_legal_database_url(citation: str) -> Optional[str]:
    """
    Get a URL for a citation from legal databases like vLex, CaseMine, Leagle, etc.
    
    Args:
        citation: The citation text
        
    Returns:
        str: Legal database URL for the citation, or None if not found
    """
    try:
        # Try different legal databases based on citation type
        citation_lower = citation.lower()
        
        # vLex for international and some US cases
        if any(term in citation_lower for term in ['u.s.', 'f.', 's.ct.', 'l.ed.']):
            search_query = citation.replace(' ', '+')
            vlex_url = f"https://vlex.com/sites/search?q={search_query}"
            return vlex_url
        
        # CaseMine for Indian and some international cases
        elif any(term in citation_lower for term in ['indian', 'india', 'supreme court', 'high court']):
            search_query = citation.replace(' ', '+')
            casemine_url = f"https://www.casemine.com/search?q={search_query}"
            return casemine_url
        
        # Leagle for US cases
        elif any(term in citation_lower for term in ['u.s.', 'f.', 's.ct.', 'l.ed.', 'f.2d', 'f.3d']):
            # Check specifically for F.2d and F.3d patterns for Leagle
            if any(pattern in citation_lower for pattern in ['f.2d', 'f.3d']):
                search_query = citation.replace(' ', '+')
                leagle_url = f"https://www.leagle.com/search?q={search_query}"
                return leagle_url
            else:
                # For other US cases, use vLex
                search_query = citation.replace(' ', '+')
                vlex_url = f"https://vlex.com/sites/search?q={search_query}"
                return vlex_url
        
        # Default to vLex for other cases
        else:
            search_query = citation.replace(' ', '+')
            vlex_url = f"https://vlex.com/sites/search?q={search_query}"
            return vlex_url
        
    except Exception as e:
        log_debug(f"Error generating legal database URL for '{citation}': {e}")
        return None

def get_general_legal_search_url(citation: str) -> Optional[str]:
    """
    Get a general legal search URL for a citation using legal-specific search engines.
    
    Args:
        citation: The citation text
        
    Returns:
        str: General legal search URL for the citation, or None if not found
    """
    try:
        # Use Justia for general legal search
        search_query = citation.replace(' ', '+')
        justia_url = f"https://law.justia.com/search?query={search_query}"
        return justia_url
        
    except Exception as e:
        log_debug(f"Error generating general legal search URL for '{citation}': {e}")
        return None

def get_google_scholar_url(citation: str) -> Optional[str]:
    """
    Get Google Scholar URL for a citation.
    
    Args:
        citation: The citation text
        
    Returns:
        str: Google Scholar URL for the citation, or None if not found
    """
    try:
        search_query = citation.replace(' ', '+')
        scholar_url = f"https://scholar.google.com/scholar?q={search_query}"
        return scholar_url
        
    except Exception as e:
        log_debug(f"Error generating Google Scholar URL for '{citation}': {e}")
        return None

def generate_washington_citation_variants(citation: str) -> List[str]:
    """
    Generate Washington-specific citation variants with proper normalization.
    
    Args:
        citation: The citation to generate variants for
        
    Returns:
        List[str]: List of citation variants
    """
    variants = []
    
    # First, normalize Wn. to Wash. for better search results
    normalized_citation = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
    
    # Washington citation patterns with proper normalization
    washington_patterns = [
        # Standard Washington patterns (Wn. -> Wash.)
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn \2 \3'),
        
        # Washington App patterns (Wn. App. -> Wash. App.)
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. App. \2 \3'),
        
        # Washington 2d patterns (Wn. 2d -> Wash. 2d)
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wash. 2d \2 \3'),
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Washington 2d \2 \3'),
        
        # Handle cases where Wn. is already in the citation
        (r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
    ]
    
    # Apply patterns to both original and normalized citations
    for original, replacement in washington_patterns:
        # Apply to original citation
        variant = re.sub(original, replacement, citation, flags=re.IGNORECASE)
        if variant != citation:
            variants.append(variant)
        
        # Apply to normalized citation (Wn. -> Wash.)
        variant = re.sub(original, replacement, normalized_citation, flags=re.IGNORECASE)
        if variant != normalized_citation and variant not in variants:
            variants.append(variant)
    
    # Add the normalized citation itself
    if normalized_citation != citation:
        variants.append(normalized_citation)
    
    # Add specific Washington variants for better search
    if 'Wn.' in citation or 'Wn ' in citation:
        # Convert Wn. to Wash. for better API compatibility
        wash_variant = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
        if wash_variant not in variants:
            variants.append(wash_variant)
        
        # Also try Washington (full word)
        wash_full_variant = citation.replace('Wn.', 'Washington ').replace('Wn ', 'Washington ')
        if wash_full_variant not in variants:
            variants.append(wash_full_variant)
    
    return variants

def generate_parallel_citations(citation: str) -> List[str]:
    """
    Generate parallel citation attempts for common legal databases.
    
    Args:
        citation: The citation to generate parallel citations for
        
    Returns:
        List[str]: List of parallel citation variants
    """
    variants = []
    
    # Common parallel citation patterns
    # If it's a Washington citation, try federal equivalents
    if 'Wn.' in citation or 'Wash.' in citation:
        # Try to find federal parallel citations
        # This would require a lookup table or API call
        pass
    
    # If it's a federal citation, try state equivalents
    if 'F.' in citation or 'U.S.' in citation:
        # Try to find state parallel citations
        pass
    
    return variants

def extract_case_name_from_courtlistener_cluster(cluster_data: dict) -> str:
    """
    Extract case name from CourtListener cluster data.
    Uses 'case_name' as the canonical name if available, with 'case_name_short' and 'case_name_full' as fallbacks.
    
    Args:
        cluster_data: CourtListener cluster data dictionary
        
    Returns:
        str: Extracted case name or "Unknown Case"
    """
    try:
        # Use 'case_name' as the canonical name if available
        case_name = (
            cluster_data.get("case_name")
            or cluster_data.get("case_name_short")
            or cluster_data.get("case_name_full")
            or cluster_data.get("name")
            or cluster_data.get("title")
        )
        if case_name and case_name != "Unknown Case":
            return case_name
        
        # If still no case name, try to extract from absolute_url
        if cluster_data.get("absolute_url"):
            url_path = cluster_data["absolute_url"]
            if "/opinion/" in url_path:
                parts = url_path.split("/")
                if len(parts) >= 4:
                    case_slug = parts[-2]
                    case_name = case_slug.replace("-", " ").title()
                    return case_name
        
        return "Unknown Case"
    except Exception as e:
        log_debug(f"Error extracting case name from cluster: {e}")
        return "Unknown Case"

def extract_canonical_date_from_courtlistener_cluster(cluster_data: dict) -> str:
    """
    Extract canonical date from CourtListener cluster data.
    Uses 'date_filed' as the canonical date if available, with other date fields as fallbacks.
    Returns just the year (e.g., '1954' from '1954-05-17').
    
    Args:
        cluster_data: CourtListener cluster data dictionary
        
    Returns:
        str: Extracted year or None
    """
    try:
        # Use 'date_filed' as the canonical date if available
        canonical_date = cluster_data.get("date_filed")
        if canonical_date:
            # Extract year from ISO date string (e.g., '1954-05-17' -> '1954')
            if isinstance(canonical_date, str) and '-' in canonical_date:
                year = canonical_date.split('-')[0]
                if year.isdigit():
                    return year
        
        # Fallback to other date fields
        fallback_dates = [
            cluster_data.get("date_created"),
            cluster_data.get("date_modified"),
        ]
        
        # Check if there are other_dates available
        other_dates = cluster_data.get("other_dates", [])
        if isinstance(other_dates, list) and other_dates:
            fallback_dates.extend(other_dates)
        
        # Return the first available date's year
        for date in fallback_dates:
            if date and isinstance(date, str) and '-' in date:
                year = date.split('-')[0]
                if year.isdigit():
                    return year
        
        return None
        
    except Exception as e:
        log_debug(f"Error extracting canonical date from cluster: {e}")
        return None

def get_canonical_case_name_from_google_scholar(citation: str) -> Optional[str]:
    """
    Get canonical case name from Google Scholar using direct web scraping.
    
    Args:
        citation: The citation text to search for
        
    Returns:
        Canonical case name if found, None otherwise
    """
    try:
        # Add delay to prevent rate limiting
        time.sleep(2)  # 2 second delay between requests
        
        # Build Google Scholar search URL
        search_query = quote_plus(citation)
        scholar_url = f"https://scholar.google.com/scholar?q={search_query}&hl=en&as_sdt=0,5"
        
        log_debug(f"Searching Google Scholar for citation: {citation}")
        
        # Browser-like headers for web scraping
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Fetch the search results page with longer timeout
        response = requests.get(scholar_url, headers=headers, timeout=30)
        
        # Check for rate limiting
        if response.status_code == 429:
            log_debug(f"Google Scholar rate limited for citation: {citation}")
            return None
        
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for search result titles (Google Scholar result titles are in h3 tags)
        result_titles = soup.find_all('h3', class_='gs_rt')
        
        if result_titles:
            # Get the first result title
            first_title = result_titles[0].get_text(strip=True)
            
            # Also look for snippets which might contain case names
            result_snippets = soup.find_all('div', class_='gs_rs')
            first_snippet = result_snippets[0].get_text(strip=True) if result_snippets else ""
            
            # Extract case name from title and snippet
            case_name = extract_case_name_from_scholar_result(first_title, first_snippet)
            
            if case_name:
                log_debug(f"Found case name in Google Scholar: {case_name}")
                return case_name
        
        log_debug(f"No case name found in Google Scholar for: {citation}")
        return None
        
    except requests.exceptions.RequestException as e:
        log_debug(f"Network error searching Google Scholar for '{citation}': {e}")
        return None
    except Exception as e:
        log_debug(f"Error searching Google Scholar for '{citation}': {e}")
        return None

def extract_case_name_from_scholar_result(title: str, snippet: str) -> Optional[str]:
    """
    Extract case name from Google Scholar search result.
    
    Args:
        title: The title of the search result
        snippet: The snippet/description of the search result
        
    Returns:
        Extracted case name if found, None otherwise
    """
    # Combine title and snippet for analysis
    text = f"{title} {snippet}"
    
    # Look for common case name patterns
    patterns = [
        # Pattern: "Case Name v. Another Party"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        # Pattern: "Case Name v. Another Party,"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),',
        # Pattern: "Case Name v. Another Party."
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\.',
        # Pattern: "Case Name v. Another Party,"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+',
        # Pattern: "Case Name v. Another Party"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean up the match
            case_name = match.strip()
            if len(case_name) > 10 and 'v.' in case_name:  # Basic validation
                return case_name
    
    return None

def normalize_case_name(name: str) -> str:
    """Normalize the 'v.' in case names to lowercase with a period."""
    if not isinstance(name, str):
        return name
    # Replace ' V. ' or ' V ' with ' v. '
    name = name.replace(' V. ', ' v. ').replace(' V ', ' v. ')
    # Also handle edge cases: at the end of string
    name = name.replace(' V.', ' v.').replace(' V', ' v')
    return name

# Patch all places where canonical case names are returned from CourtListener or Google Scholar
# For example, in get_canonical_case_name_from_courtlistener and get_canonical_case_name_from_google_scholar

# In get_canonical_case_name_from_courtlistener, after fetching case_name:
# case_name = normalize_case_name(case_name)
# In get_canonical_case_name_from_google_scholar, after fetching case_name:
# case_name = normalize_case_name(case_name)

def find_shared_case_name_for_citations(text: str, citation_objs: list) -> dict:
    """
    Find shared case names for multiple citations in the same text.
    
    Args:
        text: The full text document
        citation_objs: List of citation objects with 'citation', 'start_index', 'end_index'
        
    Returns:
        dict: Mapping of citation strings to case names
    """
    if not text or not citation_objs:
        return {}
    
    result = {}
    
    try:
        # Sort citations by their position in the text
        sorted_citations = sorted(citation_objs, key=lambda x: x.get('start_index', 0))
        
        for citation_obj in sorted_citations:
            citation = citation_obj.get('citation', '')
            if not citation:
                continue
                
            # Extract case name from context around this citation
            start_idx = citation_obj.get('start_index', 0)
            end_idx = citation_obj.get('end_index', len(text))
            
            # Get context before the citation
            context_start = max(0, start_idx - 500)
            context_before = text[context_start:start_idx]
            
            # Try to extract case name from context
            case_name = extract_case_name_from_context_unified(context_before, citation)
            
            if case_name and is_valid_case_name(case_name):
                result[citation] = case_name
            else:
                # If no case name found, try the entire line containing the citation
                line_start = text.rfind('\n', 0, start_idx) + 1
                line_end = text.find('\n', end_idx)
                if line_end == -1:
                    line_end = len(text)
                
                line = text[line_start:line_end]
                case_name = extract_case_name_from_citation_line(line)
                
                if case_name and is_valid_case_name(case_name):
                    result[citation] = case_name
                else:
                    result[citation] = ""
        
        # If we found case names, try to share them across similar citations
        # (e.g., parallel citations for the same case)
        if result:
            # Group citations by their case names
            case_name_groups = {}
            for citation, case_name in result.items():
                if case_name:
                    if case_name not in case_name_groups:
                        case_name_groups[case_name] = []
                    case_name_groups[case_name].append(citation)
            
            # For citations without case names, try to assign from similar citations
            for citation, case_name in result.items():
                if not case_name:
                    # Look for similar citations that might be parallel citations
                    for known_case_name, known_citations in case_name_groups.items():
                        for known_citation in known_citations:
                            # Check if citations are likely parallel (same volume/reporter)
                            if _are_likely_parallel_citations(citation, known_citation):
                                result[citation] = known_case_name
                                break
                        if result[citation]:  # If we found a match, break out of outer loop
                            break
        
    except Exception as e:
        logger.warning(f"Error in find_shared_case_name_for_citations: {e}")
        # Return empty dict on error
        return {}
    
    return result

def _are_likely_parallel_citations(citation1: str, citation2: str) -> bool:
    """
    Check if two citations are likely parallel citations for the same case.
    
    Args:
        citation1: First citation
        citation2: Second citation
        
    Returns:
        bool: True if citations are likely parallel
    """
    if not citation1 or not citation2:
        return False
    
    # Extract volume and reporter from citations
    # Pattern: volume reporter page (e.g., "123 Wn. App. 456")
    pattern = r'(\d+)\s+([A-Z][a-z]+\.?\s*\d*)\s+(\d+)'
    
    match1 = re.search(pattern, citation1)
    match2 = re.search(pattern, citation2)
    
    if match1 and match2:
        volume1, reporter1, page1 = match1.groups()
        volume2, reporter2, page2 = match2.groups()
        
        # Check if volumes and pages are the same (likely same case)
        if volume1 == volume2 and page1 == page2:
            return True
        
        # Check if they're different reporters but same volume/page (parallel citations)
        if volume1 == volume2 and page1 == page2 and reporter1 != reporter2:
            return True
    
    return False

def extract_in_re_case_name_from_context(*args, **kwargs):
    return ""
