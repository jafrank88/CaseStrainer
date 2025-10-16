"""
Strict Context Isolator - Prevents case name bleeding between citations.

CRITICAL PROBLEM SOLVED:
When multiple citations appear close together like:
"P.R. Aqueduct v. Met, 506 U.S. 139 ... Will v. Hallock, 546 U.S. 345"

The extractor was picking up "Will v. Hallock" for "506 U.S. 139" instead of
"P.R. Aqueduct v. Met" because it wasn't properly isolating the context.

SOLUTION:
This module provides strict context boundaries by:
1. Finding ALL citations in the document
2. For each citation, isolating ONLY the text immediately before it
3. Stopping at the nearest previous citation boundary
4. Extracting case name ONLY from that isolated context
"""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


def find_all_citation_positions(text: str) -> List[Tuple[int, int, str]]:
    """
    Find all citation positions in the text.
    
    Returns:
        List of (start_pos, end_pos, citation_text) tuples
    """
    citations = []
    
    # Patterns for common citation formats
    patterns = [
        # Federal reporters: 123 U.S. 456, 123 S. Ct. 456, 123 F.3d 456
        r'\b\d+\s+(?:U\.S\.|S\.\s*Ct\.|F\.\s*2d|F\.\s*3d|F\.\s*4th|F\.\s*Supp\.?\s*2d|F\.\s*Supp\.?\s*3d|L\.\s*Ed\.?\s*2d)\s+\d+',
        # State reporters: 123 Wash.2d 456, 123 P.3d 456
        r'\b\d+\s+(?:Wash\.2d|Wn\.2d|Wn\.\s*App\.?\s*2d|P\.\s*2d|P\.\s*3d|P\.)\s+\d+',
        # Cal. reporters: 123 Cal.3d 456
        r'\b\d+\s+(?:Cal\.\s*2d|Cal\.\s*3d|Cal\.\s*4th|Cal\.\s*5th|Cal\.\s*App\.?\s*2d|Cal\.\s*App\.?\s*3d)\s+\d+',
        # Neutral/Public Domain Citations: 2017-NM-007, 2017 ND 123, etc.
        r'\b20\d{2}-(?:NM|NMCA)-\d{1,5}\b',  # New Mexico (hyphenated)
        r'\b20\d{2}\s+(?:ND|OK|SD|UT|WI|WY|MT)\s+\d{1,5}\b',  # Other states (space-separated)
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            citations.append((match.start(), match.end(), match.group(0)))
    
    # Sort by position
    citations.sort(key=lambda x: x[0])
    
    # Deduplicate overlapping citations
    deduped = []
    last_end = -1
    for start, end, cit_text in citations:
        if start >= last_end:
            deduped.append((start, end, cit_text))
            last_end = end
    
    logger.debug(f"[STRICT-CONTEXT] Found {len(deduped)} citation positions")
    return deduped


def get_strict_context_for_citation(
    text: str,
    citation_start: int,
    citation_end: int,
    all_citation_positions: Optional[List[Tuple[int, int, str]]] = None,
    max_lookback: int = 200
) -> str:
    """
    Get strictly isolated context for a citation, stopping at previous citation boundaries.
    
    Args:
        text: Full document text
        citation_start: Start position of this citation
        citation_end: End position of this citation
        all_citation_positions: Pre-computed citation positions (or will compute if None)
        max_lookback: Maximum characters to look back
        
    Returns:
        Strictly isolated context string
    """
    if all_citation_positions is None:
        all_citation_positions = find_all_citation_positions(text)
    
    # Find previous citation that ends before this one starts
    previous_citation_end = 0
    for cit_start, cit_end, cit_text in all_citation_positions:
        if cit_end < citation_start:
            previous_citation_end = max(previous_citation_end, cit_end)
        elif cit_start >= citation_start:
            break  # We've passed our citation
    
    # Determine strict context boundaries
    context_start = max(
        previous_citation_end + 1,  # Stop at previous citation
        citation_start - max_lookback  # Don't go too far back
    )
    context_start = max(0, context_start)
    
    # Extract ONLY the text before this citation
    strict_context = text[context_start:citation_start].strip()
    
    logger.debug(
        f"[STRICT-CONTEXT] Citation at {citation_start}-{citation_end}: "
        f"context from {context_start} to {citation_start} ({len(strict_context)} chars)"
    )
    
    return strict_context


def extract_case_name_from_strict_context(
    context: str,
    citation_text: str
) -> Optional[str]:
    """
    Extract case name from strictly isolated context.
    
    This function ONLY looks at the provided context and won't bleed to other citations.
    
    Args:
        context: Strictly isolated context (text immediately before citation)
        citation_text: The citation text (for logging)
        
    Returns:
        Extracted case name or None
    """
    if not context or len(context) < 10:
        return None
    
    # CRITICAL: Remove signal words and case history notations BEFORE pattern matching
    
    # FIRST: Remove entire lines containing legal concepts that aren't case names
    # This handles "Anti-SLAPP Statute / Collateral Order Doctrine\n\nOverruling..."
    doctrine_lines_pattern = r'[^\n]*\b(doctrine|rule|test|standard|principle|holding)\b[^\n]*\n+'
    context = re.sub(doctrine_lines_pattern, '', context, flags=re.IGNORECASE)
    
    # THEN: Remove signal words and status indicators
    signal_patterns = [
        # Signal words - must be complete words with boundaries
        r'\b(cf|e\.g\.|i\.e\.|see also|see|compare|accord|but see|but cf|contra)\b\.?\s+',
        # Case history notations (including standalone "overruling")
        r'\b(overruling|overruled by|superseding|superseded by|abrogated by|disapproved of on other grounds by|disapproved of by|modified by|limited by|questioned by|criticized by|distinguished by|affirmed by|affirming|reversed by|reversing|vacated by|remanded by|amended by)\b\s+',
        # Procedural phrases
        r'\b(quoting|citing|discussing|relying on|based on|following|applying|interpreting)\b\s+',
        # Parenthetical case history
        r'\([^)]{0,150}?(overruled|superseded|abrogated|disapproved|modified|affirmed|reversed)[^)]{0,150}?\)\s*',
    ]
    
    original_context = context
    for signal_pattern in signal_patterns:
        context = re.sub(signal_pattern, '', context, flags=re.IGNORECASE)
    
    if context != original_context:
        logger.debug(f"[STRICT-EXTRACT] Cleaned signal words: '{original_context[-50:]}' → '{context[-50:]}'")
    
    # Look for paragraph/sentence boundaries but be less aggressive
    # Only split if we have very long context (>150 chars) to avoid losing too much
    if len(context) > 150:
        sentences = re.split(r'[.!]\s+(?=[A-Z])', context)
        if len(sentences) > 1:
            # Take the last 2 sentences to preserve more context
            context = ' '.join(sentences[-2:]).strip()
            logger.debug(f"[STRICT-EXTRACT] Reduced context to last 2 sentences")
    
    # Patterns to extract case names (BALANCED - not too strict, not too loose)
    patterns = [
        # Standard "v." pattern - must have "v." but flexible ending
        # Match: "Erie Railroad Co. v. Tompkins" even if followed by comma/paren
        r'([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}?)\s+v\.\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,120}?)(?:\s*[,;\(]|$)',
        
        # In re/Matter of/Estate of patterns
        r'(?:In\s+re|Matter\s+of|Estate\s+of)\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,100}?)(?:\s*[,;\(]|$)',
        
        # Ex parte pattern  
        r'Ex\s+parte\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,100}?)(?:\s*[,;\(]|$)',
        
        # Fallback: Capitalized name before punctuation/end
        # Match multi-word capitalized phrases
        r'([A-Z][A-Za-z\'\.\&,\-]{3,}(?:\s+[A-Z][A-Za-z\'\.\&,\-]{2,})+)(?:\s*[,;\(]|$)',
    ]
    
    for pattern_idx, pattern in enumerate(patterns, 1):
        try:
            # Look for matches, preferring the LAST one (closest to citation)
            matches = list(re.finditer(pattern, context, re.IGNORECASE))
            if not matches:
                continue
            
            match = matches[-1]  # Take the last (closest) match
            
            if pattern_idx == 1:  # Standard "v." pattern (2 groups)
                plaintiff = match.group(1).strip()
                defendant = match.group(2).strip()
                
                # Clean up whitespace and newlines
                plaintiff = re.sub(r'\s+', ' ', plaintiff).strip(' ,;\n')
                defendant = re.sub(r'\s+', ' ', defendant).strip(' ,;\n')
                
                # Fix corporate name punctuation: "Spokeo , Inc." → "Spokeo, Inc."
                plaintiff = re.sub(r'\s+,\s+', ', ', plaintiff)
                defendant = re.sub(r'\s+,\s+', ', ', defendant)
                
                # Remove trailing incomplete words (truncation artifacts)
                plaintiff = re.sub(r'\s+[a-z]{1,2}$', '', plaintiff)  # "Name v. Ca" → "Name v."
                defendant = re.sub(r'\s+[a-z]{1,2}$', '', defendant)
                
                # Check for truncation at start (lowercase start indicates truncation)
                if plaintiff and plaintiff[0].islower():
                    logger.warning(f"[STRICT-EXTRACT] Detected truncated plaintiff: '{plaintiff}'")
                    continue  # Skip this match, try other patterns
                if defendant and defendant[0].islower():
                    logger.warning(f"[STRICT-EXTRACT] Detected truncated defendant: '{defendant}'")
                    continue
                
                case_name = f"{plaintiff} v. {defendant}"
                
            else:  # Single-group patterns (In re, Ex parte, fallback)
                case_name = match.group(1).strip(' ,;\n()\"')
                # Clean up whitespace
                case_name = re.sub(r'\s+', ' ', case_name)
            
            # === VALIDATION ===
            
            # Minimum length
            if len(case_name) < 5:
                continue
            
            # Must contain actual letters
            if not re.search(r'[A-Za-z]{3,}', case_name):
                continue
            
            # Reject if it's just a legal action word
            legal_action_words = [
                'vacated', 'affirmed', 'reversed', 'remanded', 'dismissed',
                'granted', 'denied', 'overruled', 'modified', 'stayed', 'amended'
            ]
            if case_name.lower().strip() in legal_action_words:
                continue
            
            # Reject common non-case-name phrases
            reject_phrases = [
                'we do not', 'this holding', 'the court', 'decision in',
                'holding that', 'pursuant to', 'under', 'based on',
                'principles set forth', 'intervening decision', 'recused'
            ]
            if any(phrase in case_name.lower() for phrase in reject_phrases):
                logger.debug(f"[STRICT-EXTRACT] Rejected phrase contamination: '{case_name}'")
                continue
            
            # For "v." patterns, validate both party names
            if ' v. ' in case_name.lower():
                parts = re.split(r'\s+v\.\s+', case_name, flags=re.IGNORECASE)
                if len(parts) != 2:
                    continue
                
                plaintiff_part = parts[0].strip()
                defendant_part = parts[1].strip()
                
                # Both parties must have meaningful length
                if len(plaintiff_part) < 2 or len(defendant_part) < 2:
                    continue
                
                # Check for incomplete/truncated parties
                if plaintiff_part.endswith(('.', ',')) or defendant_part.endswith(('.', ',')):
                    if not re.search(r'(Inc|LLC|Corp|Co|Ltd)', plaintiff_part + defendant_part):
                        continue  # Suspicious punctuation unless it's corporate
            
            # === FINAL CLEANUP ===
            
            # Remove all-caps contamination at start (document titles)
            all_caps_match = re.search(r'^([A-Z\s]+\s+[Vv]\.\s+[A-Z\s]+)\s+([A-Z][a-z])', case_name)
            if all_caps_match:
                case_name = case_name[all_caps_match.end(1):].strip()
            
            # Fix spacing around punctuation: "P .R." → "P.R."
            case_name = re.sub(r'([A-Z])\s+\.', r'\1.', case_name)
            
            # Normalize common abbreviations
            case_name = re.sub(r'\bR\.R\.\s+Co\.', 'Railroad Co.', case_name)
            case_name = re.sub(r'\bR\.\s*R\.\b', 'Railroad', case_name)
            
            # Clean up whitespace
            case_name = re.sub(r'\s+', ' ', case_name).strip()
            
            # Remove leading articles
            case_name = re.sub(r'^(the|a|an)\s+', '', case_name, flags=re.IGNORECASE).strip()
            
            if len(case_name) >= 5:
                logger.info(
                    f"[STRICT-EXTRACT] Extracted '{case_name}' for {citation_text} "
                    f"using pattern {pattern_idx}"
                )
                return case_name
                
        except Exception as e:
            logger.debug(f"[STRICT-EXTRACT] Pattern {pattern_idx} failed: {e}")
    
    logger.warning(f"[STRICT-EXTRACT] No case name found for {citation_text}")
    return None


def extract_with_strict_isolation(
    text: str,
    citations: List[Any],
    force_reextract: bool = False
) -> Dict[str, str]:
    """
    Extract case names for all citations with strict context isolation.
    
    This prevents case name bleeding between nearby citations.
    
    Args:
        text: Full document text
        citations: List of citation objects (must have citation, start_index, end_index attributes)
        force_reextract: If True, re-extract even if extracted_case_name exists
        
    Returns:
        Dictionary mapping citation text to extracted case name
    """
    # Pre-compute all citation positions for efficient boundary detection
    all_positions = find_all_citation_positions(text)
    
    results = {}
    
    for citation in citations:
        citation_text = getattr(citation, 'citation', None)
        start = getattr(citation, 'start_index', None)
        end = getattr(citation, 'end_index', None)
        
        if not citation_text or start is None or end is None:
            continue
        
        # Skip if already has good extraction
        existing_name = getattr(citation, 'extracted_case_name', None)
        if existing_name and len(existing_name) > 10 and not force_reextract:
            results[citation_text] = existing_name
            continue
        
        # Get strictly isolated context
        strict_context = get_strict_context_for_citation(
            text, start, end, all_positions, max_lookback=200
        )
        
        # Extract case name from isolated context
        case_name = extract_case_name_from_strict_context(strict_context, citation_text)
        
        if case_name:
            results[citation_text] = case_name
            # Update the citation object
            citation.extracted_case_name = case_name
            logger.info(f"[STRICT-ISOLATION] {citation_text} → '{case_name}'")
        else:
            logger.warning(f"[STRICT-ISOLATION] Failed to extract for {citation_text}")
    
    return results


__all__ = [
    'find_all_citation_positions',
    'get_strict_context_for_citation',
    'extract_case_name_from_strict_context',
    'extract_with_strict_isolation',
]
