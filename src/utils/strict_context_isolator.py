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
import html
import logging
from typing import List, Tuple, Optional, Dict, Any
from src.citation_patterns import CitationPatterns  # CONSOLIDATED: Import shared patterns

logger = logging.getLogger(__name__)


def find_all_citation_positions(text: str) -> List[Tuple[int, int, str]]:
    """
    Find all citation positions in the text.
    
    IMPORTANT: Now uses shared citation patterns from citation_patterns.py
    
    Returns:
        List of (start_pos, end_pos, citation_text) tuples
    """
    citations = []
    
    # CONSOLIDATED: Use shared patterns instead of local definitions
    compiled_patterns = CitationPatterns.get_compiled_patterns()
    
    # Use subset of patterns relevant for boundary detection
    boundary_patterns = [
        compiled_patterns['us_supreme'],
        compiled_patterns['s_ct'],
        compiled_patterns['l_ed_2d'],
        compiled_patterns['f_2d'],
        compiled_patterns['f_3d'],
        compiled_patterns['f_4th'],
        compiled_patterns['f_supp_2d'],
        # Atlantic reporters (NJ, PA, etc.)
        compiled_patterns['a_general'],
        compiled_patterns['a_2d'],
        compiled_patterns['a_3d'],
        compiled_patterns['p_2d'],
        compiled_patterns['p_3d'],
        compiled_patterns['wn_2d'],
        compiled_patterns['wash_2d'],
        compiled_patterns['wn_app'],
        compiled_patterns['cal_2d'],
        compiled_patterns['cal_3d'],
        compiled_patterns['cal_4th'],
        # Neutral citations
        compiled_patterns['neutral_nm'],
        compiled_patterns['neutral_nd'],
        compiled_patterns['neutral_ok'],
        compiled_patterns['neutral_sd'],
        compiled_patterns['neutral_ut'],
        compiled_patterns['neutral_wi'],
        compiled_patterns['neutral_wy'],
        compiled_patterns['neutral_mt'],
    ]
    
    for pattern in boundary_patterns:
        for match in pattern.finditer(text):
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
    max_lookback: int = 100
) -> str:
    """
    Get strictly isolated context for a citation, stopping at previous citation boundaries.
    
    PROXIMITY FIX: Reduced max_lookback from 200 to 100 characters to extract case names
    closest to the citation, preventing extraction of wrong case names from distant context.
    
    Args:
        text: Full document text
        citation_start: Start position of this citation
        citation_end: End position of this citation
        all_citation_positions: Pre-computed citation positions (or will compute if None)
        max_lookback: Maximum characters to look back (default: 100, reduced from 200)
        
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
    
    # USER FIX 2024-10-16: Check for parenthetical boundaries
    # If citation is inside parentheses (like "(quoting Case v. Name, 123 U.S. 456)")
    # we should ONLY look inside that parenthetical, not backwards beyond it
    paren_boundary = previous_citation_end + 1
    
    # Look backwards from citation to find opening parenthesis
    search_start = max(previous_citation_end, citation_start - max_lookback)
    text_before = text[search_start:citation_start]
    
    # Find the last opening paren before this citation
    last_open_paren = text_before.rfind('(')
    if last_open_paren >= 0:
        # Found a paren - check if citation is inside it
        actual_pos = search_start + last_open_paren
        # Make sure there's no closing paren between the opening paren and our citation
        text_between = text[actual_pos:citation_start]
        if ')' not in text_between:
            # Citation is inside parenthetical - use opening paren as boundary
            paren_boundary = actual_pos + 1  # +1 to skip the '(' itself
            logger.error(f"[PAREN-DEBUG] Citation inside parenthetical! Boundary at pos {actual_pos}")
            logger.error(f"[PAREN-DEBUG] Text after paren: '{text[paren_boundary:citation_start][-50:]}'")
        else:
            logger.error(f"[PAREN-DEBUG] Found '(' but has ')' between - not in parenthetical")
    else:
        logger.error(f"[PAREN-DEBUG] No '(' found in text_before")
    
    # Determine strict context boundaries
    context_start = max(
        paren_boundary,  # Stop at parenthetical boundary or previous citation
        citation_start - max_lookback  # Don't go too far back
    )
    context_start = max(0, context_start)
    
    # Extract ONLY the text before this citation
    strict_context = text[context_start:citation_start].strip()

    # Additional boundary trimming to prefer the nearest case segment
    # If there's a semicolon-separated series, keep only the segment AFTER the last semicolon
    # within a reasonable proximity window to the citation (prevents pulling prior cases).
    if strict_context:
        # Always keep only the segment AFTER the last semicolon to avoid pulling
        # case names from earlier clauses in multi-citation sentences.
        last_sc = strict_context.rfind(';')
        if last_sc != -1:
            strict_context = strict_context[last_sc + 1:].strip()

        # Also trim after the last em-dash or long dash which often separates cites
        for dash in ('—', '–', '--'):
            last_dash = strict_context.rfind(dash)
            if last_dash != -1:
                strict_context = strict_context[last_dash + len(dash):].strip()
                break

        # Additional boundary tokens near the citation to prevent cross-clause bleed
        try:
            lc = strict_context.lower()
            tokens = ['see also', 'but see', 'compare', 'accord', 'cf.', 'see ']
            best_idx = -1
            best_len = 0
            for t in tokens:
                idx = lc.rfind(t)
                if idx != -1:
                    # Only consider if close to the citation (towards end of context)
                    if (len(strict_context) - idx) <= 150 and idx > best_idx:
                        best_idx = idx
                        best_len = len(t)
            if best_idx != -1 and best_len > 0:
                strict_context = strict_context[best_idx + best_len:].strip()
        except Exception:
            pass

        # Cap context length to the last 300 chars to bias towards the nearest match
        if len(strict_context) > 300:
            strict_context = strict_context[-300:]
    
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
        logger.error(f"[STRICT-EXTRACT-DEBUG] Context too short for {citation_text}: {len(context) if context else 0} chars")
        return None
    
    # DEBUG: Log the context being analyzed (ENABLED FOR DEBUGGING FIX #13)
    logger.error(f"[STRICT-EXTRACT-DEBUG] Citation: {citation_text}")
    logger.error(f"[STRICT-EXTRACT-DEBUG] Context ({len(context)} chars): '{context[-200:]}'")  # Last 200 chars
    
    # First unescape any HTML entities (e.g., &#039;, &amp;)
    try:
        context = html.unescape(context)
    except Exception:
        pass
    
    # CRITICAL: Normalize Unicode characters BEFORE pattern matching
    # Convert smart quotes and apostrophes to ASCII equivalents
    context = context.replace('\u2019', "'")  # Right single quotation mark → apostrophe
    context = context.replace('\u2018', "'")  # Left single quotation mark → apostrophe
    context = context.replace('\u201C', '"')  # Left double quotation mark
    context = context.replace('\u201D', '"')  # Right double quotation mark
    context = context.replace('\u00B4', "'")  # Acute accent → apostrophe
    context = context.replace('\u0060', "'")  # Grave accent → apostrophe
    context = context.replace('\u00A0', ' ')  # Non-breaking space → space
    # Normalize dashes and unusual spaces
    context = context.replace('\u2013', '-')   # En dash
    context = context.replace('\u2014', '-')   # Em dash
    context = re.sub(r'[\u2000-\u200B\u202F\u205F\u3000]', ' ', context)  # other thin/figure spaces
    # Collapse whitespace
    context = re.sub(r'\s+', ' ', context).strip()
    
    # CRITICAL: Remove signal words and case history notations BEFORE pattern matching
    
    # FIRST: Remove entire lines containing legal concepts that aren't case names
    # This handles "Anti-SLAPP Statute / Collateral Order Doctrine\n\nOverruling..."
    doctrine_lines_pattern = r'[^\n]*\b(doctrine|rule|test|standard|principle|holding)\b[^\n]*\n+'
    context = re.sub(doctrine_lines_pattern, '', context, flags=re.IGNORECASE)
    
    # THEN: Remove signal words and status indicators
    signal_patterns = [
        # Signal words - must be complete words with boundaries
        r'\b(cf|e\.g\.|i\.e\.|see also|see|compare|accord|but see|but cf|contra)\b\.?\s+',
        # USER FIX: Introductory/conditional words that contaminate case names
        # These appear at the start of sentences before case citations
        r'\b(if|when|where|while|although|though|unless|until|since|because|as)\b\s+(?:in\s+)?',
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
    
    # FIX #13: Remove case/docket numbers from context BEFORE pattern matching
    # This handles contamination like "Inc. No. 103430-0 15 v. Marston"
    # where page numbers and headers appear IN THE MIDDLE of case names
    context_before_clean = context
    context = re.sub(r'\s+No\.\s+[\d\-\s]+(?=\s+v\.)', ' ', context, flags=re.IGNORECASE)
    if context != context_before_clean:
        logger.error(f"[FIX #13] Cleaned case numbers from context")
        logger.error(f"[FIX #13] Before: '{context_before_clean[-100:]}'")
        logger.error(f"[FIX #13] After:  '{context[-100:]}'")
    else:
        logger.error(f"[FIX #13] No case numbers found to clean in context")
    
    # Look for paragraph/sentence boundaries but be less aggressive
    # Only split if we have very long context (>150 chars) to avoid losing too much
    if len(context) > 150:
        sentences = re.split(r'[.!]\s+(?=[A-Z])', context)
        if len(sentences) > 1:
            # Take the last 2 sentences to preserve more context
            context = ' '.join(sentences[-2:]).strip()
            logger.debug(f"[STRICT-EXTRACT] Reduced context to last 2 sentences")
    
    # Patterns to extract case names (IMPROVED - GREEDY patterns for full legal names)
    patterns = [
        # PRIORITY 1: Complex legal names with full party descriptions (NEW - HIGHEST PRIORITY)
        # Matches: "Chance Gresser, individually and as parent, natural guardian, next of friendand on behalf of his daughter, C.G., and Erin Gresser, individually and asparent, natural guardian, next of friend and on behalf of her daughter, C.G. v. Banner Health, d/b/a North Colorado Medical Center"
        # Matches: "Francis Rudnicki and Pamela Rudnicki, as parents, guardians and next friends of Alexander Rudnicki, a minor v. Bianco"
        r'([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:individually|as\s+(?:parent|guardian|next\s+friend|administrator|executor|trustee|personal\s+representative)|and\s+on\s+behalf\s+of|by\s+and\s+through)[^,]*)*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:d/b/a|doing\s+business\s+as|a\s+(?:Delaware|California|New\s+York)\s+(?:Corporation|Corp|Inc|LLC|Ltd))[^,]*)*)(?:\s*[;\(]|,\s*\d|$)',
        
        # PRIORITY 2: "In re" cases with full party names
        # Matches: "In re: The PEOPLE of the State of Colorado v. Regina M. SPRINKLE"
        r'In\s+re:\s+([A-Z][A-Z\s\'&\-\.,]+)\s+v\.\s+([A-Z][A-Z\s\'&\-\.,]+)(?:\s*[;\(]|,\s*\d|$)',
        
        # PRIORITY 3: Standard "v." pattern - BALANCED to capture reasonable names
        # Stop at semicolon or opening paren to prevent cross-citation contamination
        # Reduced from 200 to 100 characters to be more selective and avoid long lookback
        # Unicode characters are normalized to ASCII before this pattern is applied
        r'([A-Z][A-Za-z\'\.\&,\s\n\-]{2,100})\s+v\.\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,100})(?:\s*[;\(]|,\s*\d|$)',
        
        # PRIORITY 4: In re/Matter of/Estate of patterns
        r'(?:In\s+re|Matter\s+of|Estate\s+of)\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,200})(?:\s*[,;\(]|$)',
        
        # PRIORITY 5: Ex parte pattern  
        r'Ex\s+parte\s+([A-Z][A-Za-z\'\.\&,\s\n\-]{2,200})(?:\s*[,;\(]|$)',
    ]
    
    for pattern_idx, pattern in enumerate(patterns, 1):
        try:
            # Look for matches - find ALL matches
            matches = list(re.finditer(pattern, context, re.IGNORECASE))
            if not matches:
                continue
            
            # USER FIX 2024-10-26: Take the match CLOSEST to the end of context (closest to citation)
            # Calculate distance from end of context for each match
            context_length = len(context)
            best_match = None
            best_distance = float('inf')
            
            for match in matches:
                # Distance from end of context = how far from the citation
                match_end = match.end()
                distance_from_end = context_length - match_end
                
                if distance_from_end < best_distance:
                    best_distance = distance_from_end
                    best_match = match
            
            if best_match is None:
                continue
            
            match = best_match  # Use the closest match to citation
            # SAFETY GUARD: Only accept matches within close proximity to the citation
            # to avoid inheriting names from distant earlier clauses.
            if best_distance > 120:
                # Too far from citation; try next pattern
                continue

            # NEARBY FRAGMENT GUARD: If the last ~120 chars contain a recent comma
            # followed by a capitalized fragment WITHOUT 'v.', prefer that fragment
            # over an earlier 'v.' match (common in shortened references like
            # "Nat'l Ass'n of Mfrs., 105 F.4th 802").
            try:
                recent = context[-120:]
                comma_idx = recent.rfind(',')
                if comma_idx != -1:
                    fragment = recent[comma_idx+1:].strip()
                    # Only consider fragment if it clearly looks like a case name signal
                    has_v = ' v. ' in fragment.lower()
                    has_prefix = re.search(r'^(in\s+re|ex\s+parte|estate\s+of|matter\s+of)\b', fragment, re.IGNORECASE)
                    if (has_v or has_prefix):
                        fragment_abs_start = len(context) - len(recent) + comma_idx + 1
                        if match.end() < fragment_abs_start:
                            frag_clean = re.sub(r'\s+', ' ', fragment).strip(' ,;\n()"')
                            if len(frag_clean) >= 5 and re.search(r'[A-Za-z]{3,}', frag_clean):
                                logger.info(f"[STRICT-EXTRACT] Using nearby case-like fragment: '{frag_clean}' for {citation_text}")
                                return frag_clean
            except Exception:
                pass
            
            # REPORTER FAMILY GUARD: If the text between this match and the citation
            # clearly references a different reporter family than the target citation,
            # treat this match as belonging to that other citation and skip it.
            try:
                def _detect_family(s: str) -> str:
                    s2 = s.lower()
                    # Order matters: check more specific tokens first
                    for token, fam in (
                        ('f. 4th', 'f4th'), ('f.4th', 'f4th'),
                        ('f. 3d', 'f3d'), ('f.3d', 'f3d'),
                        ('f. 2d', 'f2d'), ('f.2d', 'f2d'),
                        ('u.s.', 'us'), ('s. ct.', 'sct'), ('l. ed. 2d', 'led2d'),
                        ('a. 3d', 'a3d'), ('a.3d', 'a3d'),
                        ('a. 2d', 'a2d'), ('a.2d', 'a2d'),
                        ('a.', 'a'),
                        ('p. 3d', 'p3d'), ('p.3d', 'p3d'),
                        ('p. 2d', 'p2d'), ('p.2d', 'p2d'),
                        ('p.', 'p'),
                    ):
                        if token in s2:
                            return fam
                    return ''
                target_fam = _detect_family(citation_text)
                between_seg = context[match.end():]
                between_fam = _detect_family(between_seg)
                if between_fam and target_fam and between_fam != target_fam:
                    logger.debug(f"[STRICT-EXTRACT] Reporter family mismatch between match and citation (between='{between_fam}', target='{target_fam}') - skipping match")
                    continue
            except Exception:
                pass

            if pattern_idx in [1, 2, 3]:  # Patterns with 2 groups (plaintiff v. defendant)
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
                
                # Heuristic: restore governmental prefixes if present in recent context
                try:
                    recent_ctx = context[-220:]
                    mgov = re.search(r"(County|City|Township|Borough)\s+of\s+([A-Z][A-Za-z\.'\-]+)", recent_ctx, flags=re.IGNORECASE)
                    if mgov:
                        loc = mgov.group(2)
                        if plaintiff.lower() == loc.lower() or loc.lower() in plaintiff.lower():
                            # Rebuild with normalized casing
                            gov_word = mgov.group(1).capitalize()
                            loc_word = loc[0].upper() + loc[1:]
                            plaintiff = f"{gov_word} of {loc_word}"
                except Exception:
                    pass
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
                'principles set forth', 'intervening decision', 'recused',
                'at common law', 'determining the amount', 'within the province'
            ]
            if any(phrase in case_name.lower() for phrase in reject_phrases):
                continue
            
            # Reject if starts with common sentence starters
            sentence_starters = [
                'at ', 'the ', 'this ', 'that ', 'these ', 'those ',
                'in ', 'for ', 'with ', 'without ', 'under ', 'over ',
                'determining ', 'establishing ', 'calculating '
            ]
            case_lower = case_name.lower()
            if any(case_lower.startswith(starter) for starter in sentence_starters):
                # Unless it's a valid case name pattern (has "v.")
                if ' v. ' not in case_lower:
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
                # USER FIX 2024-10-17: Allow common abbreviations like Cmty., Ass'n, Dep't
                if plaintiff_part.endswith(('.', ',')) or defendant_part.endswith(('.', ',')):
                    combined = plaintiff_part + defendant_part
                    if not re.search(r"(Inc|LLC|Corp|Co|Ltd|Cmty|Ass'n|Dep't|Dept|Bd|Dist|Comm|Div)", combined):
                        continue  # Suspicious punctuation unless it's corporate or known abbreviation
            
            # If we reach here and there is no 'v.' and not an accepted prefix (In re, Ex parte, Estate of, Matter of), reject to avoid narrative fragments
            if ' v. ' not in case_name.lower():
                if not re.search(r'^(In\s+re|Ex\s+parte|Estate\s+of|Matter\s+of)\b', case_name, re.IGNORECASE):
                    logger.debug(f"[STRICT-EXTRACT] Rejecting non-case-like fragment: '{case_name}'")
                    continue

            # === FINAL CLEANUP ===
            
            # USER FIX 2024-10-21: Remove signal words from extracted case name
            # These can survive pattern matching if they're part of the matched text
            case_name = re.sub(r'^(see also|see|compare|cf|e\.g\.|i\.e\.|accord|but see|but cf|contra)\s+', '', case_name, flags=re.IGNORECASE).strip()
            case_name = re.sub(r'^(if|when|where|while|although|though|unless|until|since|because|as)\s+(?:in\s+)?', '', case_name, flags=re.IGNORECASE).strip()
            
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
    # Fallback: capture '... v. ...,' immediately before the citation (common formatting)
    try:
        recent = context[-160:]
        m = re.search(r"([A-Z][^,;()]{2,120})\s+v\.\s+([^,;()]{2,120})\s*,\s*$", recent)
        if m:
            plaintiff = re.sub(r'\s+', ' ', m.group(1)).strip(' ,;\n')
            defendant = re.sub(r'\s+', ' ', m.group(2)).strip(' ,;\n')
            if len(plaintiff) >= 2 and len(defendant) >= 2:
                fallback_name = f"{plaintiff} v. {defendant}"
                logger.info(f"[STRICT-EXTRACT:FALLBACK] Extracted '{fallback_name}' for {citation_text}")
                return fallback_name
    except Exception:
        pass
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
