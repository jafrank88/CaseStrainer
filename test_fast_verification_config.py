#!/usr/bin/env python3
"""
Test fast verification configuration with only CourtListener lookup and CaseMine
"""

import os
import sys
import time
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_fast_verification():
    """Test fast verification with only CourtListener lookup and CaseMine"""
    print("=" * 80)
    print("TESTING FAST VERIFICATION CONFIGURATION")
    print("=" * 80)
    
    # Test with real citations from a document
    test_citations = [
        "87 Wn.2d 577",
        "31 Wn.2d 100", 
        "636 F.2d 1267",
        "205 U.S. App. D.C. 139",
        "548 P.3d 226",
        "293 F. 1013",
        "54 App. D.C. 46",
        "555 P.2d 997"
    ]
    
    print(f"[INFO] Testing {len(test_citations)} citations")
    
    try:
        from src.fast_verification_config import fast_verification
        
        # Test 1: Individual verification
        print("\n" + "-" * 60)
        print("TEST 1: INDIVIDUAL FAST VERIFICATION")
        print("-" * 60)
        
        start = time.time()
        results = []
        for citation in test_citations[:3]:  # Test first 3
            result = asyncio.run(fast_verification.verify_citation_fast(citation))
            results.append(result)
            status = "[VERIFIED]" if result.verified else "[UNVERIFIED]"
            print(f"  {citation}: {status}")
        
        elapsed_individual = time.time() - start
        verified_count = sum(1 for r in results if r.verified)
        print(f"[RESULT] Individual: {elapsed_individual:.2f}s, {verified_count}/{len(results)} verified")
        
        # Test 2: Batch verification
        print("\n" + "-" * 60)
        print("TEST 2: BATCH FAST VERIFICATION")
        print("-" * 60)
        
        start = time.time()
        batch_results = asyncio.run(
            fast_verification.verify_citations_batch_fast(test_citations)
        )
        elapsed_batch = time.time() - start
        
        verified_count = sum(1 for r in batch_results if r.verified)
        print(f"[RESULT] Batch: {elapsed_batch:.2f}s, {verified_count}/{len(batch_results)} verified")
        
        # Show detailed results
        print("\n" + "-" * 60)
        print("DETAILED RESULTS")
        print("-" * 60)
        for result in batch_results:
            status = "[VERIFIED]" if result.verified else "[UNVERIFIED]"
            source = getattr(result, 'verification_source', 'None')
            print(f"  {result.citation}: {status} (source: {source})")
        
        # Performance comparison
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Individual verification: {elapsed_individual:.2f}s for {len(test_citations[:3])} citations")
        print(f"Batch verification:     {elapsed_batch:.2f}s for {len(test_citations)} citations")
        print(f"Average per citation:   {elapsed_batch / len(test_citations):.2f}s")
        
        # Test with actual processing
        print("\n" + "-" * 60)
        print("TEST 3: END-TO-END PROCESSING WITH FAST VERIFICATION")
        print("-" * 60)
        
        test_text = """
        In the case of Smith v. Jones, 87 Wn.3d 577 (2020), the court held that...
        This was followed by Smith v. Jones, 31 Wn.3d 100 (2020), which affirmed...
        The precedent was later cited in Smith v. Jones, 636 F.2d 1267 (2021).
        """
        
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        # Monkey patch the verification to use fast verification
        original_verify = None
        try:
            from src.unified_verification_master import UnifiedVerificationMaster
            original_verify = UnifiedVerificationMaster.verify_citation
            UnifiedVerificationMaster.verify_citation = fast_verification.verify_citation_fast
            UnifiedVerificationMaster.verify_citations_batch = fast_verification.verify_citations_batch_fast
        except Exception as e:
            print(f"[WARNING] Could not patch verification: {e}")
        
        config = ProcessingConfig()
        config.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config=config)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_e2e = time.time() - start
        
        # Restore original method
        if original_verify:
            UnifiedVerificationMaster.verify_citation = original_verify
        
        print(f"[RESULT] End-to-end: {elapsed_e2e:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fast_verification()
