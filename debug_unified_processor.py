#!/usr/bin/env python3
"""
Debug Unified Processor - Isolate the specific extraction bug
"""

import sys
import os
import asyncio
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_extraction():
    """Test basic citation extraction step by step"""
    print("=" * 60)
    print("TESTING BASIC EXTRACTION STEP BY STEP")
    print("=" * 60)
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    print(f"Test text: {test_text}")
    
    try:
        # Test 1: Import and initialize
        print("\n1. Testing imports...")
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from src.models import ProcessingConfig
        print("✓ Imports successful")
        
        # Test 2: Create config
        print("\n2. Testing config creation...")
        config = ProcessingConfig()
        config.enable_verification = False
        config.debug_mode = True
        print("✓ Config created")
        
        # Test 3: Initialize processor
        print("\n3. Testing processor initialization...")
        processor = UnifiedCitationProcessorV2(config=config)
        print("✓ Processor initialized")
        
        # Test 4: Test regex extraction directly
        print("\n4. Testing regex extraction...")
        try:
            from src.citation_extraction_optimized import CitationExtractor
            extractor = CitationExtractor()
            citations = extractor.extract_citations(test_text)
            print(f"✓ Regex extraction found {len(citations)} citations")
            for i, citation in enumerate(citations):
                print(f"  Citation {i+1}: {citation}")
        except Exception as e:
            print(f"✗ Regex extraction failed: {e}")
            traceback.print_exc()
        
        # Test 5: Test async processing
        print("\n5. Testing async processing...")
        try:
            result = asyncio.run(processor.process_text(test_text))
            print(f"✓ Async processing completed")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Citations: {len(result.get('citations', []))}")
            print(f"  Clusters: {len(result.get('clusters', []))}")
            
            if result.get('citations'):
                print("  First citation details:")
                first_citation = result['citations'][0]
                if hasattr(first_citation, 'citation'):
                    print(f"    Citation text: {first_citation.citation}")
                    print(f"    Case name: {first_citation.extracted_case_name}")
                    print(f"    Date: {first_citation.extracted_date}")
                else:
                    print(f"    Citation: {first_citation}")
            
            return len(result.get('citations', [])) > 0
            
        except Exception as e:
            print(f"✗ Async processing failed: {e}")
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        traceback.print_exc()
        return False

def test_simple_citation_patterns():
    """Test simple citation pattern matching"""
    print("\n" + "=" * 60)
    print("TESTING SIMPLE CITATION PATTERNS")
    print("=" * 60)
    
    test_cases = [
        "347 U.S. 483",
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Luis v. United States, 136 S. Ct. 1083 (2016)",
        "578 U.S. 5 (2016)"
    ]
    
    try:
        from src.citation_extraction_optimized import CitationExtractor
        extractor = CitationExtractor()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case}")
            try:
                citations = extractor.extract_citations(test_case)
                print(f"  Found {len(citations)} citations")
                for j, citation in enumerate(citations):
                    print(f"    {j+1}: {citation}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                
    except Exception as e:
        print(f"✗ Pattern test failed: {e}")
        traceback.print_exc()

def main():
    """Run focused debug tests"""
    print("UNIFIED PROCESSOR DEBUG TEST")
    print("Isolating the specific extraction bug")
    
    # Run tests
    test_simple_citation_patterns()
    basic_works = test_basic_extraction()
    
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    print(f"Basic Extraction: {'✓ PASS' if basic_works else '✗ FAIL'}")

if __name__ == "__main__":
    main()
