"""
Utilities to clean contamination from extracted case names and dates.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_markdown_contamination(text: str) -> str:
    """
    Remove markdown and formatting characters that contaminate case names.
    
    Args:
        text: Text that may contain markdown contamination
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    # Remove markdown characters at the start
    cleaned = re.sub(r'^[>\#\*\-\+]+\s*', '', text)
    
    # Remove markdown bold/italic markers
    cleaned = re.sub(r'\*\*([^\*]+)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*([^\*]+)\*', r'\1', cleaned)
    cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)
    cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    if cleaned != text:
        logger.info(f"[MARKDOWN-CLEAN] Removed markdown: '{text}' -> '{cleaned}'")
    
    return cleaned


def fix_truncation_at_word_boundary(case_name: str, context: str = "") -> str:
    """
    Fix case names that are truncated mid-word.
    
    Args:
        case_name: Potentially truncated case name
        context: Surrounding context to find complete name
        
    Returns:
        Fixed case name
    """
    if not case_name:
        return case_name
    
    # Check if truncated (ends with incomplete word)
    if re.search(r'\b[A-Z][a-z]{1,2}\s*$', case_name):
        # Try to find complete name in context
        if context:
            # Look for the case name pattern in context
            escaped_name = re.escape(case_name[:20])  # Use first part as anchor
            pattern = escaped_name + r'[A-Za-z\s\.,\'&]{0,50}'
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                complete_name = match.group(0)
                # Find the end at a reasonable boundary
                if ' v. ' in complete_name:
                    # Extend to include full defendant name
                    parts = complete_name.split(' v. ')
                    if len(parts) == 2:
                        defendant = parts[1]
                        # Find end of defendant name
                        end_match = re.search(r'^[A-Za-z\s\.,\'&]+', defendant)
                        if end_match:
                            complete_name = f"{parts[0]} v. {end_match.group(0)}"
                
                if len(complete_name) > len(case_name):
                    logger.info(f"[TRUNCATION-FIX] Fixed truncation: '{case_name}' -> '{complete_name}'")
                    return complete_name.strip()
    
    return case_name


def remove_citation_references_from_name(case_name: str) -> str:
    """
    Remove citation references that were incorrectly included in case names.
    
    Args:
        case_name: Case name that may contain citation references
        
    Returns:
        Cleaned case name
    """
    if not case_name:
        return case_name
    
    original = case_name
    
    # Remove citation patterns at the end
    # Matches: ", 148 Wn.2d 224, 239" or ", 159 Wn.2d 700" etc.
    patterns = [
        r',\s*\d+\s+(?:Wn\.2d|Wash\.2d|Wn\.\s*App\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?$',
        r',\s*\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?$',
        r',\s*\d+\s+(?:P\.2d|P\.3d|P\.)\s+\d+(?:\s*,\s*\d+)?$',
        r',\s*\d+\s+(?:F\.2d|F\.3d|F\.\s*Supp\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?$',
        r',\s*\d+\s+[A-Z][A-Za-z\.]+\s+\d+(?:\s*,\s*\d+)?$',
    ]
    
    for pattern in patterns:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
    
    # Clean up trailing commas
    case_name = re.sub(r'\s*,\s*$', '', case_name).strip()
    
    if case_name != original:
        logger.info(f"[CITATION-REF-CLEAN] Removed citation: '{original}' -> '{case_name}'")
    
    return case_name


def clean_extracted_case_name(case_name: str, context: str = "") -> str:
    """
    Comprehensive cleaning of extracted case names.
    
    Args:
        case_name: Extracted case name
        context: Surrounding context for fixing truncation
        
    Returns:
        Cleaned case name
    """
    if not case_name or case_name in ('N/A', 'Unknown', 'Unknown Case'):
        return case_name
    
    # Step 1: Remove markdown contamination
    cleaned = clean_markdown_contamination(case_name)
    
    # Step 2: Remove citation references
    cleaned = remove_citation_references_from_name(cleaned)
    
    # Step 3: Fix truncation
    cleaned = fix_truncation_at_word_boundary(cleaned, context)
    
    # Step 4: Final cleanup
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Validate result
    if len(cleaned) < 3 or ' v. ' not in cleaned.lower():
        logger.warning(f"[EXTRACTION-CLEAN] Result may be invalid: '{cleaned}'")
    
    return cleaned


__all__ = [
    'clean_markdown_contamination',
    'fix_truncation_at_word_boundary',
    'remove_citation_references_from_name',
    'clean_extracted_case_name',
]
