#!/usr/bin/env python3
"""
Test the full processing pipeline to see where case names get corrupted.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions

def test_full_processing():
    # Test text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""

    try:
        # Create processor
        options = ProcessingOptions()
        processor = EnhancedSyncProcessor(options)
        
        print("Testing full processing pipeline...")
        
        # Step 1: Fast citation extraction
        print("\n1. _extract_citations_fast:")
        citations = processor._extract_citations_fast(test_text)
        print(f"Found {len(citations)} citations:")
        for i, citation in enumerate(citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
        
        # Step 2: Local citation normalization
        print("\n2. _normalize_citations_local:")
        normalized_citations = processor._normalize_citations_local(citations, test_text)
        print(f"Normalized {len(normalized_citations)} citations:")
        for i, citation in enumerate(normalized_citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
            elif isinstance(citation, dict):
                print(f"  {i}. {citation.get('citation', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
        
        # Step 3: Local name/year extraction
        print("\n3. _extract_names_years_local:")
        enhanced_citations = processor._extract_names_years_local(normalized_citations, test_text)
        print(f"Enhanced {len(enhanced_citations)} citations:")
        for i, citation in enumerate(enhanced_citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
            elif isinstance(citation, dict):
                print(f"  {i}. {citation.get('citation', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
        
        # Step 4: Apply canonical names
        print("\n4. _apply_canonical_names_to_objects:")
        processor._apply_canonical_names_to_objects(enhanced_citations)
        print(f"After canonical names applied:")
        for i, citation in enumerate(enhanced_citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
            elif isinstance(citation, dict):
                print(f"  {i}. {citation.get('citation', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
        
        # Step 5: Cluster citations
        print("\n5. _cluster_citations_local:")
        clusters = processor._cluster_citations_local(enhanced_citations, test_text, "test_request")
        print(f"After clustering:")
        for i, citation in enumerate(enhanced_citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
            elif isinstance(citation, dict):
                print(f"  {i}. {citation.get('citation', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
        
        # Step 6: Ensure full names from master
        print("\n6. _ensure_full_names_from_master:")
        enhanced_citations = processor._ensure_full_names_from_master(enhanced_citations, test_text)
        print(f"After master function:")
        for i, citation in enumerate(enhanced_citations, 1):
            if hasattr(citation, 'citation'):
                print(f"  {i}. {citation.citation} -> {getattr(citation, 'extracted_case_name', 'N/A')}")
            elif isinstance(citation, dict):
                print(f"  {i}. {citation.get('citation', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
        
        # Step 7: Convert to dicts
        print("\n7. _convert_citations_to_dicts:")
        citations_list = processor._convert_citations_to_dicts(enhanced_citations)
        print(f"Final citations list:")
        for i, citation in enumerate(citations_list, 1):
            print(f"  {i}. {citation.get('citation', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
                
    except Exception as e:
        print(f"Exception in processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_processing()
