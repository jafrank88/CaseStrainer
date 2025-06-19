import re
import time
from typing import List, Dict, Optional, Any, Union

try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

# Import case name extraction functions
from src.extract_case_name import extract_case_name_from_text, extract_case_name_and_citation

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
    def __init__(self, use_eyecite: bool = True, use_regex: bool = True, context_window: int = 500, deduplicate: bool = True, extract_case_names: bool = True):
        self.use_eyecite = use_eyecite and EYECITE_AVAILABLE
        self.use_regex = use_regex
        self.context_window = context_window
        self.deduplicate = deduplicate
        self.extract_case_names = extract_case_names
        self.regex_patterns = self._default_patterns()

    def _default_patterns(self) -> Dict[str, Any]:
        """Return a dictionary of regex patterns for different citation formats."""
        return {
            # U.S. Supreme Court
            'us': re.compile(r"\b\d+\s+U\.S\.\s+\d+\b"),
            'us_alt': re.compile(r"\b\d+\s+U\.\s*S\.\s+\d+\b"),
            'us_alt2': re.compile(r"\b\d+\s+United\s+States\s+\d+\b"),
            
            # Federal Reporter
            'f2d': re.compile(r"\b\d+\s+F\.2d\s+\d+\b"),
            'f3d': re.compile(r"\b\d+\s+F\.3d\s+\d+\b"),
            'f_supp': re.compile(r"\b\d+\s+F\.\s*Supp\.\s+\d+\b"),
            'f_supp2d': re.compile(r"\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+\b"),
            'f_supp3d': re.compile(r"\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+\b"),
            
            # Supreme Court Reporter
            'sct': re.compile(r"\b\d+\s+S\.\s*Ct\.\s+\d+\b"),
            'sct_alt': re.compile(r"\b\d+\s+Sup\.\s*Ct\.\s+\d+\b"),
            
            # Lawyers' Edition
            'led': re.compile(r"\b\d+\s+L\.\s*Ed\.\s+\d+\b"),
            'led2d': re.compile(r"\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+\b"),
            
            # State Reports (generic pattern)
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

        # Regex extraction FIRST (to capture context and case names from original text)
        if self.use_regex:
            print("\nAttempting regex extraction FIRST (for context preservation)...")
            for name, pattern in self.regex_patterns.items():
                try:
                    matches = list(pattern.finditer(original_text))
                    print(f"Pattern '{name}' found {len(matches)} matches")
                    for match in matches:
                        citation_str = match.group(0)
                        if self.deduplicate and citation_str in seen:
                            continue
                        seen.add(citation_str)
                        
                        # Extract case name if enabled (using original text)
                        case_name = None
                        if self.extract_case_names:
                            case_name = extract_case_name_from_text(original_text, citation_str)
                            # Only set case_name if it is found in the context and is not None/empty
                            if not case_name:
                                case_name = ''
                            else:
                                print(f"Extracted case name: {case_name}")
                        # Always extract context (using original text)
                        context_val = self._get_context(original_text, citation_str) if (self.context_window or 200) else ""
                        entry = {
                            'citation': citation_str,
                            'method': 'regex',
                            'pattern': name,
                            'confidence': 'medium',
                            'case_name': case_name,  # will be '' if not found
                            'context': context_val or ''
                        }
                        results.append(entry)
                        print(f"Added citation: {citation_str}")
                except Exception as e:
                    print(f"Regex extraction failed for pattern '{name}': {e}")
                    if debug:
                        debug_info['warnings'].append(f"regex extraction failed for {name}: {e}")
            
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
                            case_name = extract_case_name_from_text(original_text, citation_str)
                            # Only set case_name if it is found in the context and is not None/empty
                            if not case_name:
                                case_name = ''
                            else:
                                print(f"Extracted case name: {case_name}")
                        # Always extract context (using original text)
                        context_val = self._get_context(original_text, citation_str) if (self.context_window or 200) else ""
                        entry = {
                            'citation': citation_str,
                            'method': 'eyecite',
                            'confidence': 'high',
                            'case_name': case_name,  # will be '' if not found
                            'context': context_val or ''
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
        """Return a window of context around the first occurrence of the citation. Default window is 200 if not set."""
        window = self.context_window if self.context_window and self.context_window > 0 else 200
        idx = text.find(citation)
        if idx == -1:
            return ""
        start = max(0, idx - window)
        end = min(len(text), idx + len(citation) + window)
        return text[start:end]

def extract_all_citations(text: str, use_enhanced: bool = True) -> List[str]:
    """
    Extract all citations from text using the enhanced extractor.
    
    Args:
        text: The input text to search for citations
        use_enhanced: Whether to use enhanced extraction (default: True)
    
    Returns:
        List of citation strings
    """
    extractor = CitationExtractor(use_eyecite=use_enhanced, use_regex=True, context_window=500)
    results = extractor.extract(text)
    return [r['citation'] for r in results]

def verify_citation(citation: str, use_enhanced: bool = True) -> Dict[str, Any]:
    """
    Verify a citation using the enhanced validator.
    
    Args:
        citation: The citation to verify
        use_enhanced: Whether to use enhanced validation (default: True)
    
    Returns:
        Dictionary with validation results
    """
    start_time = time.time()
    
    # Basic validation
    if not citation or not isinstance(citation, str):
        return {
            'valid': False,
            'error': 'Invalid citation format',
            'processing_time': time.time() - start_time
        }
    
    # Extract citations from the citation string
    extractor = CitationExtractor(use_eyecite=use_enhanced, use_regex=True, context_window=500)
    results = extractor.extract(citation)
    
    if not results:
        return {
            'valid': False,
            'error': 'No valid citation format found',
            'processing_time': time.time() - start_time
        }
    
    # Get the first result
    result = results[0]
    
    return {
        'valid': True,
        'citation': result['citation'],
        'method': result.get('method', 'unknown'),
        'confidence': result.get('confidence', 'medium'),
        'processing_time': time.time() - start_time
    } 