"""
Safe Wrapper for UnifiedCitationProcessorV2
Provides timeout protection, memory limits, and error recovery
Cross-platform compatible (Windows/Linux/Mac)
"""

import time
import threading
import re
from typing import List, Dict, Any, Optional
from functools import wraps

# Safety limits
MAX_TEXT_SIZE = 150000       # 150KB max text size
MAX_REGEX_TIME = 30          # 30s per regex operation
MAX_EXTRACTION_TIME = 180    # 3 minutes total extraction
MAX_CITATIONS = 200          # Max citations to process
CONTEXT_WINDOW = 150         # Smaller context window

def timeout(seconds):
    """Cross-platform timeout decorator using threading."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                logger.info(f"[TIMEOUT] Function {func.__name__} timed out after {seconds} seconds")
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator

class SafeUnifiedCitationProcessor:
    """
    Safe wrapper for UnifiedCitationProcessorV2 with comprehensive protection.
    """
    
    def __init__(self):
        logger.info("[SAFE PROCESSOR] Initializing safe citation processor...")
        
        self.processor = None
        self.config = None
        
        try:
            # Import and configure the processor
            from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
            
            # Create safe configuration
            self.config = ProcessingConfig(
                use_eyecite=False,               # Disable eyecite (can be slow)
                use_regex=True,                  # Keep regex but with limits
                extract_case_names=True,         # Keep case name extraction
                extract_dates=True,              # Keep date extraction
                enable_clustering=False,         # Disable clustering initially
                enable_deduplication=True,       # Keep deduplication
                enable_verification=False,       # Disable API calls
                context_window=CONTEXT_WINDOW,   # Smaller context
                min_confidence=0.3,              # Lower threshold
                max_citations_per_text=MAX_CITATIONS,
                debug_mode=True
            )
            
            # Initialize processor
            self.processor = UnifiedCitationProcessorV2(self.config)
            logger.info("[SAFE PROCESSOR] Processor initialized successfully")
            
        except Exception as e:
            logger.error(f"[SAFE PROCESSOR ERROR] Failed to initialize: {e}")
            self.processor = None
    
    @timeout(MAX_EXTRACTION_TIME)
    def process_text_safe(self, text: str) -> List[Dict[str, Any]]:
        """
        Safely process text with comprehensive protection.
        """
        if not self.processor:
            logger.info("[SAFE PROCESSOR] No processor available")
            return []
        
        logger.info(f"[SAFE PROCESSOR] Processing {len(text):,} characters...")
        start_time = time.time()
        
        try:
            # Pre-process text
            text = self._preprocess_text_safe(text)
            
            # Extract citations with safe regex
            citations = self._extract_citations_safe(text)
            
            # Convert to expected format
            result = self._convert_to_dict_format(citations)
            
            elapsed = time.time() - start_time
            logger.info(f"[SAFE PROCESSOR] Completed in {elapsed:.2f}s - {len(result)} citations")
            
            return result
            
        except TimeoutError:
            logger.info("[SAFE PROCESSOR] Processing timed out")
            return []
        except Exception as e:
            logger.error(f"[SAFE PROCESSOR ERROR] {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _preprocess_text_safe(self, text: str) -> str:
        """Safely preprocess text with size limits."""
        logger.info(f"[SAFE PREPROCESS] Original text: {len(text):,} characters")
        
        # Limit text size
        if len(text) > MAX_TEXT_SIZE:
            logger.info(f"[SAFE PREPROCESS] Truncating to {MAX_TEXT_SIZE:,} characters")
            text = text[:MAX_TEXT_SIZE]
        
        # Clean up text - remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Reduce multiple newlines
        text = re.sub(r' {3,}', '  ', text)            # Reduce multiple spaces
        
        logger.info(f"[SAFE PREPROCESS] Processed text: {len(text):,} characters")
        return text
    
    @timeout(MAX_REGEX_TIME)
    def _extract_citations_safe(self, text: str) -> List[Any]:
        """Extract citations using safe regex patterns."""
        logger.info("[SAFE EXTRACT] Starting citation extraction...")
        
        citations = []
        
        # Use simplified, safe regex patterns
        safe_patterns = {
            'wash2d': r'\b(\d{1,3})\s+(?:Wn\.2d|Wash\.2d)\s+(\d{1,4})\b',
            'p3d': r'\b(\d{1,3})\s+P\.3d\s+(\d{1,4})\b',
            'p2d': r'\b(\d{1,3})\s+P\.2d\s+(\d{1,4})\b',
            'f3d': r'\b(\d{1,3})\s+F\.3d\s+(\d{1,4})\b',
            'us': r'\b(\d{1,3})\s+U\.S\.\s+(\d{1,4})\b',
        }
        
        for pattern_name, pattern in safe_patterns.items():
            try:
                logger.info(f"[SAFE EXTRACT] Trying pattern: {pattern_name}")
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for i, match in enumerate(matches):
                    if len(citations) >= MAX_CITATIONS:
                        logger.info(f"[SAFE EXTRACT] Reached citation limit ({MAX_CITATIONS})")
                        break
                    
                    citation_text = match.group(0)
                    
                    # Create citation object
                    citation = self._create_safe_citation(
                        citation_text, 
                        match.start(), 
                        match.end(), 
                        text,
                        pattern_name
                    )
                    
                    citations.append(citation)
                    
                    # Progress update
                    if i > 0 and i % 20 == 0:
                        logger.info(f"[SAFE EXTRACT] Found {i} citations with {pattern_name}")
                
            except Exception as e:
                logger.error(f"[SAFE EXTRACT] Error with pattern {pattern_name}: {e}")
                continue
        
        logger.info(f"[SAFE EXTRACT] Extracted {len(citations)} citations")
        return citations
    
    def _create_safe_citation(self, citation_text: str, start: int, end: int, 
                             full_text: str, pattern: str) -> Any:
        """Create citation object with safe case name and date extraction."""
        
        # Create a simple citation object
        class SafeCitation:
            def __init__(self):
                self.citation = citation_text
                self.start_index = start
                self.end_index = end
                self.method = "safe_regex"
                self.pattern = pattern
                self.extracted_case_name = None
                self.extracted_date = None
                self.confidence = 0.6
                self.source = "Main Body"
        
        citation = SafeCitation()
        
        try:
            # Extract case name safely
            citation.extracted_case_name = self._extract_case_name_safe(
                full_text, start, end
            )
            
            # Extract date safely
            citation.extracted_date = self._extract_date_safe(
                full_text, start, end
            )
            
        except Exception as e:
            logger.error(f"[SAFE CITATION] Error extracting metadata: {e}")
        
        return citation
    
    def _extract_case_name_safe(self, text: str, start: int, end: int) -> Optional[str]:
        """Safely extract case name with limited context."""
        try:
            # Get limited context around citation
            context_start = max(0, start - CONTEXT_WINDOW)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end]
            
            # Simple pattern for case names
            patterns = [
                r'([A-Z][A-Za-z\s&,\.\']{5,60})\s+v\.\s+([A-Z][A-Za-z\s&,\.\']{5,60})',
                r'(In\s+re\s+[A-Z][A-Za-z\s&,\.\']{5,40})',
                r'(State\s+v\.\s+[A-Z][A-Za-z\s&,\.\']{5,40})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, context)
                if match:
                    if 'v.' in match.group(0):
                        return match.group(0)
                    else:
                        return match.group(1)
            
        except Exception as e:
            logger.error(f"[SAFE CASE NAME] Error: {e}")
        
        return None
    
    def _extract_date_safe(self, text: str, start: int, end: int) -> Optional[str]:
        """Safely extract date with limited context."""
        try:
            # Get limited context around citation
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            context = text[context_start:context_end]
            
            # Simple year patterns
            year_patterns = [
                r'\((\d{4})\)',     # (2022)
                r'\b(\d{4})\b',     # 2022
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, context)
                for year in matches:
                    year_int = int(year)
                    if 1950 <= year_int <= 2030:
                        return year
            
        except Exception as e:
            logger.error(f"[SAFE DATE] Error: {e}")
        
        return None
    
    def _convert_to_dict_format(self, citations: List[Any]) -> List[Dict[str, Any]]:
        """Convert citation objects to dictionary format."""
        result = []
        
        for citation in citations:
            try:
                citation_dict = {
                    'citation': getattr(citation, 'citation', ''),
                    'case_name': getattr(citation, 'extracted_case_name', None),
                    'year': getattr(citation, 'extracted_date', None),
                    'source': getattr(citation, 'source', 'Main Body'),
                    'confidence': getattr(citation, 'confidence', 0.5),
                    'method': getattr(citation, 'method', 'safe_regex'),
                    'pattern': getattr(citation, 'pattern', 'unknown')
                }
                result.append(citation_dict)
                
            except Exception as e:
                logger.error(f"[SAFE CONVERT] Error converting citation: {e}")
                continue
        
        return result

# Create convenience function
def create_safe_processor():
    """Create a safe citation processor instance."""
    return SafeUnifiedCitationProcessor() 