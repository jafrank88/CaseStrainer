import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CitationResult:
    citation: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None

class CaseNameExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _clean_extracted_case_name(self, name: str) -> str:
        if not name:
            return ""
        # Basic cleaning
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def _extract_case_name_from_context(self, text: str, citation: CitationResult, all_citations: Optional[List[CitationResult]] = None) -> Optional[str]:
        """Enhanced case name extraction with improved context handling and fallbacks."""
        if not citation.start_index or not citation.end_index:
            self.logger.debug("No start/end index provided for citation")
            return None
            
        # Get citation text and position
        citation_text = citation.citation
        start = citation.start_index
        end = citation.end_index
        
        self.logger.debug(f"\n{'='*50}")
        self.logger.debug(f"Processing citation: {citation_text}")
        self.logger.debug(f"Position: {start}-{end}")
        
        # Get isolated context to prevent cross-contamination
        context_window = 200
        context_start = max(0, start - context_window)
        context_end = min(len(text), end + context_window)
        
        # Extract context, ensuring we don't include other citations
        before = text[context_start:start]
        after = text[end:context_end]
        context = f"{before} [{citation_text}] {after}"
        
        self.logger.debug(f"Context: ...{context}...")
        
        # Common patterns for case name extraction
        patterns = [
            # Pattern 1: Case name followed by comma, then citation
            r'([A-Z][^.!?]*?)\s*\b(?:v\.|vs\.|v\s|in\s+re\b|ex\s+rel\.|ex\s+parte\b)[^.!?]*?' + re.escape(citation_text),
            # Pattern 2: In re/Ex parte at start of sentence
            r'(?:In\s+re|Ex\s+parte|Ex\s+rel\.)\s+([A-Z][^.!?]*?)(?=\s*\d|\s*v\.|\s*vs\.|\s*\n|\s*$)',
            # Pattern 3: Look for v. or v in the previous sentence
            r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)[.!?](?:\s+[A-Z]|\s*\n|\s*$)',
        ]
        
        # Try each pattern
        for i, pattern in enumerate(patterns, 1):
            self.logger.debug(f"\nTrying pattern {i}: {pattern}")
            matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
            
            if matches:
                self.logger.debug(f"Found {len(matches)} matches")
                # Get the last match (most likely to be the correct one)
                for match_num, match in enumerate(matches, 1):
                    case_name = match.group(1).strip()
                    self.logger.debug(f"Match {match_num}: '{case_name}'")
                
                # Process the best match (last one)
                best_match = matches[-1]
                case_name = best_match.group(1).strip()
                
                # Clean up the case name
                case_name = re.sub(r'\s+', ' ', case_name)
                case_name = re.sub(r'^[^A-Za-z]+', '', case_name)
                case_name = re.sub(r'[^A-Za-z0-9\s.,&\-\']', '', case_name)
                
                # Basic validation
                if (len(case_name.split()) >= 2 and
                    any(c.isalpha() for c in case_name) and
                    len(case_name) > 5 and
                    not any(term in case_name.lower() for term in ['court', 'appeals', 'district', 'circuit'])):
                    
                    self.logger.info(f"✅ Extracted case name: '{case_name}' for citation: '{citation_text}'")
                    return case_name
                else:
                    self.logger.debug(f"Match failed validation: '{case_name}'")
            else:
                self.logger.debug("No matches found with this pattern")
        
        self.logger.warning(f"❌ No valid case name found for citation: '{citation_text}'")
        return None

def test_case_name_extraction():
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
    Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
    legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820."""

    # Create test citations with their positions in the text
    citations = [
        {"text": "2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023)", "start": 50, "end": 85},
        {"text": "DeSean, 2 Wn.3d at 335", "start": 180, "end": 202},
        {"text": "169 Wn.2d 815, 820, 239 P.3d 354 (2010)", "start": 320, "end": 357},
        {"text": "Ervin, 169 Wn.2d at 820", "start": 512, "end": 535}
    ]
    
    # Initialize the extractor
    extractor = CaseNameExtractor()
    
    # Test each citation
    for i, cit in enumerate(citations, 1):
        citation = CitationResult(
            citation=cit["text"],
            start_index=cit["start"],
            end_index=cit["end"]
        )
        
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {cit['text']}")
        print(f"{'='*80}")
        
        # Extract case name from context
        case_name = extractor._extract_case_name_from_context(test_text, citation)
        
        # Print final result
        print(f"\n{'='*30} RESULT {'='*30}")
        print(f"Citation: {cit['text']}")
        print(f"Extracted Case Name: {case_name}")
        
        # Show the citation in context
        context_start = max(0, cit["start"] - 30)
        context_end = min(len(test_text), cit["end"] + 30)
        context = (
            f"...{test_text[context_start:cit['start']]}"
            f"[{test_text[cit['start']:cit['end']]}]"
            f"{test_text[cit['end']:context_end]}..."
        )
        print(f"\nContext: {context}")
        print("="*80)

if __name__ == "__main__":
    import sys
    test_case_name_extraction()
