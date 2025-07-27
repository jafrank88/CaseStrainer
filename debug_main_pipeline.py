#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig

def debug_main_pipeline():
    """Debug the case name extraction in the main processing pipeline."""
    
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
    
    print("=== MAIN PIPELINE DEBUG ===")
    
    # Step 1: Extract citations
    print("\n1. EXTRACTING CITATIONS")
    citations = processor._extract_with_regex(test_text)
    print(f"Found {len(citations)} citations")
    
    for i, citation in enumerate(citations):
        print(f"   {i+1}. {citation.citation}")
        print(f"      Start: {citation.start_index}, End: {citation.end_index}")
        print(f"      Extracted case name: {citation.extracted_case_name}")
        print()
    
    # Step 2: Check if case names are being extracted correctly
    print("\n2. CASE NAME EXTRACTION CHECK")
    for citation in citations:
        if '196 Wn. 2d 285' in citation.citation:
            print(f"Citation: {citation.citation}")
            print(f"Context: {citation.context}")
            print(f"Extracted case name: {citation.extracted_case_name}")
            
            # Check if the context includes Lakehaven
            if "Lakehaven" in citation.context:
                print("⚠️  WARNING: Context includes 'Lakehaven'")
            if "Davison" in citation.context:
                print("✅ Context includes 'Davison'")
            print()

if __name__ == "__main__":
    debug_main_pipeline() 