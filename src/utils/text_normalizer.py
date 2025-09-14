"""
Text normalization utilities for handling Unicode character encoding issues.

This module provides functions to normalize text by converting problematic Unicode
characters to their standard ASCII equivalents, making regex patterns more reliable.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Unicode character mappings for common problematic characters
UNICODE_MAPPINGS = {
    # Apostrophes and quotes
    '\u2019': "'",  # Right single quotation mark
    '\u2018': "'",  # Left single quotation mark
    '\u201A': "'",  # Single low-9 quotation mark
    '\u201B': "'",  # Single high-reversed-9 quotation mark
    '\u2032': "'",  # Prime
    '\u2035': "'",  # Reversed prime
    '\u201C': '"',  # Left double quotation mark
    '\u201D': '"',  # Right double quotation mark
    '\u201E': '"',  # Double low-9 quotation mark
    '\u201F': '"',  # Double high-reversed-9 quotation mark
    '\u2033': '"',  # Double prime
    '\u2034': '"',  # Triple prime
    '\u2036': '"',  # Reversed double prime
    '\u2037': '"',  # Reversed triple prime
    '\u2039': '<',  # Single left-pointing angle quotation mark
    '\u203A': '>',  # Single right-pointing angle quotation mark
    '\u00B4': "'",  # Acute accent
    '\u0060': '`',  # Grave accent
    '\u02B9': "'",  # Modifier letter prime
    '\u02BB': "'",  # Modifier letter turned comma
    '\u02BC': "'",  # Modifier letter apostrophe
    '\u02BD': "'",  # Modifier letter reversed comma
    '\u02BE': "'",  # Modifier letter right half ring
    '\u02BF': "'",  # Modifier letter left half ring
    
    # Ampersands
    '\u0026': '&',  # Ampersand (standard)
    '\uFF06': '&',  # Fullwidth ampersand
    '\u204A': '&',  # Tironian sign et
    '\u214B': '&',  # Turned ampersand
    
    # Hyphens and dashes
    '\u002D': '-',  # Hyphen-minus (standard)
    '\u2010': '-',  # Hyphen
    '\u2011': '-',  # Non-breaking hyphen
    '\u2012': '-',  # Figure dash
    '\u2013': '-',  # En dash
    '\u2014': '-',  # Em dash
    '\u2015': '-',  # Horizontal bar
    '\u2212': '-',  # Minus sign
    '\uFE58': '-',  # Small em dash
    '\uFE63': '-',  # Small hyphen-minus
    '\uFF0D': '-',  # Fullwidth hyphen-minus
    
    # Periods and dots
    '\u002E': '.',  # Full stop (standard)
    '\u2024': '.',  # One dot leader
    '\u2025': '..', # Two dot leader
    '\u2026': '...',# Horizontal ellipsis
    '\u2027': '.',  # Hyphenation point
    
    # Other punctuation
    '\u055A': ':',  # Armenian apostrophe
    '\u055B': ':',  # Armenian emphasis mark
    '\u055C': ':',  # Armenian exclamation mark
    '\u055D': ':',  # Armenian comma
    '\u055E': ':',  # Armenian question mark
    '\u055F': ':',  # Armenian abbreviation mark
    '\u05F3': "'",  # Hebrew punctuation geresh
}

def normalize_text(text: str) -> str:
    """
    Normalize text by converting problematic Unicode characters to standard ASCII equivalents.
    
    This function handles common Unicode character encoding issues that can cause
    regex patterns to fail, such as smart quotes, em dashes, and other special characters.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text with Unicode characters converted to ASCII equivalents
    """
    if not text:
        return text
    
    normalized = text
    
    # Apply Unicode character mappings
    for unicode_char, ascii_char in UNICODE_MAPPINGS.items():
        normalized = normalized.replace(unicode_char, ascii_char)
    
    # Additional normalization: clean up multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Clean up multiple periods (but preserve ellipsis)
    normalized = re.sub(r'\.{4,}', '...', normalized)
    
    logger.debug(f"Text normalization: '{text[:50]}...' -> '{normalized[:50]}...'")
    
    return normalized.strip()

def normalize_case_name(case_name: str) -> str:
    """
    Normalize a case name specifically, handling common legal text issues.
    
    Args:
        case_name: Case name to normalize
        
    Returns:
        Normalized case name
    """
    if not case_name:
        return case_name
    
    # First apply general text normalization
    normalized = normalize_text(case_name)
    
    # Legal-specific normalizations
    # Handle common abbreviations
    normalized = re.sub(r'\bDept\b', 'Dep\'t', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bDepartment\b', 'Dep\'t', normalized, flags=re.IGNORECASE)
    
    # Clean up extra spaces around punctuation
    normalized = re.sub(r'\s*,\s*', ', ', normalized)
    normalized = re.sub(r'\s*\.\s*', '. ', normalized)
    
    logger.debug(f"Case name normalization: '{case_name}' -> '{normalized}'")
    
    return normalized.strip()

def clean_extracted_case_name(case_name: str) -> str:
    """
    Clean up extracted case names by removing leading text that doesn't belong.
    
    This function handles cases where regex patterns capture too much text,
    such as when "court. Lopez Demetrio v. Sakuma Bros. Farms" should be
    cleaned to "Lopez Demetrio v. Sakuma Bros. Farms".
    
    Args:
        case_name: Extracted case name to clean
        
    Returns:
        Cleaned case name
    """
    if not case_name:
        return case_name
    
    # Remove leading text that doesn't belong to case names
    # Common patterns that appear before case names
    leading_patterns = [
        r'^[^A-Z]*',  # Remove non-capital letters at start
        r'^(court|court\.|this\s+court|we\s+review|also\s+an?\s+issue|statutory\s+interpretation|questions?\s+of\s+law|de\s+novo|in\s+light\s+of|the\s+record\s+certified|federal\s+court)[\s\.]*',
        r'^(and|or|but|that|this|is|also|we|may|ask|resolution|of|that|question|necessary|to|resolve|case|before)[\s\.]*',
        r'^(see|citing|quoting|accord|id\.|ibid\.|brief\s+at|opening\s+br\.|reply\s+br\.)[\s\.]*',
        # More specific patterns for the current issue
        r'^[^A-Z]*an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*',
        r'^[^A-Z]*interpretation\s+is\s+also\s+an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*',
        r'^[^A-Z]*statutory\s+interpretation\s+is\s+also\s+an?\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo[\s\.]*',
    ]
    
    cleaned = case_name
    for pattern in leading_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove leading punctuation and whitespace
    cleaned = re.sub(r'^[\s\.,;:]+', '', cleaned)
    
    # Ensure the cleaned name starts with a capital letter
    if cleaned and not cleaned[0].isupper():
        # Find the first capital letter
        match = re.search(r'[A-Z]', cleaned)
        if match:
            cleaned = cleaned[match.start():]
        else:
            # If no capital letter found, return original
            cleaned = case_name
    
    logger.debug(f"Case name cleaning: '{case_name}' -> '{cleaned}'")
    
    return cleaned.strip()

def is_unicode_problematic(text: str) -> bool:
    """
    Check if text contains problematic Unicode characters that could cause regex issues.
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains problematic Unicode characters
    """
    if not text:
        return False
    
    # Check for any characters in our problematic Unicode ranges
    for unicode_char in UNICODE_MAPPINGS.keys():
        if unicode_char in text:
            return True
    
    return False
