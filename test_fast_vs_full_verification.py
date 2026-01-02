#!/usr/bin/env python3
"""
Compare fast verification (CourtListener + CaseMine) vs full verification
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

def test_verification_comparison():
    """Compare fast vs full verification performance"""
    print("=" * 80)
    print("COMPARING FAST VS FULL VERIFICATION")
    print("=" * 80)
    
    # Test with real citations
    test_citations = [
        "87 Wn.3d 577",
        "31 Wn.3d 100", 
        "636 F.2d 1267"
    ]
    
    print(f"[INFO] Testing {len(test_citations)} citations")
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        from src.fast_verification_config import fast_verification
        
        # Test 1: Fast verification
        print("\n" + "-" * 60)
        print("TEST 1: FAST VERIFICATION (CourtListener + CaseMine)")
        print("-" * 60)
        
        # Monkey patch to use fast verification
        from src.unified_verification_master import UnifiedVerificationMaster
        original_verify = UnifiedVerificationMaster.verify_citation
        original_batch = UnifiedVerificationMaster.verify_citations_batch
        UnifiedVerificationMaster.verify_citation = fast_verification.verify_citation_fast
        UnifiedVerificationMaster.verify_citations_batch = fast_verification.verify_citations_batch_fast
        
        config_fast = ProcessingConfig()
        config_fast.enable_verification = True
        
        processor_fast = UnifiedCitationProcessorV2(config=config_fast)
        
        start = time.time()
        result_fast = asyncio.run(processor_fast.process_text(
            "Test: 87 Wn.3d 577, 31 Wn.3d 100, 636 F.2d 1267"
        ))
        elapsed_fast = time.time() - start
        
        # Restore original methods
        UnifiedVerificationMaster.verify_citation = original_verify
        UnifiedVerificationMaster.verify_citations_batch = original_batch
        
        verified_fast = sum(1 for c in result_fast.get('citations', []) if getattr(c, 'verified', False))
        print(f"[RESULT] Fast: {elapsed_fast:.2f}s, {verified_fast} verified")
        
        # Test 2: Full verification
        print("\n" + "-" * 60)
        print("TEST 2: FULL VERIFICATION (ALL SOURCES)")
        print("-" * 60)
        
        config_full = ProcessingConfig()
        config_full.enable_verification = True
        
        processor_full = UnifiedCitationProcessorV2(config=config_full)
        
        start = time.time()
        result_full = asyncio.run(processor_full.process_text(
            "Test: 87 Wn.3d 577, 31 Wn.3d 100, 636 F.2d 1267"
        ))
        elapsed_full = time.time() - start
        
        verified_full = sum(1 for c in result_full.get('citations', []) if getattr(c, 'verified', False))
        print(f"[RESULT] Full: {elapsed_full:.2f}s, {verified_full} verified")
        
        # Test 3: No verification
        print("\n" + "-" * 60)
        print("TEST 3: NO VERIFICATION (BASELINE)")
        print("-" * 60)
        
        config_none = ProcessingConfig()
        config_none.enable_verification = False
        
        processor_none = UnifiedCitationProcessorV2(config=config_none)
        
        start = time.time()
        result_none = asyncio.run(processor_none.process_text(
            "Test: 87 Wn.3d 577, 31 Wn.3d 100, 636 F.2d 1267"
        ))
        elapsed_none = time.time() - start
        
        print(f"[RESULT] None: {elapsed_none:.2f}s")
        
        # Performance comparison
        print("\n" + "=" * 60)
        print("PERFORMANCE COMPARISON")
        print("=" * 60)
        print(f"No verification:    {elapsed_none:.2f}s (baseline)")
        print(f"Fast verification:  {elapsed_fast:.2f}s ({elapsed_fast/elapsed_none:.1f}x slower)")
        print(f"Full verification:  {elapsed_full:.2f}s ({elapsed_full/elapsed_none:.1f}x slower)")
        print(f"Speedup (Fast vs Full): {elapsed_full/elapsed_fast:.1f}x")
        
        # Show verification results
        print("\n" + "-" * 60)
        print("VERIFICATION RESULTS")
        print("-" * 60)
        print(f"Fast verification:  {verified_fast}/{len(result_fast.get('citations', []))} citations verified")
        print(f"Full verification:  {verified_full}/{len(result_full.get('citations', []))} citations verified")
        
        # Recommendation
        print("\n" + "=" * 60)
        print("RECOMMENDATION")
        print("=" * 60)
        if elapsed_fast < 5 * elapsed_none:
            print("✅ Fast verification is acceptable for production use")
            print("   - Provides verification with minimal performance impact")
            print("   - Uses CourtListener lookup + CaseMine sources")
        else:
            print("⚠️  Fast verification may be too slow for production")
            print("   - Consider disabling verification for better performance")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification_comparison()
