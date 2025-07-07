import warnings
import re
import time
import logging
from typing import List, Dict, Optional, Any, Union
from rapidfuzz import fuzz

try:
    from eyecite import get_citations, resolve_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

# Updated: Use the unified verify_citation from enhanced_multi_source_verifier
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from src.extract_case_name import (
    extract_case_name_triple_from_text, 
    extract_case_name_from_context_unified,
    is_valid_case_name,
    clean_case_name
)

# Import the main regex patterns from citation_utils
from src.citation_utils import extract_citations_from_text

from src.case_name_extraction_core import extract_case_name_triple, extract_case_name_from_text, extract_case_name_hinted, extract_year_from_line

from src.citation_normalizer import normalize_citation

def deprecated_warning(func):
    """Decorator to show deprecation warnings."""
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated. Use src.unified_citation_processor.UnifiedCitationProcessor instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper

class CitationExtractor:
    """
    Unified citation extractor supporting eyecite and regex extraction, deduplication,
    optional context, debug info, and a consistent return format.

    DEPRECATED: This module is deprecated. Use src.unified_citation_processor instead.

    Features:
    - Eyecite and regex extraction (with fallback)
    - Case name extraction from context
    - Deduplication
    - Optional context window around citations
    - Configurable debug/info output (stats, timing, warnings, errors)
    - Consistent, structured return format
    - Optional: batch support, context window, method/source, confidence, etc.
    """
    def __init__(self, use_eyecite: bool = True, use_regex: bool = True, context_window: int = 1000, deduplicate: bool = True, extract_case_names: bool = True):
        self.use_eyecite = use_eyecite and EYECITE_AVAILABLE
        self.use_regex = use_regex
        self.context_window = context_window
        self.deduplicate = deduplicate
        self.extract_case_names = extract_case_names
        self.regex_patterns = self._default_patterns()

    def _default_patterns(self) -> Dict[str, Any]:
        """Return a dictionary of regex patterns for different citation formats."""
        return {
            # U.S. Supreme Court - comprehensive patterns
            'us': re.compile(r"\b\d+\s+U\.?\s*S\.?\s+\d+\b"),
            'us_alt': re.compile(r"\b\d+\s+U\.\s*S\.\s+\d+\b"),
            'us_alt2': re.compile(r"\b\d+\s+United\s+States\s+\d+\b"),
            
            # Federal Reporter - comprehensive patterns
            'f2d': re.compile(r"\b\d+\s+F\.2d\s+\d+\b"),
            'f3d': re.compile(r"\b\d+\s+F\.3d\s+\d+\b"),
            'f4th': re.compile(r"\b\d+\s+F\.4th\s+\d+\b"),
            'f_supp': re.compile(r"\b\d+\s+F\.\s*Supp\.\s+\d+\b"),
            'f_supp2d': re.compile(r"\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+\b"),
            'f_supp3d': re.compile(r"\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+\b"),
            
            # Supreme Court Reporter
            'sct': re.compile(r"\b\d+\s+S\.\s*Ct\.\s+\d+\b"),
            'sct_alt': re.compile(r"\b\d+\s+Sup\.\s*Ct\.\s+\d+\b"),
            
            # Lawyers' Edition
            'led': re.compile(r"\b\d+\s+L\.\s*Ed\.\s+\d+\b"),
            'led2d': re.compile(r"\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+\b"),
            
            # Washington State Reports - comprehensive patterns
            'wn2d': re.compile(r"\b\d+\s+Wn\.2d\s+\d+\b"),
            'wn_app': re.compile(r"\b\d+\s+Wn\.\s*App\.\s+\d+\b"),
            'wn_app2d': re.compile(r"\b\d+\s+Wn\.\s*App\.\s*2d\s+\d+\b"),
            'wn_generic': re.compile(r"\b\d+\s+Wn\.\s+\d+\b"),
            'wash2d': re.compile(r"\b\d+\s+Wash\.2d\s+\d+\b"),
            'wash_app': re.compile(r"\b\d+\s+Wash\.\s*App\.\s+\d+\b"),
            'wash_generic': re.compile(r"\b\d+\s+Wash\.\s+\d+\b"),
            
            # Pacific Reporter - comprehensive patterns
            'p2d': re.compile(r"\b\d+\s+P\.2d\s+\d+\b"),
            'p3d': re.compile(r"\b\d+\s+P\.3d\s+\d+\b"),
            'p_generic': re.compile(r"\b\d+\s+P\.\s+\d+\b"),
            
            # Regional Reporters - comprehensive patterns
            'a2d': re.compile(r"\b\d+\s+A\.2d\s+\d+\b"),
            'a3d': re.compile(r"\b\d+\s+A\.3d\s+\d+\b"),
            'a_generic': re.compile(r"\b\d+\s+A\.\s+\d{2,}\b"),
            'ne2d': re.compile(r"\b\d+\s+N\.E\.2d\s+\d+\b"),
            'ne3d': re.compile(r"\b\d+\s+N\.E\.3d\s+\d+\b"),
            'ne_generic': re.compile(r"\b\d+\s+N\.E\.\s+\d{2,}\b"),
            'nw2d': re.compile(r"\b\d+\s+N\.W\.2d\s+\d+\b"),
            'nw3d': re.compile(r"\b\d+\s+N\.W\.3d\s+\d+\b"),
            'nw_generic': re.compile(r"\b\d+\s+N\.W\.\s+\d{2,}\b"),
            'se2d': re.compile(r"\b\d+\s+S\.E\.2d\s+\d+\b"),
            'se3d': re.compile(r"\b\d+\s+S\.E\.3d\s+\d+\b"),
            'se_generic': re.compile(r"\b\d+\s+S\.E\.\s+\d{2,}\b"),
            'sw2d': re.compile(r"\b\d+\s+S\.W\.2d\s+\d+\b"),
            'sw3d': re.compile(r"\b\d+\s+S\.W\.3d\s+\d+\b"),
            'sw_generic': re.compile(r"\b\d+\s+S\.W\.\s+\d{2,}\b"),
            
            # California Reports
            'cal2d': re.compile(r"\b\d+\s+Cal\.2d\s+\d+\b"),
            'cal3d': re.compile(r"\b\d+\s+Cal\.3d\s+\d+\b"),
            'cal4th': re.compile(r"\b\d+\s+Cal\.4th\s+\d+\b"),
            'cal_generic': re.compile(r"\b\d+\s+Cal\.\s+\d{2,}\b"),
            
            # Westlaw and LEXIS
            'westlaw': re.compile(r"\b\d{4}\s+WL\s+\d+\b"),
            'lexis': re.compile(r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b"),
            
            # State Reports (generic pattern) - more specific
            'state': re.compile(r"\b\d+\s+[A-Z][a-z]+\.\s+\d+\b"),
            
            # Year-based citations
            'year_citation': re.compile(r"\b\d{4}\s+U\.S\.\s+\d+\b"),
            'year_citation_alt': re.compile(r"\b\d{4}\s+[A-Z][a-z]+\.\s+\d+\b"),
        }

    def extract(self, text: str, return_context: bool = False, debug: bool = False) -> Union[List[Dict], Dict[str, Any]]:
        """
        Extract citations from text.
        Args:
            text: The input text to search for citations.
            return_context: Whether to include context around each citation.
            debug: Whether to include debug info and stats in the output.
        Returns:
            List of dicts (or dict with debug info if debug=True)
        """
        start_time = time.time()
        results = []
        seen = set()
        debug_info = {'stats': {}, 'warnings': [], 'errors': []} if debug else None

        print(f"Starting citation extraction on text of length {len(text)}")
        if not text or not text.strip():
            print("Warning: Empty or whitespace-only text provided")
            if debug:
                debug_info['warnings'].append("Empty or whitespace-only text provided")
            return [] if not debug else debug_info

        # Store original text for context extraction (before any cleaning)
        original_text = text

        # --- SHARED CASE NAME DETECTION (for all grouped citations) ---
        # We'll collect all regex matches first, then assign shared case names
        all_citation_objs = []
        if self.use_regex:
            for name, pattern in self.regex_patterns.items():
                try:
                    matches = list(pattern.finditer(original_text))
                    for match in matches:
                        citation_str = match.group(0)
                        citation_str = normalize_citation(citation_str)  # Normalize here
                        if self.deduplicate and citation_str in seen:
                            continue
                        seen.add(citation_str)
                        all_citation_objs.append({
                            'citation': citation_str,
                            'start_index': match.start(),
                            'end_index': match.end(),
                            'pattern': name
                        })
                except Exception as e:
                    if debug:
                        debug_info['warnings'].append(f"regex extraction failed for {name}: {e}")
        
        # Group citations that are part of the same parallel citation
        if self.deduplicate:
            all_citation_objs = self._group_parallel_citations(all_citation_objs, original_text)
        # Now build results with shared case names if available
        for obj in all_citation_objs:
            citation_str = obj['citation']
            case_name_triple = {'canonical_name': '', 'extracted_name': '', 'hinted_name': '', 'case_name': '', 'canonical_date': '', 'extracted_date': ''}
            if self.extract_case_names:
                case_name_triple = extract_case_name_triple(text, citation_str)
            context_val = self._get_context(text, citation_str) if (self.context_window or 200) else ""
            entry = {
                'citation': citation_str,
                'method': 'regex',
                'pattern': obj.get('pattern', ''),
                'confidence': 'medium',
                'case_name': case_name_triple['case_name'],
                'context': context_val or '',
                'extracted_case_name': case_name_triple['extracted_name'] or '',
                'hinted_case_name': case_name_triple['hinted_name'] or '',
                'canonical_date': case_name_triple['canonical_date'] or '',
                'extracted_date': case_name_triple['extracted_date'] or '',
            }
            results.append(entry)
        if debug:
            debug_info['stats']['regex_citations'] = len(results)

        # Eyecite extraction SECOND (to find any additional citations we missed)
        if self.use_eyecite:
            print("Attempting eyecite extraction SECOND (for additional citations)...")
            try:
                tokenizer = None
                if EYECITE_AVAILABLE:
                    tokenizer = AhocorasickTokenizer()
                    print("Using AhocorasickTokenizer")
                    print("Running eyecite citation extraction...")
                    eyecite_citations = get_citations(original_text, tokenizer=tokenizer)
                    for c in eyecite_citations:
                        # Extract citation text from eyecite object properly
                        citation_str = extract_citation_text_from_eyecite(c)
                        citation_str = normalize_citation(citation_str)  # Normalize here
                        
                        # Skip empty citations (filtered out short citations)
                        if not citation_str or not citation_str.strip():
                            continue
                            
                        if self.deduplicate and citation_str in seen:
                            continue
                        seen.add(citation_str)
                        
                        # Get case name triple for eyecite citations too
                        case_name_triple = {'canonical_name': '', 'extracted_name': '', 'hinted_name': '', 'case_name': '', 'canonical_date': '', 'extracted_date': ''}
                        if self.extract_case_names:
                            case_name_triple = extract_case_name_triple(text, citation_str)
                        
                        entry = {
                            'citation': citation_str,
                            'method': 'eyecite',
                            'pattern': 'eyecite',
                            'confidence': 'medium',
                            'case_name': case_name_triple['case_name'],
                            'context': self._get_context(text, citation_str) if (self.context_window or 200) else "",
                            'extracted_case_name': case_name_triple['extracted_name'],
                            'hinted_case_name': case_name_triple['hinted_name'],
                            'canonical_date': case_name_triple['canonical_date'],
                            'extracted_date': case_name_triple['extracted_date'],
                        }
                        results.append(entry)
                else:
                    print("Eyecite not available")
                    if debug:
                        debug_info['warnings'].append("Eyecite not available")
                if debug:
                    debug_info['stats']['eyecite_citations'] = len(results)
            except Exception as e:
                print(f"Eyecite extraction failed: {e}")
                if debug:
                    debug_info['warnings'].append(f"eyecite extraction failed: {e}")

        print(f"\nExtraction complete. Found {len(results)} total citations.")
        if debug:
            debug_info['stats']['total_citations'] = len(results)
            debug_info['stats']['processing_time'] = time.time() - start_time
            debug_info['citations'] = results
            return debug_info
        return results

    def _get_context(self, text: str, citation: str) -> str:
        """Return a window of context around the first occurrence of the citation. Default window is 1000 if not set."""
        window = self.context_window if self.context_window and self.context_window > 0 else 1000
        idx = text.find(citation)
        if idx == -1:
            return ""
        
        start = max(0, idx - window // 2)
        end = min(len(text), idx + len(citation) + window // 2)
        return text[start:end]

    def extract_case_names_from_text(self, text, citations):
        """Extract case names from text using citation context."""
        case_names = []
        for citation in citations:
            citation_text = str(citation)
            case_name = extract_case_name_from_text(text, citation_text)
            if case_name:
                case_names.append({
                    'citation': citation_text,
                    'case_name': case_name,
                    'method': 'context'
                })
        return case_names

    def _extract_case_name_from_context(self, text, citation):
        """Extract case name from context around a citation using canonical function."""
        idx = text.find(citation)
        if idx == -1:
            return None
        
        # Look for case name before the citation
        before_context = text[max(0, idx - 500):idx]
        
        # Use the canonical unified function
        case_name = extract_case_name_from_context_unified(before_context, citation)
        
        if case_name and is_valid_case_name(case_name):
            return clean_case_name(case_name)
        
        return None

    def _is_valid_case_name(self, case_name):
        """Check if a case name is valid using canonical function."""
        return is_valid_case_name(case_name)

    def _clean_case_name(self, case_name):
        """Clean and normalize a case name using canonical function."""
        return clean_case_name(case_name)

    def extract_citations_with_case_names(self, text: str) -> Dict[str, Any]:
        """
        Extract citations and case names from text.
        
        Args:
            text: The input text to search for citations and case names
            
        Returns:
            Dictionary containing citations, case names, and metadata
        """
        try:
            # Extract citations using the main extract method
            citations_result = self.extract(text, return_context=True, debug=False)
            
            # Extract case names from the text
            case_names = []
            if self.extract_case_names:
                # Extract case names from the text using regex patterns
                case_names = self._extract_case_names_from_text(text)
            
            # Prepare the result
            result = {
                'citations': citations_result,
                'case_names': case_names,
                'metadata': {
                    'text_length': len(text),
                    'citations_found': len(citations_result),
                    'case_names_found': len(case_names),
                    'extraction_method': 'unified_extractor'
                }
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Error in extract_citations_with_case_names: {str(e)}")
            return {
                'citations': [],
                'case_names': [],
                'metadata': {
                    'error': str(e),
                    'text_length': len(text) if text else 0
                }
            }

    def _extract_case_names_from_text(self, text: str) -> List[str]:
        """
        Extract case names from text using regex patterns.
        
        Args:
            text: The input text
            
        Returns:
            List of extracted case names
        """
        case_names = []
        
        # Common case name patterns
        patterns = [
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+v\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+vs\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+versus\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\bIn\s+re\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
            r'\b([A-Z][A-Za-z\'\-\s,\.]+)\s+ex\s+rel\.\s+([A-Z][A-Za-z\'\-\s,\.]+?)(?:\s*[,;]|\s*$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    # For "X v. Y" patterns
                    case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:
                    # For "In re X" or "X ex rel. Y" patterns
                    case_name = match.group(0).strip()
                
                # Clean and validate the case name
                if self._is_valid_case_name(case_name):
                    case_names.append(case_name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_case_names = []
        for case_name in case_names:
            if case_name not in seen:
                seen.add(case_name)
                unique_case_names.append(case_name)
        
        return unique_case_names

    def _group_parallel_citations(self, citation_objs, text):
        """Group citations that are part of the same parallel citation, but also return each as a separate entry for verification."""
        if not citation_objs:
            return citation_objs
        
        # Sort by start position
        citation_objs.sort(key=lambda x: x['start_index'])
        
        grouped = []
        i = 0
        while i < len(citation_objs):
            current = citation_objs[i]
            group = [current]
            
            # Look for citations that are close together and might be parallel
            j = i + 1
            while j < len(citation_objs):
                next_citation = citation_objs[j]
                
                # Check if citations are close together (within 50 characters)
                if next_citation['start_index'] - current['end_index'] <= 50:
                    # Check if they're separated by commas or other separators
                    between_text = text[current['end_index']:next_citation['start_index']]
                    if re.search(r'[,;]\s*', between_text):
                        group.append(next_citation)
                        current = next_citation
                        j += 1
                        continue
                
                break
            
            if len(group) > 1:
                # Add each component as a separate entry for verification
                for obj in group:
                    component_obj = obj.copy()
                    component_obj['is_parallel_component'] = True
                    grouped.append(component_obj)
                # Also add the combined group for context/cluster display
                combined_citation = ', '.join([obj['citation'] for obj in group])
                combined_obj = {
                    'citation': combined_citation,
                    'start_index': group[0]['start_index'],
                    'end_index': group[-1]['end_index'],
                    'pattern': 'parallel',
                    'is_parallel': True,
                    'is_parallel_group': True,
                    'components': group
                }
                grouped.append(combined_obj)
            else:
                grouped.append(current)
            
            i = j
        
        return grouped

    def _is_valid_case_name(self, case_name: str) -> bool:
        """
        Check if a case name is valid.
        
        Args:
            case_name: The case name to validate
            
        Returns:
            bool: True if valid
        """
        if not case_name or len(case_name) < 5:
            return False
        
        # Must contain typical case name patterns
        case_patterns = [
            r'\b[A-Z][a-z]+\s+(?:v\.|vs\.|versus)\s+[A-Z][a-z]+',  # e.g., "Smith v. Jones"
            r'\bIn\s+re\s+[A-Z][a-z]+',  # e.g., "In re Smith"
            r'\b[A-Z][a-z]+\s+(?:ex\s+rel\.|ex\s+rel)\s+[A-Z][a-z]+',  # e.g., "State ex rel. Smith"
        ]
        
        for pattern in case_patterns:
            if re.search(pattern, case_name, re.IGNORECASE):
                return True
        
        return False

    def extract_citations(self, text: str) -> List[Dict]:
        """
        Extract only citations from text (without case names).
        
        Args:
            text: The input text to search for citations
            
        Returns:
            List of citation dictionaries
        """
        try:
            result = self.extract(text, return_context=True, debug=False)
            return result if isinstance(result, list) else []
        except Exception as e:
            logging.error(f"Error in extract_citations: {str(e)}")
            return []

def normalize_washington_citations(citation_text: str) -> str:
    """Normalize Washington citations from Wn. to Wash. format."""
    # Wn.2d -> Wash. 2d
    citation_text = re.sub(r'\bWn\.2d\b', 'Wash. 2d', citation_text)
    # Wn.3d -> Wash. 3d  
    citation_text = re.sub(r'\bWn\.3d\b', 'Wash. 3d', citation_text)
    # Wn. App. -> Wash. App.
    citation_text = re.sub(r'\bWn\. App\.\b', 'Wash. App.', citation_text)
    # Wn. -> Wash.
    citation_text = re.sub(r'\bWn\.\b', 'Wash.', citation_text)
    return citation_text

def extract_all_citations(text: str, logger=None) -> List[Dict]:
    """
    Extract all citations from text using the unified extractor.
    
    This function now delegates to the unified citation extraction system
    for consistency across the codebase.
    
    Args:
        text: The text to extract citations from
        logger: Optional logger instance
        
    Returns:
        List of citation dictionaries with metadata
    """
    from src.unified_citation_extractor import extract_all_citations as unified_extract
    return unified_extract(text, logger)

def verify_citation(citation: str, use_enhanced: bool = True) -> dict:
    """Verify a citation using the unified workflow (verify_citation_unified_workflow)."""
    verifier = EnhancedMultiSourceVerifier()
    return verifier.verify_citation_unified_workflow(citation)

def extract_case_name_from_line(line):
    # Look for the last 'v.' or 'vs.' before the first citation
    # This is a simple fallback method
    pass

def extract_year_from_line(line):
    # Look for a year in parentheses at the end
    # This is a simple fallback method
    pass

def count_washington_citations(citations: List[Dict]) -> Dict:
    """Count Washington citations and provide statistics."""
    washington_citations = []
    for citation_info in citations:
        citation = citation_info['citation']
        if 'Wash.' in citation:
            washington_citations.append(citation_info)
    
    # Count by source
    regex_count = len([c for c in washington_citations if c['source'] == 'regex'])
    eyecite_count = len([c for c in washington_citations if c['source'] == 'eyecite'])
    
    return {
        "total_washington": len(washington_citations),
        "regex_washington": regex_count,
        "eyecite_washington": eyecite_count,
        "washington_citations": washington_citations
    }

def extract_citation_text_from_eyecite(citation_obj):
    """Extract citation text from eyecite object properly."""
    if isinstance(citation_obj, str):
        citation_str = citation_obj
    else:
        citation_str = str(citation_obj)
    
    # Filter out short form citations early
    if any(pattern in citation_str for pattern in [
        "IdCitation('Id.", 
        "IdCitation('id.", 
        "IdCitation('Ibid.", 
        "IdCitation('ibid.",
        "ShortCaseCitation(",
        "UnknownCitation(",
        "SupraCitation(",
        "InfraCitation("
    ]):
        return ""  # Return empty string for short citations to filter them out
    
    # Extract citation from FullCaseCitation format
    import re
    full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
    if full_case_match:
        extracted = full_case_match.group(1)
        # Additional check for short citations within FullCaseCitation
        if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
            return ""  # Filter out short citations
        return extracted
    
    # Extract citation from ShortCaseCitation format
    short_case_match = re.search(r"ShortCaseCitation\('([^']+)'", citation_str)
    if short_case_match:
        extracted = short_case_match.group(1)
        # Filter out short citations
        if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
            return ""  # Filter out short citations
        return extracted
    
    # Extract citation from FullLawCitation format
    law_match = re.search(r"FullLawCitation\('([^']+)'", citation_str)
    if law_match:
        return law_match.group(1)
    
    # If it's an object with a 'cite' attribute (eyecite objects)
    if hasattr(citation_obj, 'cite') and citation_obj.cite:
        cite_text = citation_obj.cite
        # Filter out short citations
        if cite_text.lower().startswith(('id.', 'ibid.')) or ' at ' in cite_text.lower():
            return ""  # Filter out short citations
        return cite_text
    
    # If it's an object with a 'citation' attribute
    if hasattr(citation_obj, 'citation') and citation_obj.citation:
        cite_text = citation_obj.citation
        # Filter out short citations
        if cite_text.lower().startswith(('id.', 'ibid.')) or ' at ' in cite_text.lower():
            return ""  # Filter out short citations
        return cite_text
    
    # If it's an object with 'groups' attribute (eyecite objects)
    if hasattr(citation_obj, 'groups') and citation_obj.groups:
        groups = citation_obj.groups
        volume = groups.get('volume', '')
        reporter = groups.get('reporter', '')
        page = groups.get('page', '')
        if volume and reporter and page:
            return f"{volume} {reporter} {page}"
    
    # Fallback to string representation
    return citation_str 