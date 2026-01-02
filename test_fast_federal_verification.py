#!/usr/bin/env python3
"""
Test fast verification for Federal citations (includes Law.Resource.org)
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

def test_fast_federal_verification():
    """Test fast verification with Law.Resource.org for Federal citations"""
    print("=" * 80)
    print("TESTING FAST FEDERAL VERIFICATION (CourtListener + CaseMine + Law.Resource.org)")
    print("=" * 80)
    
    # Test with Federal citations
    federal_citations = [
        "636 F.2d 1267",      # Federal Reporter, 2d series
        "293 F. 1013",        # Federal Reporter
        "87 Wn.3d 577",       # State reporter (should not use Law.Resource.org)
        "31 Wn.3d 100",       # State reporter (should not use Law.Resource.org)
        "548 P.3d 226",       # Pacific Reporter (should not use Law.Resource.org)
    ]
    
    print(f"[INFO] Testing {len(federal_citations)} citations")
    print(f"[INFO] Federal citations: {[c for c in federal_citations if 'F.' in c]}")
    print(f"[INFO] State citations: {[c for c in federal_citations if 'F.' not in c]}")
    
    try:
        from src.fast_verification_federal_config import fast_federal_verification
        
        # Test 1: Check Federal citation detection
        print("\n" + "-" * 60)
        print("TEST 1: FEDERAL CITATION DETECTION")
        print("-" * 60)
        
        for citation in federal_citations:
            is_federal = fast_federal_verification.is_federal_citation(citation)
            print(f"  {citation}: {'Federal' if is_federal else 'State'} citation")
        
        # Test 2: Individual verification
        print("\n" + "-" * 60)
        print("TEST 2: INDIVIDUAL FAST VERIFICATION")
        print("-" * 60)
        
        start = time.time()
        results = []
        for citation in federal_citations:
            result = asyncio.run(fast_federal_verification.verify_citation_fast(citation))
            results.append(result)
            status = "[VERIFIED]" if result.verified else "[UNVERIFIED]"
            source = getattr(result, 'verification_source', 'None')
            print(f"  {citation}: {status} (source: {source})")
        
        elapsed_individual = time.time() - start
        verified_count = sum(1 for r in results if r.verified)
        print(f"[RESULT] Individual: {elapsed_individual:.2f}s, {verified_count}/{len(results)} verified")
        
        # Test 3: Batch verification
        print("\n" + "-" * 60)
        print("TEST 3: BATCH FAST VERIFICATION")
        print("-" * 60)
        
        start = time.time()
        batch_results = asyncio.run(
            fast_federal_verification.verify_citations_batch_fast(federal_citations)
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
            is_federal = fast_federal_verification.is_federal_citation(result.citation)
            print(f"  {result.citation}: {status} (source: {source}, type: {'Federal' if is_federal else 'State'})")
        
        # Test 4: End-to-end processing
        print("\n" + "-" * 60)
        print("TEST 4: END-TO-END PROCESSING WITH FAST FEDERAL VERIFICATION")
        print("-" * 60)
        
        test_text = """
        In the case of Smith v. Jones, 636 F.2d 1267 (1980), the court held that...
        This was followed by Smith v. Jones, 293 F. 1013 (1981), which affirmed...
        The state precedent was Smith v. Jones, 87 Wn.3d 577 (2020).
        """
        
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        # Monkey patch the verification to use fast federal verification
        from src.unified_verification_master import UnifiedVerificationMaster
        original_verify = UnifiedVerificationMaster.verify_citation
        original_batch = UnifiedVerificationMaster.verify_citations_batch
        UnifiedVerificationMaster.verify_citation = fast_federal_verification.verify_citation_fast
        UnifiedVerificationMaster.verify_citations_batch = fast_federal_verification.verify_citations_batch_fast
        
        config = ProcessingConfig()
        config.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config=config)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_e2e = time.time() - start
        
        # Restore original methods
        UnifiedVerificationMaster.verify_citation = original_verify
        UnifiedVerificationMaster.verify_citations_batch = original_batch
        
        print(f"[RESULT] End-to-end: {elapsed_e2e:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
        # Show which citations were verified
        citations = result.get('citations', [])
        for cit in citations:
            cit_text = getattr(cit, 'citation', 'Unknown')
            verified = getattr(cit, 'verified', False)
            source = getattr(cit, 'verification_source', 'None')
            status = "[VERIFIED]" if verified else "[UNVERIFIED]"
            print(f"  {cit_text}: {status} (source: {source})")
        
        # Performance summary
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Individual verification: {elapsed_individual:.2f}s for {len(federal_citations)} citations")
        print(f"Batch verification:     {elapsed_batch:.2f}s for {len(federal_citations)} citations")
        print(f"End-to-end processing:  {elapsed_e2e:.2f}s for 3 citations")
        print(f"Average per citation:   {elapsed_batch / len(federal_citations):.2f}s")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fast_federal_verification()
