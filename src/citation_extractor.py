import re
import time
from typing import List, Dict, Optional, Any, Union

try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer, HyperscanTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

class CitationExtractor:
    """
    Unified citation extractor supporting eyecite and regex extraction, deduplication,
    optional context, debug info, and a consistent return format.

    Features:
    - Eyecite and regex extraction (with fallback)
    - Deduplication
    - Optional context window around citations
    - Configurable debug/info output (stats, timing, warnings, errors)
    - Consistent, structured return format
    - Optional: batch support, context window, method/source, confidence, etc.
    """
    def __init__(self, use_eyecite: bool = True, use_regex: bool = True, context_window: int = 0, deduplicate: bool = True):
        self.use_eyecite = use_eyecite and EYECITE_AVAILABLE
        self.use_regex = use_regex
        self.context_window = context_window
        self.deduplicate = deduplicate
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

        # Eyecite extraction
        if self.use_eyecite:
            print("Attempting eyecite extraction...")
            try:
                tokenizer = None
                if EYECITE_AVAILABLE:
                    try:
                        tokenizer = HyperscanTokenizer()
                        print("Using HyperscanTokenizer")
                    except Exception as e:
                        print(f"Falling back to AhocorasickTokenizer: {e}")
                        tokenizer = AhocorasickTokenizer()
                    
                    print("Running eyecite citation extraction...")
                    citations = get_citations(text, tokenizer=tokenizer)
                    print(f"Eyecite found {len(citations)} citations")
                    
                    for c in citations:
                        citation_str = str(c)
                        if self.deduplicate and citation_str in seen:
                            continue
                        seen.add(citation_str)
                        entry = {
                            'citation': citation_str,
                            'method': 'eyecite',
                            'confidence': 'high',
                        }
                        if return_context and self.context_window > 0:
                            entry['context'] = self._get_context(text, citation_str)
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

        # Regex extraction
        if self.use_regex:
            print("\nAttempting regex extraction...")
            for name, pattern in self.regex_patterns.items():
                try:
                    matches = list(pattern.finditer(text))
                    print(f"Pattern '{name}' found {len(matches)} matches")
                    for match in matches:
                        citation_str = match.group(0)
                        if self.deduplicate and citation_str in seen:
                            continue
                        seen.add(citation_str)
                        entry = {
                            'citation': citation_str,
                            'method': 'regex',
                            'pattern': name,
                            'confidence': 'medium',
                        }
                        if return_context and self.context_window > 0:
                            entry['context'] = self._get_context(text, citation_str)
                        results.append(entry)
                        print(f"Added citation: {citation_str}")
                except Exception as e:
                    print(f"Regex extraction failed for pattern '{name}': {e}")
                    if debug:
                        debug_info['warnings'].append(f"regex extraction failed for {name}: {e}")
            
            if debug:
                debug_info['stats']['regex_citations'] = len(results)

        print(f"\nExtraction complete. Found {len(results)} total citations.")
        if debug:
            debug_info['stats']['total_citations'] = len(results)
            debug_info['stats']['processing_time'] = time.time() - start_time
            debug_info['citations'] = results
            return debug_info
        return results

    def _get_context(self, text: str, citation: str) -> str:
        """Return a window of context around the first occurrence of the citation."""
        idx = text.find(citation)
        if idx == -1:
            return ""
        start = max(0, idx - self.context_window)
        end = min(len(text), idx + len(citation) + self.context_window)
        return text[start:end] 