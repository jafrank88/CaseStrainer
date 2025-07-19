#!/usr/bin/env python3
"""
Debug script to check processor configuration and verification
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.services.citation_service import CitationService
from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def debug_processor():
    """Debug the processor configuration"""
    
    print("=== Debugging Processor Configuration ===")
    
    # Create service
    service = CitationService()
    
    print(f"\n1. Service processor type: {type(service.processor)}")
    print(f"   Processor: {service.processor}")
    
    if hasattr(service.processor, 'config'):
        print(f"   Has config: Yes")
        print(f"   Config: {service.processor.config}")
    else:
        print(f"   Has config: No")
    
    # Test with a simple citation that should be verifiable
    test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)"
    
    print(f"\n2. Testing with simple citation: {test_text}")
    
    # Test the fast processor directly
    fast_config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        debug_mode=True,  # Enable debug mode
        min_confidence=0.0
    )
    
    print(f"\n3. Creating fast processor with config:")
    print(f"   enable_verification: {fast_config.enable_verification}")
    print(f"   debug_mode: {fast_config.debug_mode}")
    
    fast_processor = UnifiedCitationProcessorV2(fast_config)
    
    print(f"\n4. Fast processor created:")
    print(f"   Type: {type(fast_processor)}")
    print(f"   Config enable_verification: {fast_processor.config.enable_verification}")
    
    print(f"\n5. Processing text with fast processor:")
    try:
        results = fast_processor.process_text(test_text)
        print(f"   Results type: {type(results)}")
        print(f"   Number of results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}:")
            print(f"     Citation: {result.citation}")
            print(f"     Extracted case name: {result.extracted_case_name}")
            print(f"     Extracted date: {result.extracted_date}")
            print(f"     Canonical name: {result.canonical_name}")
            print(f"     Canonical date: {result.canonical_date}")
            print(f"     Verified: {result.verified}")
            print(f"     URL: {result.url}")
            print(f"     Method: {result.method}")
            
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_processor() 