import re
import sys
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from unified_citation_processor_v2 import UnifiedCitationProcessorV2

@dataclass
class CitationResult:
    citation: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None

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
    
    # Initialize the processor
    processor = UnifiedCitationProcessorV2()
    
    # Test each citation
    for i, cit in enumerate(citations, 1):
        citation = CitationResult(
            citation=cit["text"],
            start_index=cit["start"],
            end_index=cit["end"]
        )
        
        # Extract case name from context
        case_name = processor._extract_case_name_from_context(test_text, citation)
        
        # Print results
        print(f"\n=== Test Case {i} ===")
        print(f"Citation: {cit['text']}")
        print(f"Position: {cit['start']}-{cit['end']}")
        print(f"Extracted Case Name: {case_name}")
        
        # Show context
        context_start = max(0, cit["start"] - 50)
        context_end = min(len(test_text), cit["end"] + 50)
        print(f"Context: ...{test_text[context_start:cit['start']]}[{test_text[cit['start']:cit['end']]}]{test_text[cit['end']:context_end]}...")

if __name__ == "__main__":
    test_case_name_extraction()
