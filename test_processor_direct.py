#!/usr/bin/env python3
"""
Direct test of the processor to see what's taking so long
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_processor_direct():
    """Test the processor directly"""
    print("🔍 Direct Processor Test")
    print("=" * 40)
    
    # Test text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"Text length: {len(test_text)} characters")
    print(f"Word count: {len(test_text.split())} words")
    
    # Test with fast config (no verification)
    print("\nTesting with fast config (no verification)...")
    fast_config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=False,  # Disable verification for speed
        debug_mode=False,
        min_confidence=0.0
    )
    
    start_time = time.time()
    try:
        processor = UnifiedCitationProcessorV2(fast_config)
        results = processor.process_text(test_text)
        processing_time = time.time() - start_time
        
        print(f"✅ Fast processing completed in {processing_time:.2f} seconds")
        print(f"Found {len(results)} citations")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.citation} -> {result.extracted_case_name} ({result.extracted_date})")
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Fast processing failed after {processing_time:.2f} seconds: {e}")
    
    print("\n" + "="*50)
    
    # Test with minimal config
    print("Testing with minimal config...")
    minimal_config = ProcessingConfig(
        use_eyecite=False,  # Disable eyecite
        use_regex=True,     # Only use regex
        extract_case_names=False,  # Disable case name extraction
        extract_dates=False,       # Disable date extraction
        enable_clustering=False,   # Disable clustering
        enable_deduplication=False, # Disable deduplication
        enable_verification=False,  # Disable verification
        debug_mode=False,
        min_confidence=0.0
    )
    
    start_time = time.time()
    try:
        processor = UnifiedCitationProcessorV2(minimal_config)
        results = processor.process_text(test_text)
        processing_time = time.time() - start_time
        
        print(f"✅ Minimal processing completed in {processing_time:.2f} seconds")
        print(f"Found {len(results)} citations")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.citation}")
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Minimal processing failed after {processing_time:.2f} seconds: {e}")

if __name__ == "__main__":
    test_processor_direct() 