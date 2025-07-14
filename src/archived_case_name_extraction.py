#!/usr/bin/env python3
"""
Archived Case Name Extraction Module

DEPRECATED: This module is archived and deprecated. All functionality has been
integrated into the unified pipeline (UnifiedCitationProcessor with 
extract_case_name_triple from .case_name_extraction_core).

This module will be removed in a future version.
"""

import warnings
warnings.warn(
    "src.archived_case_name_extraction is deprecated and archived. All functionality "
    "has been integrated into UnifiedCitationProcessor with extract_case_name_triple "
    "from .case_name_extraction_core. Use the unified pipeline instead.",
    DeprecationWarning,
    stacklevel=2
)

import re
import string
from .extract_case_name import clean_case_name, is_citation_like

# Global variable for recent case names
_recent_case_names = []

# --- Deprecated Wrappers ---
def extract_case_name_from_context_split(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_from_text in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_from_context_split is deprecated. Use extract_case_name_from_text in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_from_context(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_from_text in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_from_context is deprecated. Use extract_case_name_from_text in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_from_context_context_based(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_from_text in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_from_context_context_based is deprecated. Use extract_case_name_from_text in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_from_context_context_based_enhanced(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_from_text in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_from_context_context_based_enhanced is deprecated. Use extract_case_name_from_text in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_from_citation_line(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_from_text in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_from_citation_line is deprecated. Use extract_case_name_from_text in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_from_text(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_from_text in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_from_text is deprecated. Use extract_case_name_from_text in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_hinted(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_hinted in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_hinted is deprecated. Use extract_case_name_hinted in src/case_name_extraction_core.py', DeprecationWarning)
    return ''

def extract_case_name_triple_from_text(*args, **kwargs):
    """DEPRECATED: Use extract_case_name_triple in src/case_name_extraction_core.py"""
    import warnings
    warnings.warn('extract_case_name_triple_from_text is deprecated. Use extract_case_name_triple in src/case_name_extraction_core.py', DeprecationWarning)
    return {'canonical_name': '', 'extracted_name': '', 'hinted_name': ''}

# --- Context/Line-based Extraction (full versions) ---
# (Copy the full implementations from src/extract_case_name.py for reference)

def extract_in_re_case_name_from_context(context_before: str, citation_text: str = "") -> str:
    """
    Specifically look for "in re" case names within 15 words before a citation.
    This handles cases where "in re" appears close to the citation without other citations in between.
    """
    if not context_before:
        return ""
    context_before = re.sub(r'\s+', ' ', context_before)
    context = context_before[-300:]
    in_re_pattern = r'(?:^|\s)(in\s+re\s+[A-Z][A-Za-z\'\-\s]+(?:[A-Za-z\'\-\s]+)*)'
    matches = list(re.finditer(in_re_pattern, context, re.IGNORECASE | re.DOTALL))
    if matches:
        case_name = matches[-1].group(1).strip()
        # Clean up the case name
        # (Assume clean_case_name and is_citation_like are imported)
        case_name = clean_case_name(case_name)
        if case_name:
            return case_name
    flexible_pattern = r'(?:^|\s)(in\s+re\s+[A-Z][A-Za-z\'\-\s]+(?:[A-Za-z\'\-\s]+)*)'
    matches = list(re.finditer(flexible_pattern, context, re.IGNORECASE | re.DOTALL))
    if matches:
        potential_case_name = matches[-1].group(1).strip()
        match_end = matches[-1].end()
        text_after_match = context[match_end:]
        citation_patterns = [
            r'\d+\s+[A-Z]\.\s*\d+',
            r'\d+\s+[A-Z]{2,}\.\s*\d+',
            r'\d+\s+U\.\s*S\.\s*\d+',
            r'\d+\s+S\.\s*Ct\.\s*\d+',
            r'\d+\s+L\.\s*Ed\.\s*\d+\s*\w+',
            r'\d+\s+L\.\s*Ed\.\s*\d+',
        ]
        has_intervening_citation = False
        for pattern in citation_patterns:
            if re.search(pattern, text_after_match):
                has_intervening_citation = True
                break
        if not has_intervening_citation:
            case_name = clean_case_name(potential_case_name)
            if case_name and not is_citation_like(case_name):
                return case_name
    return ""

def extract_case_name_from_context(context_before: str, citation: str = "") -> str:
    """
    Attempt to extract a probable case name from the text before a citation.
    Looks for patterns like 'Smith v. Jones', 'In re Estate of ...', etc.
    Returns the case name if found, otherwise returns ''.
    """
    global _recent_case_names
    if not context_before:
        return ""
    context_lower = context_before.lower().strip()
    if context_lower.startswith('id.') or context_lower == 'id':
        if _recent_case_names:
            return _recent_case_names[-1]
        return ""
    context_before = re.sub(r'\s+', ' ', context_before)
    context = context_before[-500:]
    tokens = context.split()
    v_indices = [i for i, t in enumerate(tokens) if t.lower() in {'v.', 'vs.', 'versus'}]
    if v_indices:
        idx = v_indices[-1]
        before = tokens[max(0, idx-7):idx]
        after = tokens[idx+1:idx+8]
        context_words = {'the', 'in', 'as', 'at', 'by', 'for', 'on', 'with', 'to', 'from', 'of', 'decision', 'court', 'case', 'held'}
        while before and before[0].lower().strip(string.punctuation) in context_words:
            before = before[1:]
        after_clean = []
        abbrev_set = {
            'U.S.', 'D.C.', 'N.Y.', 'Cal.', 'Fla.', 'Ill.', 'Tex.', 'Ala.', 'Ariz.', 'Ark.', 'Colo.', 'Conn.', 'Del.', 'Ga.', 
            'Idaho', 'Ind.', 'Iowa', 'Kan.', 'Ky.', 'La.', 'Md.', 'Mass.', 'Mich.', 'Minn.', 'Miss.', 'Mo.', 'Mont.', 'Neb.', 
            'Nev.', 'N.H.', 'N.J.', 'N.M.', 'N.C.', 'N.D.', 'Ohio', 'Okla.', 'Ore.', 'Pa.', 'R.I.', 'S.C.', 'S.D.', 'Tenn.', 
            'Vt.', 'Va.', 'Wash.', 'W.Va.', 'Wis.', 'Wyo.', 'Puget', 'Sound', 'Reg', 'Techsystems', 'Transportation', 'Ecology', 
            'Campbell', 'Gwinn', 'Holdings', 'Industries', 'Security', 'Retirement', 'Systems', 'Forfeiture', 'Chevrolet', 
            'Chevelle', 'Medical', 'Center', 'Building', 'Industry', 'Ass\'n', 'Robinson', 'Silva-Baltazar', 'Pierce', 'County',
            'Wilson', 'Court', 'Ltd.', 'Partnership', 'Tony', 'Maroni\'s', 'Wenatchee', 'Valley', 'Utter', 'Association'
        }
        for word in after:
            w = word.strip(',;:')
            if not w:
                continue
            after_clean.append(w)
            if w[-1] == '.' and w not in abbrev_set and len(w) > 2:
                break
            if w[-1] in ';,:':
                break
        if before and after_clean:
            case_name = ' '.join(before + [tokens[idx]] + after_clean)
            case_name = clean_case_name(case_name)
            if (len(case_name) > 5 and
                ' v.' in case_name and
                not any(word in case_name.lower() for word in ['exhibit', 'deposition', 'evidence', 'testimony', 'allowing', 'commentary', 'argument', 'federal rules'])):
                _recent_case_names.append(case_name)
                if len(_recent_case_names) > 10:
                    _recent_case_names = _recent_case_names[-10:]
                return case_name
    patterns = [
        r"([A-Z][\w\u00C0-\u017F'\-\s,\.]+?\s+v\.\s+[A-Z][\w\u00C0-\u017F'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][\w\u00C0-\u017F'\-\s,\.]+?\s+vs\.\s+[A-Z][\w\u00C0-\u017F'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][\w\u00C0-\u017F'\-\s,\.]+?\s+versus\s+[A-Z][\w\u00C0-\u017F'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][\w\u00C0-\u017F]+?\s+v\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"([A-Z][\w\u00C0-\u017F]+?\s+vs\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"([A-Z][\w\u00C0-\u017F]+?\s+versus\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(In\s+re\s+[A-Z][\w\u00C0-\u017F]+?\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(Estate\s+of\s+[A-Z][\w\u00C0-\u017F]+?\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(Matter\s+of\s+[A-Z][\w\u00C0-\u017F]+?\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(Ex\s+parte\s+[A-Z][\w\u00C0-\u017F]+?\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)([A-Z][\w\u00C0-\u017F]+\s+ex\s+rel\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(People\s+v\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(State\s+v\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)(United\s+States\s+v\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)([A-Z][\w\u00C0-\u017F]+\s+et\s+al\.\s+v\.\s+[A-Z][\w\u00C0-\u017F]+)",
        r"(?:^|\s)([A-Z][\w\u00C0-\u017F]+\s*&\s*[A-Z][\w\u00C0-\u017F]+\s+v\.\s+[A-Z][\w\u00C0-\u017F]+)",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
        if matches:
            potential_case_name = matches[-1].group(1).strip()
            case_name = clean_case_name(potential_case_name)
            if case_name and not is_citation_like(case_name):
                _recent_case_names.append(case_name)
                if len(_recent_case_names) > 10:
                    _recent_case_names = _recent_case_names[-10:]
                return case_name
    return "" 