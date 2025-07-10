#!/usr/bin/env python3
"""
Test script to verify CourtListener API key in UnifiedCitationProcessor
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    print("✅ Successfully imported UnifiedCitationProcessor")
    
    # Create processor instance
    processor = UnifiedCitationProcessor()
    print("✅ Successfully created UnifiedCitationProcessor instance")
    
    # Check if API key is accessible
    if hasattr(processor, 'api_key'):
        print(f"Processor API key: {processor.api_key}")
        print(f"API key length: {len(processor.api_key) if processor.api_key else 0}")
        
        if processor.api_key and processor.api_key.startswith("443a"):
            print("✅ Processor API key starts with expected prefix '443a'")
        else:
            print("❌ Processor API key does not start with expected prefix '443a'")
    else:
        print("❌ Processor does not have api_key attribute")
    
    # Check if courtlistener_api_key is accessible (used in verification)
    if hasattr(processor, 'courtlistener_api_key'):
        print(f"Processor courtlistener_api_key: {processor.courtlistener_api_key}")
        if processor.courtlistener_api_key and processor.courtlistener_api_key.startswith("443a"):
            print("✅ Processor courtlistener_api_key starts with expected prefix '443a'")
        else:
            print("❌ Processor courtlistener_api_key does not start with expected prefix '443a'")
    else:
        print("❌ Processor does not have courtlistener_api_key attribute")
        
except ImportError as e:
    print(f"❌ Failed to import UnifiedCitationProcessor: {e}")
except Exception as e:
    print(f"❌ Error during testing: {e}") 