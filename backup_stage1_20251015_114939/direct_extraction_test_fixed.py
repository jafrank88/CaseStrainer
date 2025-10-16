#!/usr/bin/env python3
"""
Direct test of case name extraction logic with enhanced logging
"""

import re
import sys
import logging
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class CaseNameExtractor:
    def __init__(self):
        self.logger = logger
    
    def _clean_extracted_case_name(self, name: str) -> str:
        if not name:
            return ""
        # Basic cleaning
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def extract_case_name(self, text: str, citation_text: str, start: int, end: int) -> Optional[str]:
        """Extract case name from text around a citation."""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🔍 Extracting case name for: '{citation_text}' at position {start}-{end}")
        
        # Show context around the citation
        context_window = 300  # Increased context window for better debugging
        context_start = max(0, start - context_window)
        context_end = min(len(text), end + context_window)
        
        before = text[context_start:start]
        after = text[end:context_end]
        full_context = f"{before} [CITATION: {citation_text}] {after}"
        
        self.logger.debug(f"\n=== CONTEXT AROUND CITATION ===\n{full_context}\n{'='*50}")
        
        # Enhanced patterns for case name extraction
        patterns = [
            # Pattern 1: Case name followed by comma, then citation (most common)
            {
                'pattern': r'([A-Z][^.!?]*?)\s*\b(?:v\.|vs\.|v\s|in\s+re\b|ex\s+rel\.|ex\s+parte\b)[^.!?]*?' + re.escape(citation_text),
                'description': 'Case name followed by citation'
            },
            # Pattern 2: In re/Ex parte at start of sentence
            {
                'pattern': r'(?:In\s+re|Ex\s+parte|Ex\s+rel\.|Matter\s+of|In\s+the\s+Matter\s+of)\s+([A-Z][^.!?]*?)(?=\s*\d|\s*v\.|\s*vs\.|\s*\n|\s*$)',
                'description': 'In re/Ex parte at start of sentence'
            },
            # Pattern 3: Look for v. or v in the previous sentence
            {
                'pattern': r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)[.!?](?:\s+[A-Z]|\s*\n|\s*$)',
                'description': 'Case name in previous sentence'
            },
            # Pattern 4: For corporate names with Inc., LLC, etc.
            {
                'pattern': r'([A-Z][^.!?]*?\b(?:Inc\.?|L\.?L\.?C\.?|Corp\.?|Ltd\.?|Co\.?)\b[^.!?]*?\b(?:v\.?|vs\.?)\b[^.!?]*?)[^A-Za-z0-9]' + re.escape(citation_text),
                'description': 'Corporate name with Inc./LLC'
            }
        ]
        
        # Try each pattern
        for i, pattern_info in enumerate(patterns, 1):
            pattern = pattern_info['pattern']
            self.logger.debug(f"\n🔄 Trying pattern {i}: {pattern_info['description']}")
            self.logger.debug(f"   Regex: {pattern}")
            
            try:
                matches = list(re.finditer(pattern, full_context, re.IGNORECASE | re.DOTALL))
                
                if matches:
                    self.logger.debug(f"   Found {len(matches)} matches")
                    # Get the last match (most likely to be the correct one)
                    for match_num, match in enumerate(matches, 1):
                        case_name = match.group(1).strip()
                        self.logger.debug(f"   Match {match_num}: '{case_name}'")
                    
                    # Process the best match (last one)
                    best_match = matches[-1]
                    case_name = best_match.group(1).strip()
                    
                    # Clean up the case name
                    case_name = self._clean_extracted_case_name(case_name)
                    
                    # Basic validation
                    if (len(case_name.split()) >= 2 and
                        any(c.isalpha() for c in case_name) and
                        len(case_name) > 5 and
                        not any(term in case_name.lower() for term in ['court', 'appeals', 'district', 'circuit'])):
                        
                        self.logger.info(f"✅ Extracted case name: '{case_name}'")
                        return case_name
                    else:
                        self.logger.debug(f"   ❌ Match failed validation: '{case_name}'")
                else:
                    self.logger.debug("   No matches found with this pattern")
                    
            except Exception as e:
                self.logger.error(f"   ❌ Error applying pattern: {e}")
                continue
        
        self.logger.warning("❌ No valid case name found")
        return None

def main():
    test_text = """In Spokeo, Inc. v. Robins, 578 U.S. 330 (2016), the Supreme Court held that 
    a plaintiff must demonstrate concrete injury even for statutory violations. This was later 
    cited in 136 S. Ct. 1540 (2016) and 194 L. Ed. 2d 635 (2016).
    
    In another context, the court in Five Corners Family Farmers v. State, 173 Wn.2d 296, 
    306, 268 P.3d 892 (2011) discussed the importance of standing in environmental cases.
    
    The case of Branson v. Washington Fine Wine, 2 Wn. App. 2d 1048 (2018) provides 
    additional context on this issue."""

    # Test cases with their positions in the text
    test_cases = [
        {"text": "578 U.S. 330 (2016)", "start": 25, "end": 43},  # Spokeo
        {"text": "136 S. Ct. 1540 (2016)", "start": 129, "end": 150},  # Spokeo parallel
        {"text": "194 L. Ed. 2d 635 (2016)", "start": 155, "end": 178},  # Spokeo parallel
        {"text": "173 Wn.2d 296, 306, 268 P.3d 892 (2011)", "start": 247, "end": 285},  # Five Corners
        {"text": "2 Wn. App. 2d 1048 (2018)", "start": 368, "end": 391},  # Branson
    ]
    
    extractor = CaseNameExtractor()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {case['text']}")
        print("-" * 80)
        
        case_name = extractor.extract_case_name(
            test_text, 
            case['text'], 
            case['start'], 
            case['end']
        )
        
        print(f"\n📝 Result for {case['text']}:")
        if case_name:
            print(f"✅ Extracted case name: {case_name}")
        else:
            print("❌ No case name could be extracted")

if __name__ == "__main__":
    main()
