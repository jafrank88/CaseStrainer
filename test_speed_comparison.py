#!/usr/bin/env python3
"""
Test processing speed with and without verification
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_processing_speed():
    """Test processing speed with and without verification"""
    print("=" * 80)
    print("TESTING PROCESSING SPEED WITH/WITHOUT VERIFICATION")
    print("=" * 80)
    
    # Test with a simple text sample first
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
        
        # Test 1: WITH verification (current default)
        print("\n" + "-" * 60)
        print("TEST 1: WITH VERIFICATION")
        print("-" * 60)
        
        config_with = ProcessingConfig()
        config_with.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config=config_with)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_with = time.time() - start
        
        print(f"[RESULT] WITH verification: {elapsed_with:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
        # Test 2: WITHOUT verification
        print("\n" + "-" * 60)
        print("TEST 2: WITHOUT VERIFICATION")
        print("-" * 60)
        
        config_without = ProcessingConfig()
        config_without.enable_verification = False
        
        processor = UnifiedCitationProcessorV2(config=config_without)
        
        start = time.time()
        result = asyncio.run(processor.process_text(test_text))
        elapsed_without = time.time() - start
        
        print(f"[RESULT] WITHOUT verification: {elapsed_without:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
        # Calculate difference
        print("\n" + "=" * 60)
        print("PERFORMANCE COMPARISON")
        print("=" * 60)
        print(f"WITH verification:    {elapsed_with:.2f}s")
        print(f"WITHOUT verification: {elapsed_without:.2f}s")
        print(f"Difference:           {elapsed_with - elapsed_without:.2f}s")
        if elapsed_without > 0:
            print(f"Speedup:              {elapsed_with / elapsed_without:.1f}x")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_processing_speed()
