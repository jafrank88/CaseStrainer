#!/usr/bin/env python3
"""
Step-by-step extraction debugging to find exactly where the pipeline fails
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_individual_extraction_steps():
    """Test each individual step of the extraction pipeline"""
    print("=" * 60)
    print("DETAILED STEP-BY-STEP EXTRACTION TEST")
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
        
        # Test individual regex patterns
        print("\n1. Testing individual regex patterns...")
        us_pattern = processor.citation_patterns.get('us')
        if us_pattern:
            matches = list(us_pattern.finditer(test_text))
            print(f"✓ US pattern found {len(matches)} matches")
            for match in matches:
                print(f"  Match: '{match.group(0)}'")
        else:
            print("✗ US pattern not found")
        
        # Test regex enhanced extraction step by step
        print("\n2. Testing _extract_with_regex_enhanced step by step...")
        
        # Check if patterns exist
        priority_patterns = ['us', 'f3d', 'p3d', 'wn2d']
        for pattern_name in priority_patterns:
            if pattern_name in processor.citation_patterns:
                pattern = processor.citation_patterns[pattern_name]
                matches = list(pattern.finditer(test_text))
                print(f"  Pattern '{pattern_name}': {len(matches)} matches")
                for match in matches:
                    print(f"    Match: '{match.group(0)}'")
            else:
                print(f"  Pattern '{pattern_name}': NOT FOUND")
        
        # Test full regex enhanced extraction
        print("\n3. Testing full _extract_with_regex_enhanced...")
        try:
            regex_citations = processor._extract_with_regex_enhanced(test_text)
            print(f"✓ Regex enhanced found {len(regex_citations)} citations")
            for i, citation in enumerate(regex_citations):
                print(f"  Citation {i+1}: {citation.citation} (method: {citation.method})")
        except Exception as e:
            print(f"✗ Regex enhanced failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test eyecite extraction
        print("\n4. Testing _extract_with_eyecite...")
        try:
            eyecite_citations = processor._extract_with_eyecite(test_text)
            print(f"✓ Eyecite found {len(eyecite_citations)} citations")
            for i, citation in enumerate(eyecite_citations):
                print(f"  Citation {i+1}: {citation.citation} (method: {citation.method})")
        except Exception as e:
            print(f"✗ Eyecite failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test deduplication step
        print("\n5. Testing deduplication...")
        try:
            # Combine results manually
            all_citations = []
            if 'regex_citations' in locals():
                all_citations.extend(regex_citations)
            if 'eyecite_citations' in locals():
                all_citations.extend(eyecite_citations)
            
            print(f"  Before deduplication: {len(all_citations)} citations")
            deduplicated = processor._deduplicate_citations(all_citations)
            print(f"  After deduplication: {len(deduplicated)} citations")
            
            for i, citation in enumerate(deduplicated):
                print(f"    Citation {i+1}: {citation.citation} (method: {citation.method})")
                
        except Exception as e:
            print(f"✗ Deduplication failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test unified extraction
        print("\n6. Testing _extract_citations_unified...")
        try:
            unified_citations = processor._extract_citations_unified(test_text)
            print(f"✓ Unified extraction found {len(unified_citations)} citations")
            for i, citation in enumerate(unified_citations):
                print(f"  Citation {i+1}: {citation.citation} (method: {citation.method})")
        except Exception as e:
            print(f"✗ Unified extraction failed: {e}")
            import traceback
            traceback.print_exc()
        
        return len(unified_citations) > 0 if 'unified_citations' in locals() else False
        
    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run detailed step-by-step tests"""
    print("DETAILED EXTRACTION PIPELINE DEBUG")
    print("Testing each individual step to find the exact failure point")
    
    success = test_individual_extraction_steps()
    
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    print(f"Extraction Pipeline: {'✓ PASS' if success else '✗ FAIL'}")

if __name__ == "__main__":
    main()
