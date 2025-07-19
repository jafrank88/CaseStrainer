#!/usr/bin/env python3
"""
Test script to verify sync vs async processing and verification settings
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.services.citation_service import CitationService
from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_sync_vs_async():
    """Test the difference between sync and async processing"""
    
    print("=== Testing Sync vs Async Processing ===")
    
    # Test text
    test_text = "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    
    # Create service
    service = CitationService()
    
    print(f"\n1. Testing should_process_immediately:")
    should_immediate = service.should_process_immediately({'type': 'text', 'text': test_text})
    print(f"   Should process immediately: {should_immediate}")
    
    print(f"\n2. Testing sync processing (process_immediately):")
    try:
        sync_result = service.process_immediately({'type': 'text', 'text': test_text})
        print(f"   Status: {sync_result.get('status')}")
        print(f"   Citations found: {len(sync_result.get('citations', []))}")
        
        # Check for canonical names
        canonical_names = [c.get('canonical_name') for c in sync_result.get('citations', []) if c.get('canonical_name')]
        print(f"   Canonical names found: {len(canonical_names)}")
        for name in canonical_names:
            print(f"     - {name}")
            
    except Exception as e:
        print(f"   Error in sync processing: {e}")
    
    print(f"\n3. Testing async processing (process_citation_task):")
    try:
        async_result = service.process_citation_task('test-task', 'text', {'text': test_text})
        print(f"   Status: {async_result.get('status')}")
        print(f"   Citations found: {len(async_result.get('citations', []))}")
        
        # Check for canonical names
        canonical_names = [c.get('canonical_name') for c in async_result.get('citations', []) if c.get('canonical_name')]
        print(f"   Canonical names found: {len(canonical_names)}")
        for name in canonical_names:
            print(f"     - {name}")
            
    except Exception as e:
        print(f"   Error in async processing: {e}")
    
    print(f"\n4. Testing processor config directly:")
    try:
        # Check the main processor config
        if hasattr(service.processor, 'config'):
            print(f"   Main processor enable_verification: {service.processor.config.enable_verification}")
        else:
            print(f"   Main processor has no config attribute")
            
        # Create a new processor like in process_immediately
        fast_config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            enable_verification=True,
            debug_mode=False,
            min_confidence=0.0
        )
        fast_processor = UnifiedCitationProcessorV2(fast_config)
        print(f"   Fast processor enable_verification: {fast_processor.config.enable_verification}")
        
        # Test the fast processor directly
        fast_results = fast_processor.process_text(test_text)
        print(f"   Fast processor citations found: {len(fast_results)}")
        canonical_names = [r.canonical_name for r in fast_results if r.canonical_name]
        print(f"   Fast processor canonical names: {len(canonical_names)}")
        for name in canonical_names:
            print(f"     - {name}")
            
    except Exception as e:
        print(f"   Error testing processor config: {e}")

if __name__ == '__main__':
    test_sync_vs_async() 