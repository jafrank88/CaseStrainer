#!/usr/bin/env python3
"""
Test script to check if ProcessingConfig is working correctly.
"""

print("🚀 Script starting...")

import sys
import os

print("🚀 Imports completed")

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🚀 Added src to path")

try:
    print("🚀 Attempting to import...")
    from unified_citation_processor_v2 import ProcessingConfig, UnifiedCitationProcessorV2
    print("✅ Successfully imported ProcessingConfig and UnifiedCitationProcessorV2")
    
    # Test creating a config with verification enabled
    config = ProcessingConfig(
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
    
    print(f"✅ Created config with enable_verification: {config.enable_verification}")
    print(f"✅ Config type: {type(config)}")
    print(f"✅ Config repr: {repr(config)}")
    
    # Test creating a processor with this config
    processor = UnifiedCitationProcessorV2(config)
    print(f"✅ Created processor with config enable_verification: {processor.config.enable_verification}")
    print(f"✅ Processor config type: {type(processor.config)}")
    print(f"✅ Processor config repr: {repr(processor.config)}")
    
    # Test processing a simple citation
    test_text = "534 F.3d 1290"
    print(f"✅ Testing with text: '{test_text}'")
    
    results = processor.process_text(test_text)
    print(f"✅ Processing completed, got {len(results)} results")
    
    for i, result in enumerate(results):
        print(f"✅ Result {i}: {result.citation} -> verified={result.verified}, canonical_name={result.canonical_name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("🚀 Script ending...") 