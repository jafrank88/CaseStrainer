import re
import time
from typing import List, Dict, Optional, Any, Union
from rapidfuzz import fuzz

try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

# Updated: Use the unified verify_citation from enhanced_multi_source_verifier
from src.enhanced_multi_source_verifier import verify_citation, EnhancedMultiSourceVerifier
from src.extract_case_name import (
    extract_case_name_triple_from_text, 
    extract_case_name_from_context_unified,
    is_valid_case_name,
    clean_case_name
)
from src.case_name_extraction_core import extract_case_name_triple, extract_case_name_from_text, extract_case_name_hinted

class CitationExtractor:
    """
    Unified citation extractor supporting eyecite and regex extraction, deduplication,
    optional context, debug info, and a consistent return format.

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
        # Now build results with shared case names if available
        for obj in all_citation_objs:
            citation_str = obj['citation']
            case_name_triple = {'canonical_name': '', 'extracted_name': '', 'hinted_name': ''}
            if self.extract_case_names:
                case_name_triple = extract_case_name_triple(text, citation_str)
            context_val = self._get_context(text, citation_str) if (self.context_window or 200) else ""
            entry = {
                'citation': citation_str,
                'method': 'regex',
                'pattern': obj.get('pattern', ''),
                'confidence': 'medium',
                'case_name': case_name_triple['canonical_name'],
                'context': context_val or '',
                'extracted_case_name': case_name_triple['extracted_name'] or '',
                'hinted_case_name': case_name_triple['hinted_name'] or '',
                'extracted_date': extract_year_from_line(text) or '',
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
                    citations = get_citations(text, tokenizer=tokenizer)
                    print(f"Eyecite found {len(citations)} citations")
                    for c in citations:
                        citation_str = str(c)
                        if self.deduplicate and citation_str in seen:
                            continue
                        seen.add(citation_str)
                        
                        # Extract case name if enabled (using original text)
                        case_name = None
                        if self.extract_case_names:
                            case_name = extract_case_name_triple(text, citation_str)
                            # Only set case_name if it is found in the context and is not None/empty
                            if not case_name:
                                case_name = ''
                            else:
                                print(f"Extracted case name: {case_name}")
                        # Always extract context (using original text)
                        context_val = self._get_context(text, citation_str) if (self.context_window or 200) else ""
                        entry = {
                            'citation': citation_str,
                            'method': 'eyecite',
                            'confidence': 'high',
                            'case_name': case_name,  # will be '' if not found
                            'context': context_val or '',
                            'extracted_case_name': case_name or '',
                            'extracted_date': extract_year_from_line(text) or '',
                        }
                        results.append(entry)
                        print(f"Added citation: {citation_str}")
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
        start = max(0, idx - window)
        end = min(len(text), idx + len(citation) + window)
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
    
    def _is_valid_case_name(self, case_name):
        """Check if extracted text looks like a valid case name using canonical function."""
        return is_valid_case_name(case_name)
    
    def _clean_case_name(self, case_name):
        """Clean up extracted case name using canonical function."""
        return clean_case_name(case_name)

def extract_all_citations(text: str, use_enhanced: bool = True) -> list:
    """
    Extract all citations from text using the unified citation extractor.
    Args:
        text (str): The text to extract citations from
        use_enhanced (bool): Ignored, kept for compatibility
    Returns:
        list: List of extracted citation dicts
    """
    from src.unified_citation_extractor import extract_all_citations
    return extract_all_citations(text)

def verify_citation(citation: str, use_enhanced: bool = True) -> dict:
    """Verify a citation using the unified workflow (verify_citation_unified_workflow)."""
    verifier = EnhancedMultiSourceVerifier()
    return verifier.verify_citation_unified_workflow(citation)

def extract_case_name_from_line(line):
    # Look for the last 'v.' or 'vs.' before the first citation
    match = re.search(r'([A-Z][^,]+?\s+v\.?\s+[A-Z][^,]+)', line)
    if match:
        return match.group(1).strip()
    return ""

def extract_year_from_line(line):
    # Look for a year in parentheses at the end
    match = re.search(r'\((19|20)\d{2}\)', line)
    if match:
        return match.group(1)
    # Fallback: look for any 4-digit year
    match = re.search(r'(19|20)\d{2}', line)
    if match:
        return match.group(0)
    return "" 