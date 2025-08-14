#!/usr/bin/env python3
"""
Debug extraction at each step of the unified pipeline
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_processor_steps():
    """Test each step of the unified processor pipeline"""
    print("=" * 60)
    print("TESTING UNIFIED PROCESSOR PIPELINE STEPS")
    print("=" * 60)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    print(f"Test text: {test_text}")
    
    try:
        # Import and initialize
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        
        config = ProcessingConfig()
        config.enable_verification = False
        config.debug_mode = True
        
        processor = UnifiedCitationProcessorV2(config=config)
        print("✓ Processor initialized")
        
        # Test Step 1: Enhanced regex extraction
        print("\n1. Testing _extract_with_regex_enhanced...")
        try:
            regex_citations = processor._extract_with_regex_enhanced(test_text)
            print(f"✓ Regex enhanced found {len(regex_citations)} citations")
            for i, citation in enumerate(regex_citations):
                print(f"  Citation {i+1}: {citation.citation}")
        except Exception as e:
            print(f"✗ Regex enhanced failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Step 2: Eyecite extraction
        print("\n2. Testing _extract_with_eyecite...")
        try:
            eyecite_citations = processor._extract_with_eyecite(test_text)
            print(f"✓ Eyecite found {len(eyecite_citations)} citations")
            for i, citation in enumerate(eyecite_citations):
                print(f"  Citation {i+1}: {citation.citation}")
        except Exception as e:
            print(f"✗ Eyecite failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Step 3: Unified extraction
        print("\n3. Testing _extract_citations_unified...")
        try:
            unified_citations = processor._extract_citations_unified(test_text)
            print(f"✓ Unified extraction found {len(unified_citations)} citations")
            for i, citation in enumerate(unified_citations):
                print(f"  Citation {i+1}: {citation.citation}")
        except Exception as e:
            print(f"✗ Unified extraction failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Step 4: Full process_text pipeline
        print("\n4. Testing full process_text pipeline...")
        try:
            result = asyncio.run(processor.process_text(test_text))
            print(f"✓ Full pipeline found {len(result.get('citations', []))} citations")
            print(f"✓ Full pipeline found {len(result.get('clusters', []))} clusters")
            
            for i, citation in enumerate(result.get('citations', [])):
                if hasattr(citation, 'citation'):
                    print(f"  Citation {i+1}: {citation.citation}")
                else:
                    print(f"  Citation {i+1}: {citation}")
                    
        except Exception as e:
            print(f"✗ Full pipeline failed: {e}")
            import traceback
            traceback.print_exc()
        
        return len(result.get('citations', [])) > 0 if 'result' in locals() else False
        
    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_eyecite_availability():
    """Test if eyecite is properly available"""
    print("\n" + "=" * 60)
    print("TESTING EYECITE AVAILABILITY")
    print("=" * 60)
    
    try:
        from src.unified_citation_processor_v2 import EYECITE_AVAILABLE
        print(f"EYECITE_AVAILABLE flag: {EYECITE_AVAILABLE}")
        
        if EYECITE_AVAILABLE:
            from src.unified_citation_processor_v2 import get_citations, AhocorasickTokenizer
            test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
            tokenizer = AhocorasickTokenizer()
            citations = get_citations(test_text, tokenizer=tokenizer)
            print(f"✓ Direct eyecite call found {len(citations)} citations")
            return True
        else:
            print("✗ Eyecite not available")
            return False
            
    except Exception as e:
        print(f"✗ Eyecite availability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run focused debug tests"""
    print("EXTRACTION PIPELINE DEBUG TEST")
    print("Testing each step of the unified processor pipeline")
    
    # Test eyecite availability first
    eyecite_works = test_eyecite_availability()
    
    # Test unified processor steps
    pipeline_works = test_unified_processor_steps()
    
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    print(f"Eyecite Available: {'✓ PASS' if eyecite_works else '✗ FAIL'}")
    print(f"Pipeline Works: {'✓ PASS' if pipeline_works else '✗ FAIL'}")

if __name__ == "__main__":
    main()
