#!/usr/bin/env python3
"""
Test Washington citations from the standard test text
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_washington_citations():
    """Test the Washington citations from the standard test text"""
    
    print("=== Testing Washington Citations ===")
    
    # Test citations from the standard test text
    test_citations = [
        "200 Wn.2d 72",
        "514 P.3d 643", 
        "171 Wn.2d 486",
        "256 P.3d 321",
        "146 Wn.2d 1",
        "43 P.3d 4"
    ]
    
    # Create processor with verification enabled
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        debug_mode=True,
        min_confidence=0.0
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    for citation in test_citations:
        print(f"\n--- Testing: {citation} ---")
        
        try:
            results = processor.process_text(citation)
            print(f"Results: {len(results)}")
            
            for i, result in enumerate(results):
                print(f"  Result {i+1}:")
                print(f"    Citation: {result.citation}")
                print(f"    Extracted case name: {result.extracted_case_name}")
                print(f"    Extracted date: {result.extracted_date}")
                print(f"    Canonical name: {result.canonical_name}")
                print(f"    Canonical date: {result.canonical_date}")
                print(f"    Verified: {result.verified}")
                print(f"    URL: {result.url}")
                print(f"    Method: {result.method}")
                print(f"    Error: {result.error}")
                
                # Check metadata for verification details
                if result.metadata:
                    print(f"    Metadata keys: {list(result.metadata.keys())}")
                    if 'fallback_source' in result.metadata:
                        print(f"    Fallback source: {result.metadata['fallback_source']}")
                    if 'canonical_service_result' in result.metadata:
                        print(f"    Canonical service result: {result.metadata['canonical_service_result']}")
                        
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == '__main__':
    test_washington_citations() 