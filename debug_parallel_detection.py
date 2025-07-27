#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig

def debug_parallel_detection():
    """Debug the parallel citation detection logic."""
    
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
    
    # Extract citations first
    citations = processor._extract_with_regex(test_text)
    print(f"Found {len(citations)} citations")
    
    # Print citation details before parallel detection
    print("\n=== BEFORE PARALLEL DETECTION ===")
    for i, citation in enumerate(citations):
        print(f"{i+1}. {citation.citation}")
        print(f"   Start: {citation.start_index}, End: {citation.end_index}")
        print(f"   Extracted case name: {citation.extracted_case_name}")
        print()
    
    # Run parallel detection
    print("=== RUNNING PARALLEL DETECTION ===")
    citations_after_parallel = processor._detect_parallel_citations(citations, test_text)
    
    # Print citation details after parallel detection
    print("\n=== AFTER PARALLEL DETECTION ===")
    for i, citation in enumerate(citations_after_parallel):
        print(f"{i+1}. {citation.citation}")
        print(f"   Start: {citation.start_index}, End: {citation.end_index}")
        print(f"   Extracted case name: {citation.extracted_case_name}")
        print(f"   Is parallel: {citation.is_parallel}")
        print(f"   Cluster ID: {getattr(citation, 'cluster_id', 'None')}")
        print(f"   Cluster members: {getattr(citation, 'cluster_members', [])}")
        print()

if __name__ == "__main__":
    debug_parallel_detection() 