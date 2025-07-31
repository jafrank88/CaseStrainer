#!/usr/bin/env python3
"""
Debug the fallback verification pipeline to see why it's not working in production
"""

import sys
import os
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_processor_with_debug():
    """Test the unified citation processor with debug logging to see fallback issues"""
    
    print("DEBUGGING UNIFIED CITATION PROCESSOR FALLBACK PIPELINE")
    print("=" * 70)
    
    try:
        # Import the unified citation processor
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        print("SUCCESS: Imported UnifiedCitationProcessorV2")
        
        # Create processor with debug mode enabled
        config = ProcessingConfig()
        config.debug_mode = True
        config.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config)
        print("SUCCESS: Created processor with debug mode enabled")
        
        # Test with a citation that should trigger fallback
        test_text = "In State v. Arndt (2019), the court cited 194 Wn. 2d 784."
        
        print(f"\nProcessing test text: {test_text}")
        print("-" * 50)
        
        # Process the text and capture all logging
        result = processor.process_text(test_text)
        
        print(f"\nRESULTS:")
        print(f"Citations found: {len(result)}")
        
        for i, citation in enumerate(result):
            print(f"\nCitation {i+1}:")
            print(f"  Text: {citation.citation}")
            print(f"  Verified: {citation.verified}")
            print(f"  Source: {getattr(citation, 'source', 'N/A')}")
            print(f"  Canonical name: {getattr(citation, 'canonical_name', 'N/A')}")
            print(f"  Canonical date: {getattr(citation, 'canonical_date', 'N/A')}")
            print(f"  Extracted case name: {getattr(citation, 'extracted_case_name', 'N/A')}")
            print(f"  Extracted date: {getattr(citation, 'extracted_date', 'N/A')}")
            
            # Check metadata for fallback info
            metadata = getattr(citation, 'metadata', {})
            if metadata:
                verification_method = metadata.get('verification_method', 'N/A')
                fallback_source = metadata.get('fallback_source', 'N/A')
                print(f"  Verification method: {verification_method}")
                print(f"  Fallback source: {fallback_source}")
        
        # Check if any citations were verified by fallback
        fallback_verified = [c for c in result if getattr(c, 'source', '') and 
                           ('Cornell' in getattr(c, 'source', '') or 
                            'Justia' in getattr(c, 'source', '') or
                            'fallback' in getattr(c, 'source', '').lower())]
        
        print(f"\nFALLBACK ANALYSIS:")
        print(f"Total citations: {len(result)}")
        print(f"Verified citations: {sum(1 for c in result if c.verified)}")
        print(f"Fallback verified: {len(fallback_verified)}")
        
        if len(fallback_verified) > 0:
            print("SUCCESS: Fallback verification is working!")
            return True
        else:
            print("ISSUE: No fallback verification detected")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception in unified processor test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_fallback_call():
    """Test calling the fallback verifier directly with the same parameters the processor would use"""
    
    print(f"\n{'='*70}")
    print("TESTING DIRECT FALLBACK VERIFIER CALL")
    print(f"{'='*70}")
    
    try:
        from src.fallback_verifier import FallbackVerifier
        
        verifier = FallbackVerifier()
        print("SUCCESS: Created FallbackVerifier instance")
        
        # Test with the same parameters the processor would use
        citation_text = "194 Wn. 2d 784"
        extracted_case_name = "State v. Arndt"
        extracted_date = "2019"
        
        print(f"Testing with:")
        print(f"  Citation: {citation_text}")
        print(f"  Case name: {extracted_case_name}")
        print(f"  Date: {extracted_date}")
        
        result = verifier.verify_citation(citation_text, extracted_case_name, extracted_date)
        
        print(f"\nFallback verifier result:")
        print(f"  Verified: {result.get('verified', False)}")
        print(f"  Source: {result.get('source', 'N/A')}")
        print(f"  Canonical name: {result.get('canonical_name', 'N/A')}")
        print(f"  Canonical date: {result.get('canonical_date', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0.0)}")
        print(f"  URL: {result.get('url', 'N/A')}")
        
        if result.get('verified'):
            print("SUCCESS: Direct fallback verifier call works!")
            return True
        else:
            print("ISSUE: Direct fallback verifier call failed")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception in direct fallback test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("COMPREHENSIVE FALLBACK VERIFICATION DEBUG")
    print("=" * 70)
    
    # Test 1: Direct fallback verifier
    direct_success = test_direct_fallback_call()
    
    # Test 2: Through unified processor
    processor_success = test_unified_processor_with_debug()
    
    print(f"\n{'='*70}")
    print("DEBUG SUMMARY")
    print(f"{'='*70}")
    print(f"Direct fallback verifier: {'SUCCESS' if direct_success else 'FAILED'}")
    print(f"Unified processor fallback: {'SUCCESS' if processor_success else 'FAILED'}")
    
    if direct_success and not processor_success:
        print("\nCONCLUSION: Fallback verifier works but unified processor isn't calling it properly")
    elif not direct_success:
        print("\nCONCLUSION: Fallback verifier itself still has issues")
    else:
        print("\nCONCLUSION: Both tests passed - fallback should be working")
