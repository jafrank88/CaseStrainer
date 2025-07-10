#!/usr/bin/env python3
"""
Test script for the enhanced unified citation processor.

This script tests all the improvements integrated from CitationProcessor and CitationExtractor:
- Enhanced text cleaning
- Comprehensive regex patterns
- Date extraction from context
- Streaming support for large documents
- Better error handling and logging
"""

import sys
import os
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
from src.standalone_citation_parser import DateExtractor

def test_text_cleaning():
    """Test the enhanced text cleaning functionality."""
    print("=== Testing Text Cleaning ===")
    
    # Test cases with various text issues
    test_cases = [
        {
            'input': "This   has   extra   spaces   and\n\n\nline breaks",
            'expected_cleaned': "This has extra spaces and\n\nline breaks"
        },
        {
            'input': "This has \"curly quotes\" and 'smart quotes'",
            'expected_cleaned': "This has \"curly quotes\" and 'smart quotes'"
        },
        {
            'input': "This has unicode characters: café résumé naïve",
            'expected_cleaned': "This has unicode characters: café résumé naïve"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        cleaned = TextCleaner.clean_text(test_case['input'])
        print(f"Test {i+1}:")
        print(f"  Input: {repr(test_case['input'])}")
        print(f"  Cleaned: {repr(cleaned)}")
        print(f"  Expected: {repr(test_case['expected_cleaned'])}")
        print(f"  Pass: {cleaned == test_case['expected_cleaned']}")
        print()

def test_date_extraction():
    """Test the date extraction from context functionality."""
    print("=== Testing Date Extraction ===")
    
    # Test cases with dates in context
    test_cases = [
        {
            'text': "The court decided in 2024 that the case was important. See Smith v. Jones, 123 Wn. App. 456.",
            'citation_start': 70,
            'citation_end': 85,
            'expected_date': "2024-01-01"
        },
        {
            'text': "The case was filed on January 15, 2024. See Doe v. Roe, 456 P.3d 789.",
            'citation_start': 50,
            'citation_end': 65,
            'expected_date': "2024-01-15"
        },
        {
            'text': "The decision was issued on 2024-03-20. See Brown v. White, 789 F.3d 123.",
            'citation_start': 45,
            'citation_end': 60,
            'expected_date': "2024-03-20"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        extracted_date = DateExtractor.extract_date_from_context(
            test_case['text'], 
            test_case['citation_start'], 
            test_case['citation_end']
        )
        print(f"Test {i+1}:")
        print(f"  Text: {test_case['text']}")
        print(f"  Citation position: {test_case['citation_start']}-{test_case['citation_end']}")
        print(f"  Extracted date: {extracted_date}")
        print(f"  Expected date: {test_case['expected_date']}")
        print(f"  Pass: {extracted_date == test_case['expected_date']}")
        print()

def test_comprehensive_regex_patterns():
    """Test the comprehensive regex patterns from CitationExtractor."""
    print("=== Testing Comprehensive Regex Patterns ===")
    
    # Test text with various citation formats
    test_text = """
    The court cited several cases: Smith v. Jones, 123 Wn. App. 456, 789 P.3d 123 (2024);
    Doe v. Roe, 456 F.3d 789, 123 S. Ct. 456 (2024); Brown v. White, 789 A.2d 123;
    Green v. Blue, 2024 WL 123456; and Black v. Red, No. 48000-0-II.
    """
    
    processor = UnifiedCitationProcessor()
    citations = processor.extract_regex_citations(test_text)
    
    print(f"Found {len(citations)} citations:")
    for i, citation in enumerate(citations):
        print(f"  {i+1}. {citation.citation} (pattern: {citation.pattern})")
    
    # Check for specific citation types
    expected_patterns = ['wn_app', 'p3d', 'f3d', 'sct', 'a2d', 'westlaw']
    found_patterns = [c.pattern for c in citations]
    
    print(f"\nExpected patterns: {expected_patterns}")
    print(f"Found patterns: {found_patterns}")
    
    missing_patterns = [p for p in expected_patterns if p not in found_patterns]
    if missing_patterns:
        print(f"Missing patterns: {missing_patterns}")
    else:
        print("All expected patterns found!")
    print()

def test_complex_citation_processing():
    """Test complex citation processing with parallel citations."""
    print("=== Testing Complex Citation Processing ===")
    
    # Test text with complex citation patterns
    test_text = """
    The court held in Smith v. Jones, 123 Wn. App. 456, 789 P.3d 123 (2024) that the 
    defendant was liable. This was confirmed in Doe v. Roe, 456 F.3d 789, 123 S. Ct. 456, 
    789 L. Ed. 2d 123 (2024). The case history shows (I) the initial filing, (II) the 
    appeal, and (III) the final decision. The unpublished memorandum opinion was 
    released on January 15, 2024.
    """
    
    processor = UnifiedCitationProcessor()
    result = processor.process_text(test_text)
    
    print(f"Processing results:")
    print(f"  Total citations: {result['summary']['total_citations']}")
    print(f"  Parallel citations: {result['summary']['parallel_citations']}")
    print(f"  Verified citations: {result['summary']['verified_citations']}")
    print(f"  Unique cases: {result['summary']['unique_cases']}")
    
    print(f"\nFormatted results:")
    for i, citation in enumerate(result['results']):
        print(f"  {i+1}. {citation['display_text']}")
        if citation.get('parallel_citations'):
            print(f"     Parallel: {citation['parallel_citations']}")
    print()

def test_streaming_support():
    """Test streaming support for large documents."""
    print("=== Testing Streaming Support ===")
    
    # Create a large test document
    large_text = "This is a large document. " * 10000
    large_text += "Smith v. Jones, 123 Wn. App. 456, 789 P.3d 123 (2024). " * 100
    large_text += "Doe v. Roe, 456 F.3d 789 (2024). " * 100
    
    processor = UnifiedCitationProcessor()
    
    # Test chunk processing
    start_time = time.time()
    result = processor._process_text_in_chunks(large_text, chunk_size=50000, extract_case_names=True)
    processing_time = time.time() - start_time
    
    print(f"Large document processing:")
    print(f"  Document size: {len(large_text):,} characters")
    print(f"  Processing time: {processing_time:.2f} seconds")
    print(f"  Total citations: {result['statistics'].total_citations}")
    print(f"  Chunks processed: {result['metadata']['chunks_processed']}")
    print()

def test_error_handling():
    """Test error handling and edge cases."""
    print("=== Testing Error Handling ===")
    
    processor = UnifiedCitationProcessor()
    
    # Test with empty text
    result = processor.process_text("")
    print(f"Empty text result: {result['summary']}")
    
    # Test with None text
    result = processor.process_text(None)
    print(f"None text result: {result.get('error', 'No error')}")
    
    # Test with very long text
    very_long_text = "Test citation: Smith v. Jones, 123 Wn. App. 456. " * 10000
    result = processor.process_text(very_long_text)
    print(f"Very long text result: {result['summary']}")
    print()

def main():
    """Run all tests."""
    print("Enhanced Unified Citation Processor Test Suite")
    print("=" * 50)
    
    try:
        test_text_cleaning()
        test_date_extraction()
        test_comprehensive_regex_patterns()
        test_complex_citation_processing()
        test_streaming_support()
        test_error_handling()
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 