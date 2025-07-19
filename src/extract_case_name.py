#!/usr/bin/env python3
"""
Case Name Extraction Module

This module provides various functions for extracting case names from text,
URLs, and other sources. It includes both literal extraction and canonical
name lookup capabilities.

DEPRECATED: Most functions in this module are deprecated. The main extraction
logic has been integrated into the unified pipeline (UnifiedCitationProcessor
with extract_case_name_triple from .case_name_extraction_core).

STILL USED: Some functions are still used by the unified pipeline:
- get_canonical_case_name_from_courtlistener
- get_canonical_case_name_from_google_scholar
- extract_case_name_hinted
- extract_case_name_from_text (and its helpers)

All other functions are deprecated and will be removed in a future version.
"""

import warnings
warnings.warn(
    "src.extract_case_name is deprecated. Most functionality has been integrated "
    "into UnifiedCitationProcessor with extract_case_name_triple from "
    "src.case_name_extraction_core. Only API lookup functions remain in use.",
    DeprecationWarning,
    stacklevel=2
)

import re
import requests
import time
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus, urlparse
import logging
from bs4 import BeautifulSoup
import json

# Set up debug logging
logging.basicConfig(filename='case_name_debug.log', level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Set up module logger
logger = logging.getLogger(__name__)

def log_debug(message):
    """Helper function to log debug messages to file"""
    logging.debug(message)
    logger.debug(f"[DEBUG] {message}")

# Stub function for deprecated wrappers
def extract_case_name_best(content: str, citation: str, input_type: str = 'text', source_url: str = None) -> str:
    """
    Real implementation using the canonical extract_case_name_unified function.
    This replaces the stub implementation with a working one.
    """
    try:
        # Use the canonical unified extraction function
        # Fix relative import issue
        try:
            return extract_case_name_unified(content, citation)
        except NameError:
            # If extract_case_name_unified is not available, use a fallback
            from src.case_name_extraction_core import extract_case_name_and_date_comprehensive
            case_name, _, _ = extract_case_name_and_date(text=content, citation=citation)
            return case_name or ""
    except Exception as e:
        logger.warning(f"extract_case_name_best failed: {e}")
        return ""

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
    Enhanced version with better handling of complex citations and case name-citation association.
    Uses narrow 100-character context window and focuses on adjacency between case name and date.
    Args:
        text: The full text
        citation_text: The specific citation to find case name for
        all_citations: List of all citations in the text (for context)
        canonical_name: Known canonical case name for the case
    Returns:
        str: Extracted case name or empty string
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    if not text or not citation_text:
        logger.debug("[extract_case_name_from_text] Empty text or citation_text.")
        return ""
    
    # Normalize all whitespace to spaces
    norm_text = re.sub(r'\s+', ' ', text)
    logger.debug(f"[extract_case_name_from_text] Normalized text: '{norm_text[:200]}...'")
    logger.debug(f"[extract_case_name_from_text] Looking for citation: '{citation_text}'")
    
    # Strategy 1: Look for case name in narrow context around citation (100 chars)
    citation_index = norm_text.find(citation_text)
    if citation_index != -1:
        # Use narrow context window (100 chars) as requested
        context_before = norm_text[max(0, citation_index - 100):citation_index]
        context_after = norm_text[citation_index:min(len(norm_text), citation_index + 100)]
        full_context = context_before + context_after
        logger.debug(f"[extract_case_name_from_text] Context before citation: '{context_before}'")
        logger.debug(f"[extract_case_name_from_text] Context after citation: '{context_after}'")
        logger.debug(f"[extract_case_name_from_text] Full context (200 chars): '{full_context}'")
        
        # Strategy 1a: Try hinted extraction first if we have a canonical name
        # BUT avoid circular calls - only call if we haven't been called from hinted extraction
        if canonical_name and not hasattr(extract_case_name_from_text, '_in_hinted_call'):
            try:
                # Set flag to prevent circular calls
                extract_case_name_from_text._in_hinted_call = True
                case_name = extract_case_name_hinted(text, citation_text, canonical_name)
                if case_name and is_valid_case_name(case_name):
                    logger.debug(f"[extract_case_name_from_text] Found case name with hinted extraction: '{case_name}'")
                    return case_name
            finally:
                # Always clean up the flag
                if hasattr(extract_case_name_from_text, '_in_hinted_call'):
                    delattr(extract_case_name_from_text, '_in_hinted_call')
        
        # Strategy 1b: Try precise extraction (most accurate)
        case_name = extract_case_name_precise(context_before, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name with precise extraction: '{case_name}'")
            return case_name
        
        # Strategy 1c: Look for case name patterns that are directly adjacent to the citation
        case_name = extract_case_name_with_date_adjacency(context_before, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name with date adjacency: '{case_name}'")
            return case_name
        
        # Strategy 1d: Look for case name patterns that are part of complex citations
        case_name = extract_case_name_from_complex_citation(full_context, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name in complex citation: '{case_name}'")
            return case_name
        
        # Strategy 1e: Fallback to enhanced context extraction with narrow window
        case_name = extract_case_name_from_context_enhanced(context_before, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name in context: '{case_name}'")
            return case_name
    else:
        logger.debug(f"[extract_case_name_from_text] Citation '{citation_text}' not found in text.")
    
    # Strategy 2: Look for case name in the entire text (global search) as last resort
    logger.debug(f"[extract_case_name_from_text] Trying global search...")
    case_name = extract_case_name_global_search(norm_text, citation_text)
    if case_name:
        logger.debug(f"[extract_case_name_from_text] Found case name in global search: '{case_name}'")
        return case_name
    
    # Strategy 3: Use canonical name ONLY as very last fallback and ONLY if we're confident
    # it actually appears in the document text
    if canonical_name and canonical_name.lower() in norm_text.lower():
        logger.debug(f"[extract_case_name_from_text] Using canonical name as fallback (found in text): '{canonical_name}'")
        return canonical_name
    
    logger.debug(f"[extract_case_name_from_text] No case name found")
    return ""

def extract_case_name_from_complex_citation(context: str, citation: str) -> str:
    """
    Extract case name from complex citation patterns like "State v. Waldon, 148 Wn. App. 952, 962-63, 202 P.3d 325 (2009)"
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    if not context or not citation:
        return ""
    
    # Patterns for complex citations with case names
    complex_citation_patterns = [
        # Pattern: Case Name, citation, citation (year)
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        # Pattern: Case Name, citation, page, citation, page (year)
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+.*?\(\d{4}\)',
        # Pattern: Case Name, citation (year)
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)',
        # Pattern: Case Name, citation with pinpoint
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+',
        # Pattern: In re cases
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        # Pattern: Estate cases
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        # Pattern: State/People cases
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    ]
    
    for i, pattern in enumerate(complex_citation_patterns):
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        logger.debug(f"[extract_case_name_from_complex_citation] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        
        if matches:
            # Take the last (most recent) match
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_from_complex_citation] Found case name in complex citation: '{case_name}'")
            
            if case_name and is_valid_case_name(case_name) and not starts_with_signal_word(case_name):
                # Verify this case name is associated with the citation we're looking for
                if is_case_name_associated_with_citation(context, case_name, citation):
                    logger.debug(f"[extract_case_name_from_complex_citation] Valid case name found: '{case_name}'")
                    return case_name
    
    logger.debug(f"[extract_case_name_from_complex_citation] No valid case names in complex citations found")
    return ""

def is_case_name_associated_with_citation(context: str, case_name: str, citation: str) -> bool:
    """
    Check if a case name is actually associated with the specific citation we're looking for.
    This prevents picking up case names from other citations in the same context.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    # Look for the case name followed by the citation in close proximity
    # Pattern: case_name, citation
    pattern = rf'{re.escape(case_name)}\s*,\s*{re.escape(citation)}'
    if re.search(pattern, context, re.IGNORECASE):
        logger.debug(f"[is_case_name_associated_with_citation] Case name '{case_name}' is directly associated with citation '{citation}'")
        return True
    
    # Look for case name followed by citation within 50 characters
    case_name_index = context.find(case_name)
    citation_index = context.find(citation)
    
    if case_name_index != -1 and citation_index != -1:
        # Case name should come before citation
        if case_name_index < citation_index:
            distance = citation_index - case_name_index
            if distance <= 50:  # Within 50 characters
                logger.debug(f"[is_case_name_associated_with_citation] Case name '{case_name}' is within {distance} chars of citation '{citation}'")
                return True
    
    logger.debug(f"[is_case_name_associated_with_citation] Case name '{case_name}' is NOT associated with citation '{citation}'")
    return False

def extract_case_name_with_date_adjacency(context_before: str, citation: str) -> str:
    """
    Extract case name with focus on adjacency between case name and date.
    Looks for patterns like "Case Name v. Defendant, 123 Reporter 456 (2023)"
    Uses narrow context and specific patterns to avoid header text.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    if not context_before:
        return ""
    
    # Use a narrower context window (50 chars) to focus on immediate adjacency
    narrow_context = context_before[-50:] if len(context_before) > 50 else context_before
    
    # Patterns that look for case names followed by dates or citations
    # More specific patterns that avoid header text
    date_adjacent_patterns = [
        # Case name followed by comma and citation (most specific)
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        # Case name followed by parentheses with year
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # In re cases with date adjacency
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # Estate cases with date adjacency
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # State/People cases with date adjacency
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    ]
    
    for i, pattern in enumerate(date_adjacent_patterns):
        matches = list(re.finditer(pattern, narrow_context, re.IGNORECASE))
        logger.debug(f"[extract_case_name_with_date_adjacency] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        
        if matches:
            # Take the last (most recent) match
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_with_date_adjacency] Found case name with date adjacency: '{case_name}'")
            
            # Enhanced validation to avoid header text
            if (case_name and 
                is_valid_case_name(case_name) and 
                not starts_with_signal_word(case_name) and
                not _is_header_or_clerical_text(case_name)):
                logger.debug(f"[extract_case_name_with_date_adjacency] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_with_date_adjacency] Case name invalid, starts with signal word, or is header text: '{case_name}'")
    
    logger.debug(f"[extract_case_name_with_date_adjacency] No valid case names with date adjacency found")
    return ""

def extract_case_name_global_search(text: str, citation: str) -> str:
    """
    Global search for case name patterns in the entire text.
    Used as a fallback when local context extraction fails.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    if not text or not citation:
        return ""
    
    patterns = [
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(Matter\s+of\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
    ]
    
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        logger.debug(f"[extract_case_name_global_search] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        for j, match in enumerate(matches):
            logger.debug(f"[extract_case_name_global_search] Match {j+1}: '{match.group(1)}'")
        
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_global_search] Cleaned case name: '{case_name}'")
            if case_name and is_valid_case_name(case_name) and not starts_with_signal_word(case_name):
                logger.debug(f"[extract_case_name_global_search] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_global_search] Case name invalid or starts with signal word: '{case_name}'")
    
    logger.debug(f"[extract_case_name_global_search] No valid case names found")
    return ""

def clean_case_name_enhanced(case_name: str) -> str:
    """
    Enhanced case name cleaning with better punctuation and signal word removal.
    """
    if not case_name:
        return ""
    
    # Remove common signal words and prefixes
    signal_words = [
        r'^See\s+generally\s+',
        r'^See\s+',
        r'^According\s+to\s+',
        r'^As\s+held\s+in\s+',
        r'^The\s+court\s+in\s+',
        r'^The\s+court\s+',
        r'^In\s+the\s+case\s+of\s+',
        r'^In\s+',
    ]
    
    for pattern in signal_words:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
    
    # Remove trailing punctuation and whitespace
    case_name = re.sub(r'[,\s]+$', '', case_name)
    case_name = case_name.rstrip('.,;:')
    
    # Remove leading/trailing whitespace
    case_name = case_name.strip()
    
    # Normalize whitespace
    case_name = re.sub(r'\s+', ' ', case_name)
    
    return case_name

def is_citation_like(text: str) -> bool:
    """
    Check if text looks like a citation rather than a case name.
    Enhanced version with better pattern matching.
    """
    if not text:
        return True
    
    # Normalize text
    text = text.strip()
    
    # Check for citation patterns
    citation_patterns = [
        r'^\d+\s+[A-Z]',  # Volume number + reporter
        r'^\d+\s*[A-Z]+\s+\d+',  # Volume + reporter + page
        r'^[A-Z]+\s+\d+',  # Reporter + page
        r'^\d+\s*[A-Z]+\s*\(\d+\)',  # Volume + reporter + (year)
        r'^[A-Z]+\s*\(\d+\)',  # Reporter + (year)
        r'^\d+\s*[A-Z]+\s*\d+\s*\(\d+\)',  # Full citation format
        r'^[A-Z]+\s*Rep\.',  # Reporter abbreviation
        r'^[A-Z]+\s*Supp\.',  # Supplement
        r'^[A-Z]+\s*2d',  # Second series
        r'^[A-Z]+\s*3d',  # Third series
        r'^F\.\s*\d+',  # Federal Reporter
        r'^U\.\s*S\.',  # United States Reports
        r'^S\.\s*Ct\.',  # Supreme Court Reporter
        r'^L\.\s*Ed\.',  # Lawyers Edition
        r'^L\.\s*Ed\.\s*2d',  # Lawyers Edition 2d
    ]
    
    for pattern in citation_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Check for very short text (likely not a case name)
    if len(text) < 5:
        return True
    
    # Check for all caps with numbers (likely citation)
    if re.match(r'^[A-Z0-9\s\.]+$', text) and any(c.isdigit() for c in text):
        return True
    
    return False

def is_valid_case_name(case_name: str) -> bool:
    """
    Validate if a case name is reasonable and complete.
    """
    if not case_name:
        return False
    
    # Normalize case name
    case_name = case_name.strip()
    
    # Must have minimum length
    if len(case_name) < 5:
        return False
    
    # Must not look like a citation
    if is_citation_like(case_name):
        return False
    
    # Must contain at least one letter
    if not re.search(r'[A-Za-z]', case_name):
        return False
    
    # Must start with a letter or common case name prefixes
    if not re.match(r'^[A-Za-z]|^In\s+re|^Estate\s+of|^Matter\s+of|^State\s+v\.|^People\s+v\.|^United\s+States\s+v\.', case_name, re.IGNORECASE):
        return False
    
    # Must contain a v. or vs. or be an In re/Estate/Matter case
    if not re.search(r'\s+v\.\s+|\s+vs\.\s+|^In\s+re|^Estate\s+of|^Matter\s+of', case_name, re.IGNORECASE):
        return False
    
    # Must not be too long (likely not a case name)
    if len(case_name) > 200:
        return False
    
    return True

def clean_case_name(case_name: str) -> str:
    """Clean and normalize a case name."""
    if not case_name:
        return ""

def expand_abbreviations(case_name: str) -> str:
    """
    Expand common abbreviations in case names.
    """
    if not case_name:
        return ""
    
    # Common legal abbreviations and their expansions
    abbreviations = {
        r'\bDep\b': 'Department',
        r'\bEmp\b': 'Employment',
        r'\bAss\'n\b': 'Association',
        r'\bCorp\b': 'Corporation',
        r'\bCo\b': 'Company',
        r'\bInc\b': 'Inc.',
        r'\bLtd\b': 'Limited',
        r'\bLLC\b': 'LLC',
        r'\bLLP\b': 'LLP',
        r'\bP\.C\.\b': 'P.C.',
        r'\bP\.A\.\b': 'P.A.',
    }
    
    expanded = case_name
    for pattern, replacement in abbreviations.items():
        expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)
    
    return expanded

def starts_with_signal_word(text: str) -> bool:
    """
    Check if text starts with a signal word that should be excluded.
    """
    if not text:
        return False
    
    signal_words = [
        'see generally',
        'see',
        'according to',
        'as held in',
        'the court in',
        'the court',
        'in the case of',
    ]
    
    text_lower = text.lower().strip()
    for signal_word in signal_words:
        if text_lower.startswith(signal_word):
            return True
    
    return False

def _is_header_or_clerical_text(text: str) -> bool:
    """
    Check if the text looks like header text, clerk names, or other non-case-name content.
    """
    if not text:
        return True
    
    # Convert to lowercase for easier checking
    text_lower = text.lower()
    
    # Check for common header/clerical words that shouldn't be in case names
    header_words = {
        'clerk', 'supreme', 'court', 'state', 'washington', 'filed', 'record', 
        'opinion', 'judge', 'justice', 'chief', 'associate', 'district', 'appeals',
        'circuit', 'federal', 'united', 'states', 'department', 'attorney', 
        'prosecuting', 'sheriff', 'county', 'municipal', 'organization', 'petitioners',
        'respondents', 'cross', 'individuals', 'similarly', 'situated', 'behalf',
        'others', 'married', 'couple', 'en', 'banc', 'file', 'office', 'june',
        'december', 'january', 'february', 'march', 'april', 'may', 'july', 'august',
        'september', 'october', 'november', 'am', 'pm', 'morning', 'afternoon',
        'pendleton', 'sarah', 'r.', 'r', 'supreme', 'court', 'clerk'
    }
    
    # Check if any header words appear in the text
    text_words = set(text_lower.split())
    if text_words.intersection(header_words):
        return True
    
    # Check for patterns that indicate header text
    header_patterns = [
        r'^[A-Z\s]+$',  # All caps text (like headers)
        r'clerk.*court',  # Contains "clerk" and "court"
        r'supreme.*court.*state',  # Contains "supreme court state"
        r'filed.*record',  # Contains "filed" and "record"
        r'opinion.*filed',  # Contains "opinion" and "filed"
        r'^[A-Z]+\s+[A-Z]+\s+[A-Z]+$',  # Three consecutive all-caps words
        r'pendleton.*supreme.*court.*clerk',  # Contains "pendleton supreme court clerk"
        r'^[A-Z]+\s+[A-Z]+\s+[A-Z]+\s+[A-Z]+',  # Four consecutive all-caps words
        r'clerk.*john.*doe',  # Contains "clerk" and "john doe"
        r'^[A-Z]+\s+[A-Z]+\s+[A-Z]+\s+[A-Z]+\s+[A-Z]+',  # Five consecutive all-caps words
    ]
    
    for pattern in header_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check if the text is too long (case names are typically not very long)
    if len(text) > 100:
        return True
    
    # Check if the text contains too many words (case names are typically 3-8 words)
    word_count = len(text.split())
    if word_count > 12:
        return True
    
    # Check for specific problematic patterns
    problematic_patterns = [
        r'R\.PENDLETON',  # The specific pattern causing the issue
        r'PENDLETON.*SUPREME.*COURT.*CLERK',
        r'CLERK.*JOHN.*DOE.*ET.*AL',
        r'SUPREME.*COURT.*CLERK.*JOHN.*DOE',
    ]
    
    for pattern in problematic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

# --- Re-exports and stubs for core extraction logic ---
import logging

def get_canonical_case_name_from_courtlistener(citation, api_key=None):
    """
    Get canonical case name using the unified citation processor.
    This replaces the stub implementation with a working one.
    """
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        processor = UnifiedCitationProcessor()
        
        # Use the existing verification workflow to get case name
        result = processor.verify_citation_unified_workflow(citation)
        
        if result and result.get('verified') == 'true':
            # Return the case name if available
            case_name = result.get('case_name', '')
            if case_name and case_name != 'N/A':
                return {
                    'case_name': case_name,
                    'date': result.get('canonical_date', ''),
                    'source': 'courtlistener_verification'
                }
        
        return None
        
    except Exception as e:
        logging.warning(f"Failed to get canonical name from CourtListener verification: {e}")
        return None

def get_canonical_case_name_from_google_scholar(citation, api_key=None):
    """
    Get canonical case name using the unified citation processor.
    This replaces the stub implementation with a working one.
    """
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        processor = UnifiedCitationProcessor()
        
        # Use the existing verification workflow to get case name
        result = processor.verify_citation_unified_workflow(citation)
        
        if result and result.get('verified') == 'true':
            # Return the case name if available
            case_name = result.get('case_name', '')
            if case_name and case_name != 'N/A':
                return {
                    'case_name': case_name,
                    'date': result.get('canonical_date', ''),
                    'source': 'google_scholar_verification'
                }
        
        return None
        
    except Exception as e:
        logging.warning(f"Failed to get canonical name from Google Scholar verification: {e}")
        return None

def extract_case_name_hinted(text: str, citation: str, canonical_name: str = None, api_key: str = None) -> str:
    """
    Safe version that NEVER returns canonical name directly.
    Only returns names actually found in the document text.
    """
    try:
        if not canonical_name:
            return ""
        
        # Find citation in text
        citation_index = text.find(citation.replace("Wash. 2d", "Wn.2d"))
        if citation_index == -1:
            citation_index = text.find(citation)
        if citation_index == -1:
            return ""
        
        # Get context before citation
        context_before = text[max(0, citation_index - 100):citation_index]
        
        # ONLY extract from document text - NEVER return canonical directly
        variants = []
        
        # Pattern 1: Extract case names from document text
        patterns = [
            r'([A-Z][A-Za-z\'\.\s,&]+\s+v\.\s+[A-Z][A-Za-z\'\.\s,&]+)',
            r'([A-Z][A-Za-z\'\.\s,&]+\s+vs\.\s+[A-Z][A-Za-z\'\.\s,&]+)',
            r'(Dep\'t\s+of\s+[A-Za-z\s,&]+\s+v\.\s+[A-Za-z\s,&]+)',
            r'(State\s+v\.\s+[A-Za-z\s,&]+)',
            r'(In\s+re\s+[A-Za-z\s,&]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, context_before)
            for match in matches:
                cleaned = clean_case_name_enhanced(match)
                if cleaned and is_valid_case_name(cleaned):
                    variants.append(cleaned)
        
        if not variants:
            # No variants found in document text
            return ""
        
        # Find best match using fuzzy matching
        from difflib import SequenceMatcher
        best_variant = ""
        best_score = 0.0
        
        for variant in variants:
            score = SequenceMatcher(None, variant.lower(), canonical_name.lower()).ratio()
            if score > best_score and score > 0.6:  # Minimum similarity threshold
                best_variant = variant
                best_score = score
        
        # CRITICAL: Verify the best variant is actually different from canonical
        # This prevents returning canonical names with minor formatting differences
        if best_variant and best_variant != canonical_name:
            # Double-check the variant actually appears in the source text
            if best_variant.replace("'", "").replace(".", "") in context_before.replace("'", "").replace(".", ""):
                return best_variant
        
        # If we get here, we couldn't find a valid extraction from the document
        return ""
        
    except Exception as e:
        import logging
        logging.warning(f"Safe hinted extraction failed: {e}")
        return ""

def extract_case_name_unified(text: str, citation: str, canonical_name: str = None, api_key: str = None) -> str:
    """
    Unified function to extract case name using multiple methods.
    This is the main entry point for case name extraction.
    
    Args:
        text: The full text content
        citation: The citation text to search for
        canonical_name: Optional canonical case name from API
        api_key: Optional API key for external services
        
    Returns:
        The best extracted case name
    """
    try:
        # First try hinted extraction if we have a canonical name
        if canonical_name:
            hinted_name = extract_case_name_hinted(text, citation, canonical_name, api_key)
            if hinted_name and is_valid_case_name(hinted_name):
                return hinted_name
        
        # Try direct extraction from text
        extracted_name = extract_case_name_from_text(text, citation)
        if extracted_name and is_valid_case_name(extracted_name):
            return extracted_name
        
        # Try global search as fallback
        global_name = extract_case_name_global_search(text, citation)
        if global_name and is_valid_case_name(global_name):
            return global_name
        
        return ""
        
    except Exception as e:
        logger.error(f"Error in extract_case_name_unified: {e}")
        return ""

def extract_case_name_from_context_unified(context: str, citation: str, canonical_name: str = None) -> str:
    """
    Unified function to extract case name from context using multiple methods.
    
    Args:
        context: The context text around the citation
        citation: The citation text
        canonical_name: Optional canonical case name
        
    Returns:
        The best extracted case name from context
    """
    try:
        # Try enhanced context-based extraction
        enhanced_name = extract_case_name_from_context_enhanced(context, citation)
        if enhanced_name and is_valid_case_name(enhanced_name):
            return enhanced_name
        
        # Try hinted extraction if we have canonical name
        if canonical_name:
            hinted_name = extract_case_name_hinted(context, citation, canonical_name)
            if hinted_name and is_valid_case_name(hinted_name):
                return hinted_name
        
        # Try basic context extraction
        basic_name = extract_case_name_from_context(context, citation)
        if basic_name and is_valid_case_name(basic_name):
            return basic_name
        
        return ""
        
    except Exception as e:
        logger.error(f"Error in extract_case_name_from_context_unified: {e}")
        return ""

def extract_case_name_triple_from_text(text: str, citation: str, api_key: str = None, context_window: int = 100) -> dict:
    """
    Extract canonical and extracted case names and dates using the core logic.
    This is a wrapper for extract_case_name_triple in src.case_name_extraction_core.
    Uses narrow 100-character context window by default.
    """
    try:
        from src.case_name_extraction_core import extract_case_name_and_date
        return extract_case_name_and_date(text=text, citation=citation)
    except Exception as e:
        logger.error(f"Error in extract_case_name_triple_from_text: {e}")
        return {'canonical_name': 'N/A', 'extracted_name': 'N/A', 'canonical_date': 'N/A', 'extracted_date': 'N/A'}

def extract_case_name_from_context_enhanced(context_before: str, citation: str) -> str:
    """
    Enhanced context-based case name extraction with better line break handling and signal word filtering.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    if not context_before:
        return ""
    
    # Already normalized by caller
    
    # More specific patterns that avoid picking up header text, clerk names, etc.
    patterns = [
        # Look for case names that are directly followed by the citation or a comma and citation
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        # Look for case names followed by parentheses with year (common citation format)
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # In re cases
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # Estate cases
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        # State/People cases
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    ]
    
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
        logger.debug(f"[extract_case_name_from_context_enhanced] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        for j, match in enumerate(matches):
            logger.debug(f"[extract_case_name_from_context_enhanced] Match {j+1}: '{match.group(1)}'")
        
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_from_context_enhanced] Cleaned case name: '{case_name}'")
            
            # Enhanced validation to avoid picking up header text, clerk names, etc.
            if (case_name and 
                is_valid_case_name(case_name) and 
                not starts_with_signal_word(case_name) and
                not _is_header_or_clerical_text(case_name)):
                logger.debug(f"[extract_case_name_from_context_enhanced] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_from_context_enhanced] Case name invalid, starts with signal word, or is header text: '{case_name}'")
    
    logger.debug(f"[extract_case_name_from_context_enhanced] No valid case names found")
    return ""

def extract_case_name_precise_boundaries(context: str) -> Optional[str]:
    """Extract case name with precise boundaries."""
    
    # Look for case name patterns in the last 150 characters
    search_text = context[-150:] if len(context) > 150 else context
    
    # Patterns for different case types (most specific first)
    patterns = [
        # Standard case: Name v. Name, (end with comma or citation)
        r'\b([A-Z][A-Za-z\s,\.&\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.&\'-]+?),\s*$',
        
        # Department cases
        r'\b(Dep\'t\s+of\s+[A-Za-z\s]+\s+v\.\s+[A-Za-z\s,\.&\'-]+?),\s*$',
        r'\b(Department\s+of\s+[A-Za-z\s]+\s+v\.\s+[A-Za-z\s,\.&\'-]+?),\s*$',
        
        # In re cases
        r'\b(In\s+re\s+[A-Za-z\s,\.&\'-]+?),\s*$',
        
        # State cases
        r'\b(State\s+v\.\s+[A-Za-z\s,\.&\'-]+?),\s*$',
        
        # More flexible patterns that don't require ending with comma
        r'\b([A-Z][A-Za-z\s,\.&\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        r'\b(State\s+v\.\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        r'\b(In\s+re\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        r'\b(Department\s+of\s+[A-Za-z\s]+\s+v\.\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            # Additional validation - be more flexible
            if 5 <= len(case_name) <= 100:
                # Check if it contains 'v.' or 'vs.' or is an 'In re' case
                if (' v. ' in case_name or ' vs. ' in case_name or 
                    case_name.lower().startswith('in re') or
                    case_name.lower().startswith('state v.')):
                    return case_name
    
    return None

def extract_case_name_precise(context_before: str, citation: str) -> str:
    """
    Extract case name with precise patterns to avoid capturing too much text.
    Handles 'v.', 'vs.', 'In re', 'Estate of', and 'State v.' cases.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    if not context_before:
        return ""
    
    # Use a wider context (80 chars) to ensure we capture the case name
    context = context_before[-80:] if len(context_before) > 80 else context_before
    
    # Patterns for various case name forms
    patterns = [
        # Standard: Name v. Name, citation
        r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5}\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*' + re.escape(citation),
        # Standard: Name v. Name (year)
        r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5}\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*\(\d{4}\)',
        # In re cases
        r'(In\s+re\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*\(\d{4}\)',
        # Estate cases
        r'(Estate\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*' + re.escape(citation),
        r'(Estate\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*\(\d{4}\)',
        # State/People cases
        r'(State\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*' + re.escape(citation),
        r'(People\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*' + re.escape(citation),
        r'(United\s+States\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*' + re.escape(citation),
        # More flexible: any case name followed by comma and citation
        r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5}\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*\d+',
    ]
    
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        logger.debug(f"[extract_case_name_precise] Pattern {i+1}: found {len(matches)} matches")
        
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_precise] Found case name: '{case_name}'")
            if (case_name and 
                is_valid_case_name(case_name) and 
                not starts_with_signal_word(case_name) and
                not _is_header_or_clerical_text(case_name) and
                len(case_name.split()) <= 10):
                logger.debug(f"[extract_case_name_precise] Valid case name found: '{case_name}'")
                return case_name
    logger.debug(f"[extract_case_name_precise] No valid case names found")
    return ""

def generate_hinted_names(context_before: str) -> list:
    """
    Generate 1, 2, and 3-word sequences before 'v.' or 'vs.' for hinted name comparison.
    Returns a list of possible hinted names.
    """
    import re
    tokens = context_before.strip().split()
    hinted_names = []
    for i in range(len(tokens)):
        if tokens[i].lower() in {"v.", "vs."} and i >= 1:
            for n in [1, 2, 3]:
                if i - n >= 0:
                    name = " ".join(tokens[i-n:i+2])
                    hinted_names.append(name)
    return hinted_names

def best_hinted_name(context_before: str, canonical_name: str) -> str:
    """
    Compare 1, 2, 3-word hinted names before 'v.' to the canonical name and pick the best match.
    """
    from difflib import SequenceMatcher
    hinted_names = generate_hinted_names(context_before)
    best = ""
    best_score = 0.0
    for name in hinted_names:
        # Clean the name to remove trailing punctuation
        cleaned_name = clean_case_name_enhanced(name)
        if cleaned_name and is_valid_case_name(cleaned_name):
            score = SequenceMatcher(None, cleaned_name.lower(), canonical_name.lower()).ratio()
            if score > best_score:
                best = cleaned_name
                best_score = score
    return best

def normalize_citation_for_extraction(citation: str) -> str:
    """
    Normalize citation to match what appears in the document text.
    """
    # Convert "Wash. 2d" back to "Wn.2d" to match document format
    normalized = citation.replace("Wash. 2d", "Wn.2d")
    normalized = normalized.replace("Washington 2d", "Wn.2d")
    
    # Add common format variations
    return normalized

def find_citation_in_text_flexible(text: str, citation: str) -> int:
    """
    Find citation in text using multiple format variations.
    """
    # Try original citation first
    pos = text.find(citation)
    if pos != -1:
        return pos
    
    # Try normalized version
    normalized = normalize_citation_for_extraction(citation)
    pos = text.find(normalized)
    if pos != -1:
        return pos
    
    # Try with different spacing
    spaced_citation = re.sub(r'(\d+)\s+([A-Z])', r'\1 \2', citation)
    pos = text.find(spaced_citation)
    if pos != -1:
        return pos
    
    # Try removing commas and extra page numbers
    simplified = re.sub(r',\s*\d+', '', citation)
    pos = text.find(simplified)
    if pos != -1:
        return pos
    
    return -1

def extract_year_enhanced_fixed(text: str, citation: str) -> str:
    """
    Enhanced year extraction with flexible citation matching.
    """
    # First, check if the citation already contains a year
    year_in_citation = re.search(r'\b(\d{4})\b', citation)
    if year_in_citation:
        return year_in_citation.group(1)
    
    # Try to find the citation in text using flexible matching
    citation_pos = find_citation_in_text_flexible(text, citation)
    if citation_pos != -1:
        after_citation = text[citation_pos + len(citation):]
        # Look for year in parentheses immediately after citation
        year_match = re.search(r'\s*\((\d{4})\)', after_citation)
        if year_match:
            return year_match.group(1)
        
        # Look for year within next 50 characters
        year_match = re.search(r'\b(\d{4})\b', after_citation[:50])
        if year_match:
            return year_match.group(1)
    
    # Try broader search for citation pattern + year
    # Look for the volume and reporter, then find year
    citation_parts = citation.split()
    if len(citation_parts) >= 3:
        volume = citation_parts[0]
        reporter = citation_parts[1]
        
        # Create flexible pattern - handle both "Wn.2d" and "Wash. 2d"
        reporter_pattern = reporter.replace("Wash.", "(?:Wash\\.|Wn\\.)").replace("Wn.", "(?:Wash\\.|Wn\\.)")
        
        pattern = rf'\b{re.escape(volume)}\s+{reporter_pattern}.*?(\d{{4}})'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return ""

def extract_case_name_triple_with_debugging(text: str, citation: str, api_key: str = None, context_window: int = 100) -> dict:
    """
    Enhanced extraction with comprehensive debugging and fallback logging.
    """
    result = {
        'case_name': "N/A",
        'extracted_date': "N/A", 
        'case_name_confidence': 0.0,
        'case_name_method': "failed",
        'debug_info': {
            'extraction_attempts': [],
            'fallback_used': False,
            'fallback_reason': None
        }
    }
    
    try:
        logger.info(f"=== EXTRACTION DEBUG START ===")
        logger.info(f"Citation: '{citation}'")
        logger.info(f"Text length: {len(text)}")
        logger.info(f"Context window: {context_window}")
        
        # PRIORITY 1: Try enhanced extraction first
        logger.info("=== TRYING ENHANCED EXTRACTION ===")
        try:
            from src.case_name_extraction_core import extract_case_name_improved
            case_name, extracted_date, confidence = extract_case_name_improved(text, citation)
            
            if case_name and case_name != "N/A":
                result['case_name'] = case_name
                result['case_name_confidence'] = confidence
                result['case_name_method'] = "enhanced_extraction"
                logger.info(f"SUCCESS: Enhanced extraction found: '{case_name}' (confidence: {confidence})")
                
                result['debug_info']['extraction_attempts'].append({
                    'method': 'enhanced_extraction',
                    'name_result': case_name,
                    'date_result': extracted_date,
                    'confidence': confidence,
                    'success': True
                })
            else:
                logger.info("Enhanced extraction failed - no case name found")
                result['debug_info']['extraction_attempts'].append({
                    'method': 'enhanced_extraction',
                    'name_result': case_name,
                    'date_result': extracted_date,
                    'confidence': confidence,
                    'success': False
                })
                
        except Exception as e:
            logger.warning(f"Enhanced extraction failed: {e}")
            result['debug_info']['extraction_attempts'].append({
                'method': 'enhanced_extraction',
                'name_result': None,
                'date_result': None,
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            })
        
        # PRIORITY 2: Try comprehensive extraction if enhanced failed
        if result['case_name'] == "N/A":
            logger.info("=== TRYING COMPREHENSIVE EXTRACTION ===")
            try:
                from src.case_name_extraction_core import extract_case_name_and_date_comprehensive
                case_name, extracted_date, canonical_name = extract_case_name_and_date(text=text, citation=citation)
                
                if case_name and case_name != "N/A":
                    result['case_name'] = case_name
                    result['case_name_confidence'] = 0.6  # Lower confidence for comprehensive
                    result['case_name_method'] = "comprehensive_extraction"
                    logger.info(f"SUCCESS: Comprehensive extraction found: '{case_name}'")
                    
                    result['debug_info']['extraction_attempts'].append({
                        'method': 'comprehensive_extraction',
                        'name_result': case_name,
                        'date_result': extracted_date,
                        'confidence': 0.6,
                        'success': True
                    })
                else:
                    logger.info("Comprehensive extraction failed - no case name found")
                    result['debug_info']['extraction_attempts'].append({
                        'method': 'comprehensive_extraction',
                        'name_result': case_name,
                        'date_result': extracted_date,
                        'confidence': 0.0,
                        'success': False
                    })
                    
            except Exception as e:
                logger.warning(f"Comprehensive extraction failed: {e}")
                result['debug_info']['extraction_attempts'].append({
                    'method': 'comprehensive_extraction',
                    'name_result': None,
                    'date_result': None,
                    'confidence': 0.0,
                    'success': False,
                    'error': str(e)
                })
        
        # PRIORITY 3: Try hinted extraction if we have no extracted name
        if result['case_name'] == "N/A":
            logger.info("=== TRYING HINTED EXTRACTION ===")
            try:
                # Use a generic hint instead of canonical name to avoid contamination
                hinted_name = extract_case_name_hinted(text, citation, None, api_key)
                if hinted_name:
                    result['hinted_name'] = hinted_name
                    result['case_name'] = hinted_name
                    result['case_name_confidence'] = 0.7
                    result['case_name_method'] = "hinted_from_document"
                    logger.info(f"SUCCESS: Hinted extraction found: '{hinted_name}'")
                    
                    result['debug_info']['extraction_attempts'].append({
                        'method': 'hinted_extraction',
                        'name_result': hinted_name,
                        'date_result': None,
                        'confidence': 0.7,
                        'success': True
                    })
                else:
                    logger.info("Hinted extraction failed - no case name found")
                    result['debug_info']['extraction_attempts'].append({
                        'method': 'hinted_extraction',
                        'name_result': None,
                        'date_result': None,
                        'confidence': 0.0,
                        'success': False
                    })
                        
            except Exception as e:
                logger.warning(f"Hinted extraction failed: {e}")
                result['debug_info']['extraction_attempts'].append({
                    'method': 'hinted_extraction',
                    'name_result': None,
                    'date_result': None,
                    'confidence': 0.0,
                    'success': False,
                    'error': str(e)
                })
        
        # PRIORITY 4: Try fallback extraction strategies
        if result['case_name'] == "N/A":
            logger.info("=== TRYING FALLBACK EXTRACTION ===")
            try:
                from src.enhanced_extraction_utils import fallback_extraction_pipeline
                
                # Find citation position in text
                citation_pos = text.find(citation)
                if citation_pos != -1:
                    fallback_result = fallback_extraction_pipeline(text, citation_pos, citation_pos + len(citation))
                    
                    if fallback_result.get('case_name'):
                        result['case_name'] = fallback_result['case_name']
                        result['case_name_confidence'] = 0.4  # Low confidence for fallback
                        result['case_name_method'] = f"fallback_{fallback_result.get('fallback_strategy_used', 'unknown')}"
                        result['debug_info']['fallback_used'] = True
                        result['debug_info']['fallback_reason'] = "All primary extraction methods failed"
                        
                        logger.info(f"SUCCESS: Fallback extraction found: '{fallback_result['case_name']}' (strategy: {fallback_result.get('fallback_strategy_used')})")
                        
                        # Log fallback usage
                        log_fallback_usage(
                            citation=citation,
                            fallback_type='extraction',
                            reason="All primary extraction methods failed",
                            context={
                                'fallback_strategy': fallback_result.get('fallback_strategy_used'),
                                'fallback_level': fallback_result.get('fallback_level'),
                                'failed_methods': [attempt['method'] for attempt in result['debug_info']['extraction_attempts'] if not attempt['success']]
                            }
                        )
                        
                        result['debug_info']['extraction_attempts'].append({
                            'method': result['case_name_method'],
                            'name_result': fallback_result['case_name'],
                            'date_result': fallback_result.get('date'),
                            'confidence': 0.4,
                            'success': True,
                            'fallback_strategy': fallback_result.get('fallback_strategy_used')
                        })
                    else:
                        logger.info("Fallback extraction failed - no case name found")
                        result['debug_info']['extraction_attempts'].append({
                            'method': 'fallback_extraction',
                            'name_result': None,
                            'date_result': None,
                            'confidence': 0.0,
                            'success': False
                        })
                else:
                    logger.info("Citation not found in text for fallback extraction")
                    result['debug_info']['extraction_attempts'].append({
                        'method': 'fallback_extraction',
                        'name_result': None,
                        'date_result': None,
                        'confidence': 0.0,
                        'success': False,
                        'error': 'Citation not found in text'
                    })
                    
            except Exception as e:
                logger.warning(f"Fallback extraction failed: {e}")
                result['debug_info']['extraction_attempts'].append({
                    'method': 'fallback_extraction',
                    'name_result': None,
                    'date_result': None,
                    'confidence': 0.0,
                    'success': False,
                    'error': str(e)
                })
        
        # Extract date if not already found
        if result['extracted_date'] == "N/A":
            try:
                from src.case_name_extraction_core import extract_date_improved
                fixed_date = extract_date_improved(text, citation)
                if fixed_date:
                    result['extracted_date'] = fixed_date
                    logger.info(f"SUCCESS: Enhanced extraction found date: '{fixed_date}'")
            except Exception as e:
                logger.warning(f"Date extraction failed: {e}")
        
        logger.info(f"=== FINAL RESULTS ===")
        logger.info(f"Case name: '{result['case_name']}'")
        logger.info(f"Extracted date: '{result['extracted_date']}'")
        logger.info(f"Method: '{result['case_name_method']}'")
        logger.info(f"Fallback used: {result['debug_info']['fallback_used']}")
        logger.info(f"=== EXTRACTION DEBUG END ===")
            
    except Exception as e:
        logger.error(f"Error in extract_case_name_triple_with_debugging: {e}")
        result['debug_info']['extraction_attempts'].append({
            'method': 'error',
            'name_result': None,
            'date_result': None,
            'confidence': 0.0,
            'success': False,
            'error': str(e)
        })
    
    return result

from src.case_name_extraction_core import extract_case_name_fixed_comprehensive as extract_case_name_fixed
from src.canonical_case_name_service import log_fallback_usage
