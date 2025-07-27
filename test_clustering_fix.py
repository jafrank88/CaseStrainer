#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig

def test_clustering_fix():
    """Test that the clustering fix prevents incorrect case name propagation."""
    
    # Test text with both citations that have the same year (2020) but different case names
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
        enable_verification=False  # Disable verification to focus on extraction
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Process the text
    results = processor.process_text(test_text)
    
    print("=== TESTING CLUSTERING FIX ===")
    print(f"Found {len(results['citations'])} citations")
    print()
    
    # Print all citations to see their exact format
    print("All citations found:")
    for i, citation in enumerate(results['citations']):
        print(f"  {i+1}. '{citation.citation}'")
    print()
    
    # Check the specific citations
    lakehaven_citation = None
    davison_citation = None
    
    for citation in results['citations']:
        if '195 Wn. 2d 742' in citation.citation:
            lakehaven_citation = citation
        elif '196 Wn. 2d 285' in citation.citation:
            davison_citation = citation
    
    print("=== RESULTS ===")
    if lakehaven_citation:
        print(f"195 Wn. 2d 742:")
        print(f"  Citation: {lakehaven_citation.citation}")
        print(f"  Extracted case name: {lakehaven_citation.extracted_case_name}")
        print(f"  Extracted date: {lakehaven_citation.extracted_date}")
        print(f"  Expected: Lakehaven Water & Sewer Dist. v. City of Fed. Way")
        print()
    else:
        print("❌ 195 Wn. 2d 742 not found")
        print()
    
    if davison_citation:
        print(f"196 Wn. 2d 285:")
        print(f"  Citation: {davison_citation.citation}")
        print(f"  Extracted case name: {davison_citation.extracted_case_name}")
        print(f"  Extracted date: {davison_citation.extracted_date}")
        print(f"  Expected: Davison v. State")
        print()
    else:
        print("❌ 196 Wn. 2d 285 not found")
        print()
    
    # Check if the fix worked
    if lakehaven_citation and davison_citation:
        lakehaven_correct = "Lakehaven" in (lakehaven_citation.extracted_case_name or "")
        davison_correct = "Davison" in (davison_citation.extracted_case_name or "")
        
        print("=== FIX VERIFICATION ===")
        if lakehaven_correct and davison_correct:
            print("✅ FIX WORKED: Each citation has its correct case name")
            print("✅ No incorrect propagation between citations with same year")
        elif lakehaven_correct and not davison_correct:
            print("⚠️  PARTIAL: Lakehaven correct, but Davison incorrect")
        elif not lakehaven_correct and davison_correct:
            print("⚠️  PARTIAL: Davison correct, but Lakehaven incorrect")
        else:
            print("❌ FIX FAILED: Both citations have incorrect case names")
    else:
        print("❌ Cannot verify fix - missing citations")

if __name__ == "__main__":
    test_clustering_fix() 