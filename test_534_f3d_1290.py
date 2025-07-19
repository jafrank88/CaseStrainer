#!/usr/bin/env python3
"""
Test the specific citation that's causing the hang: 534 F.3d 1290
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_534_f3d_1290():
    """Test the specific citation that's hanging"""
    
    print("=== Testing 534 F.3d 1290 ===")
    
    # Create processor with verification enabled
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        context_window=300,
        min_confidence=0.0,
        max_citations_per_text=1000,
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    # Test the specific citation
    test_text = "534 F.3d 1290"
    
    print(f"Testing citation: {test_text}")
    print(f"Processor config: {config}")
    print(f"Verification enabled: {config.enable_verification}")
    
    start_time = time.time()
    
    try:
        # Process with timeout
        result = processor.process_text(test_text)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Processing completed in {processing_time:.2f} seconds")
        print(f"Result type: {type(result)}")
        
        if isinstance(result, list):
            citations = result
        else:
            citations = result.citations if hasattr(result, 'citations') else []
            
        print(f"Citations found: {len(citations)}")
        
        for i, citation in enumerate(citations):
            print(f"  Citation {i+1}: {citation.citation}")
            print(f"    Verified: {citation.verified}")
            print(f"    Source: {citation.source}")
            print(f"    Canonical name: {citation.canonical_name}")
            print(f"    Canonical date: {citation.canonical_date}")
            print()
            
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"❌ Processing failed after {processing_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_534_f3d_1290() 