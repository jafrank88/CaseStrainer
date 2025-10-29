#!/usr/bin/env python3
"""
Debug script to test async verification system
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_verification_directly():
    """Test verification directly with the UnifiedVerificationMaster"""
    
    print("ASYNC VERIFICATION DEBUG TEST")
    print("=" * 50)
    
    try:
        from src.unified_verification_master import UnifiedVerificationMaster
        
        # Test with a few sample citations from the user's data
        test_citations = [
            "548 P.3d 1086",
            "517 P.3d 7", 
            "335 P.3d 514",
            "463 U.S. 29",
            "390 U.S. 747"  # This one should be "In re Permian Basin Area Rate Cases"
        ]
        
        test_case_names = [
            "Fischer v. Kenai Peninsula Borough Sch. Dist.",
            "Sulzbach v. City & Borough of Sitka",
            "Christensen v. Alaska Sales & Serv., Inc.",
            "Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co.",
            "In re Permian Basin Area Rate Cases"
        ]
        
        test_dates = ["2024", "2022", "2014", "1983", "1968"]
        
        print(f"Testing {len(test_citations)} citations...")
        
        verifier = UnifiedVerificationMaster()
        print(f"API Key configured: {bool(verifier.api_key)}")
        print(f"Rate limit: {verifier.rate_limit} requests/hour")
        
        # Test batch verification
        results = await verifier.verify_citations_batch(
            citations=test_citations,
            extracted_case_names=test_case_names,
            extracted_dates=test_dates
        )
        
        print(f"\nRESULTS:")
        print("-" * 50)
        
        for i, result in enumerate(results):
            citation = test_citations[i]
            print(f"\n{i+1}. {citation}")
            print(f"   Verified: {result.verified}")
            print(f"   Canonical Name: {result.canonical_name}")
            print(f"   Canonical Date: {result.canonical_date}")
            print(f"   Source: {result.source}")
            if result.error:
                print(f"   Error: {result.error}")
        
        # Check success rate
        verified_count = sum(1 for r in results if r.verified)
        print(f"\nSUMMARY:")
        print(f"Verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_sync_verification():
    """Test the sync verification method used in the pipeline"""
    
    print("\n\nSYNC VERIFICATION DEBUG TEST")
    print("=" * 50)
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.citation_models import CitationResult
        
        # Create test citations
        test_citations = []
        test_data = [
            ("548 P.3d 1086", "Fischer v. Kenai Peninsula Borough Sch. Dist.", "2024"),
            ("517 P.3d 7", "Sulzbach v. City & Borough of Sitka", "2022"),
            ("463 U.S. 29", "Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co.", "1983"),
        ]
        
        for citation, case_name, date in test_data:
            cr = CitationResult()
            cr.citation = citation
            cr.extracted_case_name = case_name
            cr.extracted_date = date
            cr.verified = False
            cr.verification_status = None
            test_citations.append(cr)
        
        processor = UnifiedCitationProcessorV2()
        print(f"Verification enabled: {processor.config.enable_verification}")
        
        # Test the sync verification method
        verified_citations = processor._verify_citations_sync(test_citations)
        
        print(f"\nRESULTS:")
        print("-" * 50)
        
        for i, citation in enumerate(verified_citations):
            print(f"\n{i+1}. {citation.citation}")
            print(f"   Verified: {citation.verified}")
            print(f"   Canonical Name: {citation.canonical_name}")
            print(f"   Verification Status: {citation.verification_status}")
            print(f"   Verification Source: {citation.verification_source}")
        
        # Check success rate
        verified_count = sum(1 for c in verified_citations if c.verified)
        print(f"\nSUMMARY:")
        print(f"Verified: {verified_count}/{len(verified_citations)} ({verified_count/len(verified_citations)*100:.1f}%)")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run async test
    asyncio.run(test_verification_directly())
    
    # Run sync test
    test_sync_verification()
