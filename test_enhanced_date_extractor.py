#!/usr/bin/env python3
"""
Test script for the enhanced DateExtractor in the core.
"""

from src.case_name_extraction_core import date_extractor, DateExtractor

def test_date_extractor():
    """Test the enhanced DateExtractor functionality."""
    print("Testing Enhanced DateExtractor in Core...")
    
    # Test cases with different date formats
    test_cases = [
        {
            'text': 'Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).',
            'citation': '200 Wn.2d 72',
            'expected_year': '2022',
            'description': 'Year in parentheses after citation'
        },
        {
            'text': 'The court decided in 2021 that Smith v. Jones, 150 Wn.2d 100, was correctly decided.',
            'citation': '150 Wn.2d 100',
            'expected_year': '2021',
            'description': 'Year in legal context before citation'
        },
        {
            'text': 'Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).',
            'citation': '171 Wn.2d 486',
            'expected_year': '2011',
            'description': 'Year in parentheses after parallel citation'
        },
        {
            'text': 'The case was filed on January 15, 2023. See Doe v. Roe, 180 Wn.2d 200.',
            'citation': '180 Wn.2d 200',
            'expected_year': '2023',
            'description': 'Full date format before citation'
        },
        {
            'text': 'In the matter decided in 2020, the court ruled in favor of the plaintiff.',
            'citation': 'some citation',
            'expected_year': '2020',
            'description': 'Year in legal context without specific citation'
        }
    ]
    
    print(f"\nTesting {len(test_cases)} date extraction scenarios:")
    print("=" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Text: {test_case['text'][:80]}...")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected_year']}")
        
        try:
            # Test different extraction methods
            methods = [
                ('extract_date_from_citation', date_extractor.extract_date_from_citation(test_case['text'], test_case['citation'])),
                ('extract_year_only', date_extractor.extract_year_only(test_case['text'], test_case['citation'])),
                ('extract_date_from_full_text', date_extractor.extract_date_from_full_text(test_case['text']))
            ]
            
            found_date = None
            method_used = None
            
            for method_name, result in methods:
                if result:
                    if '-' in str(result):
                        year = str(result).split('-')[0]
                    else:
                        year = str(result)
                    
                    if year == test_case['expected_year']:
                        found_date = year
                        method_used = method_name
                        break
            
            if found_date:
                print(f"✅ PASS: Found year '{found_date}' using {method_used}")
                passed += 1
            else:
                print(f"❌ FAIL: Expected '{test_case['expected_year']}', got '{found_date}'")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced DateExtractor is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total

def test_date_validation_and_normalization():
    """Test date validation and normalization functionality."""
    print("\n\nTesting Date Validation and Normalization...")
    print("=" * 60)
    
    # Test validation
    validation_tests = [
        ('2023-01-15', True, 'Valid ISO date'),
        ('2023', True, 'Valid year'),
        ('1800', True, 'Valid old year'),
        ('2025', True, 'Valid future year'),
        ('invalid', False, 'Invalid date'),
        ('', False, 'Empty string'),
        ('1999-13-45', False, 'Invalid month/day'),
    ]
    
    print("\nDate Validation Tests:")
    for date_str, expected, description in validation_tests:
        result = date_extractor.validate_date(date_str)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {description} - '{date_str}' -> {result} (expected {expected})")
    
    # Test normalization
    normalization_tests = [
        ('2023-01-15', '2023-01-15', 'Already ISO format'),
        ('2023', '2023-01-01', 'Year only'),
        ('January 15, 2023', '2023-01-15', 'Month name format'),
        ('01/15/2023', '2023-01-15', 'US format'),
        ('invalid', 'N/A', 'Invalid format'),
    ]
    
    print("\nDate Normalization Tests:")
    for input_date, expected, description in normalization_tests:
        result = date_extractor.normalize_date_format(input_date)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {description} - '{input_date}' -> '{result}' (expected '{expected}')")

def test_integration_with_unified_processor():
    """Test integration with UnifiedCitationProcessorV2."""
    print("\n\nTesting Integration with UnifiedCitationProcessorV2...")
    print("=" * 60)
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    
    test_text = "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)."
    
    try:
        # Create processor with date extraction enabled
        config = ProcessingConfig(
            use_eyecite=False,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Process the text
        results = processor.process_text(test_text)
        
        print(f"Found {len(results)} citations:")
        for i, citation in enumerate(results, 1):
            print(f"  {i}. Citation: {citation.citation}")
            print(f"     Extracted Date: {citation.extracted_date}")
            print(f"     Case Name: {citation.extracted_case_name}")
            print()
        
        # Check if dates were extracted
        citations_with_dates = [c for c in results if c.extracted_date]
        print(f"Citations with extracted dates: {len(citations_with_dates)}/{len(results)}")
        
        if citations_with_dates:
            print("✅ SUCCESS: Integration with UnifiedCitationProcessorV2 working!")
            return True
        else:
            print("❌ FAIL: No dates extracted in integration test")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in integration test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Enhanced DateExtractor Test Suite")
    print("=" * 60)
    
    # Run all tests
    test1_passed = test_date_extractor()
    test_date_validation_and_normalization()
    test2_passed = test_integration_with_unified_processor()
    
    print(f"\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Date Extraction Tests: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Enhanced DateExtractor is ready for production.")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.") 