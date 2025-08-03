#!/usr/bin/env python3
"""
Direct test of fallback verification to debug why it's not working in production
"""

import sys
import os
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fallback_verifier_directly():
    """Test the fallback verifier directly to see if it works"""
    
    print("TESTING FALLBACK VERIFIER DIRECTLY")
    print("=" * 50)
    
    try:
        # Import the fallback verifier
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.fallback_verifier import FallbackVerifier
        
        print("✅ Successfully imported FallbackVerifier")
        
        # Create verifier instance
        verifier = FallbackVerifier()
        print("✅ Successfully created FallbackVerifier instance")
        
        # Test with known Washington state citations that should be verifiable
        test_cases = [
            {
                'citation': '194 Wn. 2d 784',
                'case_name': 'State v. Arndt',
                'date': '2019'
            },
            {
                'citation': '69 P.3d 594',
                'case_name': 'State ex rel. Carroll v. Junker',
                'date': '2003'
            },
            {
                'citation': '453 P.3d 696',
                'case_name': 'State v. Armenta',
                'date': '2019'
            }
        ]
        
        print(f"\nTesting {len(test_cases)} citations with fallback verifier...")
        
        for i, test_case in enumerate(test_cases):
            citation = test_case['citation']
            case_name = test_case['case_name']
            date = test_case['date']
            
            print(f"\n[{i+1}/{len(test_cases)}] Testing: {citation}")
            print(f"  Expected case: {case_name}")
            print(f"  Expected date: {date}")
            
            try:
                result = verifier.verify_citation(citation, case_name, date)
                
                print(f"  Result: {result}")
                
                if result.get('verified'):
                    print(f"  ✅ VERIFIED via {result.get('source', 'unknown')}")
                    print(f"  Canonical name: {result.get('canonical_name', 'N/A')}")
                    print(f"  Canonical date: {result.get('canonical_date', 'N/A')}")
                    print(f"  URL: {result.get('url', 'N/A')}")
                else:
                    print(f"  ❌ NOT VERIFIED")
                    print(f"  Error: {result.get('error', 'No error message')}")
                    
            except Exception as e:
                print(f"  ❌ EXCEPTION: {str(e)}")
                import traceback
                print(f"  Traceback: {traceback.format_exc()}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import FallbackVerifier: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing fallback verifier: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_unified_processor_fallback():
    """Test fallback verification through the unified citation processor"""
    
    print(f"\n{'='*60}")
    print("TESTING FALLBACK THROUGH UNIFIED CITATION PROCESSOR")
    print(f"{'='*60}")
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        print("✅ Successfully imported UnifiedCitationProcessorV2")
        
        # Create processor with debug mode enabled
        config = ProcessingConfig()
        config.debug_mode = True
        config.enable_verification = True
        
        processor = UnifiedCitationProcessorV2(config)
        print("✅ Successfully created processor with debug mode")
        
        # Test with text containing unverifiable citations
        test_text = """
        In State v. Arndt, 194 Wn. 2d 784, 453 P.3d 696 (2019), the court held that...
        The case of State ex rel. Carroll v. Junker, 69 P.3d 594 (2003), established...
        """
        
        print(f"\nProcessing test text with citations...")
        print(f"Text: {test_text.strip()}")
        
        # Process the text
        result = processor.process_text(test_text)
        
        print(f"\nExtraction results:")
        print(f"  Citations found: {len(result)}")
        
        for i, citation in enumerate(result):
            print(f"\n  [{i+1}] {citation.citation}")
            print(f"      Verified: {citation.verified}")
            print(f"      Source: {getattr(citation, 'source', 'N/A')}")
            print(f"      Canonical name: {getattr(citation, 'canonical_name', 'N/A')}")
            print(f"      Canonical date: {getattr(citation, 'canonical_date', 'N/A')}")
            
            # Check if fallback was attempted
            metadata = getattr(citation, 'metadata', {})
            if metadata:
                verification_method = metadata.get('verification_method', 'N/A')
                fallback_source = metadata.get('fallback_source', 'N/A')
                print(f"      Verification method: {verification_method}")
                print(f"      Fallback source: {fallback_source}")
        
        # Count verification results
        verified_count = sum(1 for c in result if c.verified)
        fallback_count = sum(1 for c in result if getattr(c, 'source', '').startswith('Cornell') or getattr(c, 'source', '').startswith('Justia'))
        
        print(f"\nVerification Summary:")
        print(f"  Total citations: {len(result)}")
        print(f"  Verified: {verified_count}")
        print(f"  Fallback verified: {fallback_count}")
        
        if fallback_count == 0 and verified_count < len(result):
            print(f"  ❌ ISSUE: No fallback verification occurred for unverified citations")
            return False
        else:
            print(f"  ✅ Fallback verification appears to be working")
            return True
        
    except Exception as e:
        print(f"❌ Error testing unified processor: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("DEBUGGING FALLBACK VERIFICATION PIPELINE")
    print("=" * 60)
    
    # Test 1: Direct fallback verifier
    direct_success = test_fallback_verifier_directly()
    
    # Test 2: Through unified processor
    processor_success = test_unified_processor_fallback()
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Direct fallback verifier test: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    print(f"Unified processor fallback test: {'✅ PASSED' if processor_success else '❌ FAILED'}")
    
    if not direct_success:
        print(f"\n❌ CRITICAL: Fallback verifier itself is broken")
    elif not processor_success:
        print(f"\n❌ CRITICAL: Fallback verifier works but is not being called by unified processor")
    else:
        print(f"\n✅ Both tests passed - fallback verification should be working")
