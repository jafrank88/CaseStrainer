#!/usr/bin/env python3
"""
Test fast verification with only CourtListener lookup and CaseMine
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from src.unified_verification_master import VerificationResult
import logging
logger = logging.getLogger(__name__)

def test_fast_verification():
    """Test fast verification with only CourtListener lookup and CaseMine"""
    print("=" * 80)
    print("TESTING FAST VERIFICATION (CourtListener Lookup + CaseMine)")
    print("=" * 80)
    
    # Test with a simple text sample
    test_text = """
    In the case of Smith v. Jones, 123 U.S. 456 (2020), the court held that...
    This was followed by Smith v. Jones, 456 F.2d 789 (2020), which affirmed...
    The precedent was later cited in Smith v. Jones, 789 F.3d 123 (2021).
    """
    
    print(f"[INFO] Testing with {len(test_text)} characters of text")
    
    try:
        import asyncio
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        # Test 1: No verification (baseline)
        print("\n" + "-" * 60)
        print("TEST 1: NO VERIFICATION (BASELINE)")
        print("-" * 60)
        
        config_none = ProcessingConfig()
        config_none.enable_verification = False
        
        processor = UnifiedCitationProcessorV2(config=config_none)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_none = time.time() - start
        
        print(f"[RESULT] No verification: {elapsed_none:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
        # Test 2: Fast verification (CourtListener lookup + CaseMine only)
        print("\n" + "-" * 60)
        print("TEST 2: FAST VERIFICATION (CourtListener Lookup + CaseMine)")
        print("-" * 60)
        
        # Temporarily modify the verification sources to use only fast ones
        from src.unified_verification_master import UnifiedVerificationMaster
        
        # Create a custom verification master with only fast sources
        class FastVerificationMaster(UnifiedVerificationMaster):
            async def verify_citation_fast(self, citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str], timeout: float) -> VerificationResult:
                """Fast verification using only CourtListener lookup and CaseMine"""
                
                # Try CourtListener lookup first (fastest)
                try:
                    result = await self._verify_with_courtlistener_lookup(citation, extracted_case_name, extracted_date)
                    if result.verified:
                        return result
                except Exception as e:
                    logger.warning(f" CourtListener lookup failed: {e}")
                
                # Try CaseMine second
                try:
                    result = await self._verify_with_casemine(citation, extracted_case_name, extracted_date, min(timeout, 12.0))
                    if result.verified or getattr(result, 'possible_match', False):
                        return result
                except Exception as e:
                    logger.warning(f" CaseMine failed: {e}")
                
                return VerificationResult(citation=citation, verified=False, error="Fast verification failed")
        
        # Monkey patch the verification method
        original_verify = UnifiedVerificationMaster.verify_citation
        UnifiedVerificationMaster.verify_citation = FastVerificationMaster.verify_citation_fast
        
        config_fast = ProcessingConfig()
        config_fast.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config=config_fast)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_fast = time.time() - start
        
        # Restore original method
        UnifiedVerificationMaster.verify_citation = original_verify
        
        print(f"[RESULT] Fast verification: {elapsed_fast:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
        # Test 3: Full verification (for comparison)
        print("\n" + "-" * 60)
        print("TEST 3: FULL VERIFICATION (ALL SOURCES)")
        print("-" * 60)
        
        config_full = ProcessingConfig()
        config_full.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config=config_full)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_full = time.time() - start
        
        print(f"[RESULT] Full verification: {elapsed_full:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
        # Calculate comparison
        print("\n" + "=" * 60)
        print("PERFORMANCE COMPARISON")
        print("=" * 60)
        print(f"No verification:      {elapsed_none:.2f}s")
        print(f"Fast verification:    {elapsed_fast:.2f}s")
        print(f"Full verification:    {elapsed_full:.2f}s")
        print(f"Fast vs None:         {elapsed_fast / elapsed_none:.1f}x slower")
        print(f"Full vs Fast:         {elapsed_full / elapsed_fast:.1f}x slower")
        print(f"Full vs None:         {elapsed_full / elapsed_none:.1f}x slower")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fast_verification()
