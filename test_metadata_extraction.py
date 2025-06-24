#!/usr/bin/env python3
"""
Comprehensive metadata extraction test for all legal database sources.

This script tests that we can extract all necessary metadata fields from
all the sources we have samples for.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.legal_database_scraper import LegalDatabaseScraper
import time

def test_metadata_extraction():
    """Test metadata extraction from all supported sources."""
    
    # Sample URLs for each source (from our previous examples)
    test_urls = {
        'vLex': 'https://vlex.com/sites/search?q=534+F.3d+1290',
        'CaseMine': 'https://www.casemine.com/search?q=534+F.3d+1290',
        'Casetext': 'https://casetext.com/search?q=534+F.3d+1290',
        'Leagle': 'https://www.leagle.com/search?q=534+F.3d+1290',
        'Justia': 'https://law.justia.com/search?query=534+F.3d+1290',
        'Descrybe': 'https://descrybe.ai/case/534-f-3d-1290',
        'Midpage': 'https://midpage.ai/case/534-f-3d-1290'
    }
    
    # Define the metadata fields we expect to extract
    expected_fields = [
        'canonical_name',
        'url', 
        'parallel_citations',
        'year',
        'court',
        'docket'
    ]
    
    # Initialize the scraper
    scraper = LegalDatabaseScraper()
    
    print("=" * 80)
    print("COMPREHENSIVE METADATA EXTRACTION TEST")
    print("=" * 80)
    print()
    
    results = {}
    
    for source_name, url in test_urls.items():
        print(f"Testing {source_name}...")
        print(f"URL: {url}")
        
        try:
            # Extract metadata
            metadata = scraper.extract_case_info(url)
            
            # Store results
            results[source_name] = {
                'url': url,
                'metadata': metadata,
                'success': True,
                'errors': []
            }
            
            # Check which fields were extracted
            extracted_fields = []
            missing_fields = []
            
            for field in expected_fields:
                if field in metadata:
                    value = metadata[field]
                    if value:  # Field exists and has a value
                        extracted_fields.append(field)
                        print(f"  ✓ {field}: {value}")
                    else:
                        missing_fields.append(field)
                        print(f"  - {field}: (empty)")
                else:
                    missing_fields.append(field)
                    print(f"  ✗ {field}: (missing)")
            
            print(f"  Extracted: {len(extracted_fields)}/{len(expected_fields)} fields")
            print(f"  Missing: {missing_fields}")
            
            # Check if we got the essential fields
            essential_fields = ['canonical_name', 'url']
            essential_missing = [f for f in essential_fields if f not in extracted_fields]
            
            if essential_missing:
                print(f"  ⚠️  WARNING: Missing essential fields: {essential_missing}")
            else:
                print(f"  ✅ Essential fields present")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results[source_name] = {
                'url': url,
                'metadata': {},
                'success': False,
                'errors': [str(e)]
            }
        
        print()
        time.sleep(2)  # Be respectful to servers
    
    # Summary report
    print("=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    successful_sources = []
    failed_sources = []
    
    for source_name, result in results.items():
        if result['success']:
            successful_sources.append(source_name)
            metadata = result['metadata']
            extracted_count = sum(1 for field in expected_fields if field in metadata and metadata[field])
            print(f"✅ {source_name}: {extracted_count}/{len(expected_fields)} fields extracted")
        else:
            failed_sources.append(source_name)
            print(f"❌ {source_name}: Failed - {result['errors']}")
    
    print()
    print(f"Successful sources: {len(successful_sources)}/{len(test_urls)}")
    print(f"Failed sources: {len(failed_sources)}/{len(test_urls)}")
    
    if failed_sources:
        print(f"Failed sources: {', '.join(failed_sources)}")
    
    # Field coverage analysis
    print()
    print("FIELD COVERAGE ANALYSIS:")
    print("-" * 40)
    
    field_coverage = {field: 0 for field in expected_fields}
    
    for source_name, result in results.items():
        if result['success']:
            metadata = result['metadata']
            for field in expected_fields:
                if field in metadata and metadata[field]:
                    field_coverage[field] += 1
    
    for field, count in field_coverage.items():
        percentage = (count / len(test_urls)) * 100
        print(f"{field:20}: {count:2d}/{len(test_urls)} ({percentage:5.1f}%)")
    
    return results

def test_specific_citation_extraction():
    """Test extraction from a specific citation across multiple sources."""
    
    test_citation = "534 F.3d 1290"
    
    print("=" * 80)
    print(f"TESTING EXTRACTION FOR CITATION: {test_citation}")
    print("=" * 80)
    print()
    
    scraper = LegalDatabaseScraper()
    
    try:
        # Extract from multiple sources
        results = scraper.extract_from_multiple_sources(test_citation)
        
        print(f"Found results from {len(results)} sources:")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            for field, value in result.items():
                print(f"  {field}: {value}")
            print()
            
    except Exception as e:
        print(f"Error testing citation extraction: {e}")

if __name__ == "__main__":
    # Test individual URL extraction
    test_metadata_extraction()
    
    print("\n" + "=" * 80)
    print("TESTING MULTI-SOURCE CITATION EXTRACTION")
    print("=" * 80)
    
    # Test multi-source citation extraction
    test_specific_citation_extraction() 