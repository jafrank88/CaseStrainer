#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig

def debug_context_window():
    """Debug the actual context window being used in the main pipeline."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    # Configure processor
    config = ProcessingConfig(
        extract_case_names=True,
        enable_verification=False
    )
    processor = UnifiedCitationProcessorV2(config)
    
    print("=== CONTEXT WINDOW DEBUG ===")
    
    # Extract citations
    citations = processor._extract_with_regex(test_text)
    
    # Find the Davison citation
    davison_citation = None
    for citation in citations:
        if '196 Wn. 2d 285' in citation.citation:
            davison_citation = citation
            break
    
    if davison_citation:
        print(f"Citation: {davison_citation.citation}")
        print(f"Start index: {davison_citation.start_index}")
        print(f"End index: {davison_citation.end_index}")
        print(f"Context: {repr(davison_citation.context)}")
        print()
        
        # Check what's in the context
        if "Lakehaven" in davison_citation.context:
            print("⚠️  WARNING: Context includes 'Lakehaven'")
        if "Davison" in davison_citation.context:
            print("✅ Context includes 'Davison'")
        
        # Calculate what the context window should be
        citation_pos = davison_citation.start_index
        context_start = max(0, citation_pos - 150)
        context_end = min(len(test_text), citation_pos + len(davison_citation.citation) + 100)
        expected_context = test_text[context_start:context_end]
        
        print(f"\nExpected context window: {context_start} to {context_end}")
        print(f"Expected context: {repr(expected_context)}")
        
        if expected_context == davison_citation.context:
            print("✅ Context matches expected")
        else:
            print("❌ Context does not match expected")
    else:
        print("❌ Davison citation not found")

if __name__ == "__main__":
    debug_context_window() 