#!/usr/bin/env python3
"""
Test script to run Wikipedia case name paragraphs through the case trainer system.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_wikipedia_case_extraction():
    """Test case name extraction with Wikipedia case names."""
    
    # Test paragraph with a real case name from Wikipedia
    test_paragraph = "The court in Chisholm v. Georgia established important precedent regarding constitutional rights. This case, decided in the early 19th century, continues to influence modern jurisprudence. The holding in Chisholm v. Georgia has been cited in numerous subsequent decisions."
    
    print("=== Testing Wikipedia Case Name Extraction ===")
    print(f"Test paragraph: {test_paragraph}")
    print()
    
    try:
        # Import the case trainer modules
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        
        print("1. Testing with UnifiedCitationProcessorV2:")
        print("-" * 50)
        
        # Configure the processor
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True
        )
        
        processor = UnifiedCitationProcessorV2(config)
        
        # Process the text
        results = processor.process_text(test_paragraph)
        
        print(f"Found {len(results)} citation results:")
        for i, result in enumerate(results):
            print(f"  Result {i+1}:")
            print(f"    Citation: {result.citation}")
            print(f"    Canonical Name: {result.canonical_name}")
            print(f"    Extracted Case Name: {result.extracted_case_name}")
            print(f"    Date: {result.date}")
            print(f"    URL: {result.url}")
            print()
        
        print("2. Testing with extract_case_name_triple_comprehensive:")
        print("-" * 50)
        
        # Test the comprehensive extraction function
        extracted_name, extracted_date, confidence = extract_case_name_triple_comprehensive(test_paragraph)
        
        print(f"Extracted Name: {extracted_name}")
        print(f"Extracted Date: {extracted_date}")
        print(f"Confidence: {confidence}")
        
        # Check if the extraction was successful
        expected_case = "Chisholm v. Georgia"
        if extracted_name and extracted_name != "N/A":
            print(f"✓ Successfully extracted case name")
            if expected_case.lower() in extracted_name.lower():
                print(f"✓ Correctly identified expected case: {expected_case}")
            else:
                print(f"⚠ Extracted different case: {extracted_name} (expected: {expected_case})")
        else:
            print("✗ Failed to extract case name")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running this from the correct directory.")
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_wikipedia_cases():
    """Test multiple Wikipedia case names."""
    
    test_cases = [
        "The court in West v. Barnes established important precedent regarding constitutional rights.",
        "Chisholm v. Georgia represents a key moment in the development of constitutional law.",
        "In analyzing the constitutional issues presented, the court must consider the precedent set forth in Oswald v. New York.",
        "Van Staphorst v. Maryland established important precedent regarding constitutional rights.",
        "Collet v. Collet represents a key moment in the development of constitutional law."
    ]
    
    print("\n=== Testing Multiple Wikipedia Cases ===")
    
    try:
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        
        for i, test_text in enumerate(test_cases):
            print(f"\nTest {i+1}: {test_text}")
            
            extracted_name, extracted_date, confidence = extract_case_name_triple_comprehensive(test_text)
            
            print(f"  Extracted: {extracted_name}")
            print(f"  Date: {extracted_date}")
            print(f"  Confidence: {confidence}")
            
            # Check if extraction was successful
            if extracted_name and extracted_name != "N/A":
                print("  ✓ Extraction successful")
            else:
                print("  ✗ Extraction failed")
    
    except ImportError as e:
        print(f"Import error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_wikipedia_case_extraction()
    test_multiple_wikipedia_cases() 