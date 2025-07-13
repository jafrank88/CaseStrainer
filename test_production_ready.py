#!/usr/bin/env python3
"""
Final test to verify production-ready citation processing with batch verification.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_production_ready():
    """Test the production-ready citation processing."""
    print("TESTING PRODUCTION-READY CITATION PROCESSING")
    print("=" * 60)
    
    # Test text with multiple citations including the problematic ones
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003). This case involves the interpretation of RCW 90.03.290.
    """
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        # Create processor with verification enabled
        config = ProcessingConfig(
            enable_verification=True,
            debug_mode=False  # Set to False for production
        )
        processor = UnifiedCitationProcessorV2(config)
        
        print("Processing text with batch verification...")
        results = processor.process_text(test_text)
        
        print(f"\nFound {len(results)} citations:")
        print("-" * 60)
        
        verified_count = 0
        canonical_count = 0
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Citation: {result.citation}")
            print(f"   Extracted case name: {result.extracted_case_name}")
            print(f"   Canonical name: {result.canonical_name}")
            print(f"   Canonical date: {result.canonical_date}")
            print(f"   URL: {result.url}")
            print(f"   Verified: {result.verified}")
            print(f"   Source: {result.source}")
            print(f"   Is parallel: {result.is_parallel}")
            
            if result.verified:
                verified_count += 1
            if result.canonical_name:
                canonical_count += 1
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print(f"Total citations: {len(results)}")
        print(f"Verified: {verified_count}")
        print(f"With canonical names: {canonical_count}")
        
        # Check specific results
        print("\nSPECIFIC RESULTS:")
        for result in results:
            if "146 Wn.2d 1" in result.citation:
                print(f"\n146 Wn.2d 1 citation:")
                print(f"  Canonical name: {result.canonical_name}")
                print(f"  Source: {result.source}")
                if result.canonical_name == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                    print("  ✅ CORRECT: Found expected canonical name")
                elif result.canonical_name:
                    print(f"  ⚠ Different canonical name: {result.canonical_name}")
                else:
                    print("  ❌ No canonical name found")
        
        print("\n" + "=" * 60)
        if verified_count > 0 and canonical_count > 0:
            print("✅ PRODUCTION READY: Citations are being verified and canonical data is being found")
        else:
            print("❌ NEEDS FIXING: No citations verified or no canonical data found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_production_ready() 