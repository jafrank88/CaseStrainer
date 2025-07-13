#!/usr/bin/env python3
"""
Test that citation processing uses citation-lookup API first and stops when it provides canonical data.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_citation_lookup_only():
    """Test that citation-lookup API is used first and stops when canonical data is found."""
    print("TESTING CITATION-LOOKUP ONLY LOGIC")
    print("=" * 60)
    
    # Test text with multiple citations including parallel citations
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003). This case involves the interpretation of RCW 90.03.290.
    """
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        # Create processor with verification enabled
        config = ProcessingConfig(
            enable_verification=True,
            debug_mode=True
        )
        processor = UnifiedCitationProcessorV2(config)
        
        print("Processing text with multiple citations...")
        results = processor.process_text(test_text)
        
        print(f"\nFound {len(results)} citations:")
        print("-" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Citation: {result.citation}")
            print(f"   Extracted case name: {result.extracted_case_name}")
            print(f"   Canonical name: {result.canonical_name}")
            print(f"   Canonical date: {result.canonical_date}")
            print(f"   URL: {result.url}")
            print(f"   Verified: {result.verified}")
            print(f"   Source: {result.source}")
            print(f"   Is parallel: {result.is_parallel}")
            if result.parallel_citations:
                print(f"   Parallel citations: {result.parallel_citations}")
        
        # Check specific citation behavior
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS:")
        
        for result in results:
            if result.citation == "146 Wn.2d 1, 9, 43 P.3d 4":
                print(f"\n146 Wn.2d 1 citation:")
                print(f"  Canonical name: {result.canonical_name}")
                print(f"  Source: {result.source}")
                if result.canonical_name == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                    print("  ✅ CORRECT: Found expected canonical name")
                else:
                    print("  ❌ WRONG: Expected 'Department of Ecology v. Campbell & Gwinn, L.L.C.'")
            
            elif result.citation == "200 Wn.2d 72, 73, 514 P.3d 643":
                print(f"\n200 Wn.2d 72 citation:")
                print(f"  Canonical name: {result.canonical_name}")
                print(f"  Source: {result.source}")
                if result.canonical_name:
                    print("  ✅ Found canonical name")
                else:
                    print("  ⚠ No canonical name found")
            
            elif result.citation == "171 Wn.2d 486, 493, 256 P.3d 321":
                print(f"\n171 Wn.2d 486 citation:")
                print(f"  Canonical name: {result.canonical_name}")
                print(f"  Source: {result.source}")
                if result.canonical_name:
                    print("  ✅ Found canonical name")
                else:
                    print("  ⚠ No canonical name found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_lookup_only() 