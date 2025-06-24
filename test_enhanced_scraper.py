#!/usr/bin/env python3
"""
Test script for the Enhanced Legal Scraper

This script demonstrates how the enhanced scraper would work with
search engines to find case detail pages and extract comprehensive metadata.
"""

import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.enhanced_legal_scraper import EnhancedLegalScraper
import time

def test_enhanced_scraper():
    """Test the enhanced scraper with sample citations."""
    
    # Initialize the enhanced scraper
    scraper = EnhancedLegalScraper(use_google=True, use_bing=True)
    
    # Test citations
    test_citations = [
        "534 F.3d 1290",
        "410 U.S. 113",
        "347 U.S. 483",
        "163 Wn.2d 852"
    ]
    
    print("=" * 80, flush=True)
    print("ENHANCED LEGAL SCRAPER TEST", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    print("Supported databases:", flush=True)
    databases = scraper.get_supported_databases()
    for i, db in enumerate(databases, 1):
        print(f"  {i}. {db}", flush=True)
    print(flush=True)
    
    for citation in test_citations:
        print(f"Testing citation: {citation}", flush=True)
        print("-" * 60, flush=True)
        
        # Test with a specific database first
        test_database = "CaseMine"
        print(f"Searching {test_database} for: {citation}", flush=True)
        
        try:
            # Search for the case
            search_results = scraper.search_for_case(citation, test_database)
            print(f"Found {len(search_results)} search results", flush=True)
            
            for i, result in enumerate(search_results[:3], 1):  # Show top 3
                print(f"  Result {i}:", flush=True)
                print(f"    Title: {result.get('title', 'N/A')}", flush=True)
                print(f"    URL: {result.get('url', 'N/A')}", flush=True)
                print(f"    Source: {result.get('source', 'N/A')}", flush=True)
                print(f"    Score: {result.get('score', 0)}", flush=True)
                print(f"    Is Detail Page: {result.get('is_detail_page', False)}", flush=True)
                print(flush=True)
            
            # Extract metadata
            metadata = scraper.extract_case_metadata(citation, test_database)
            print("Extracted metadata:", flush=True)
            for key, value in metadata.items():
                print(f"  {key}: {value}", flush=True)
            print(flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            traceback.print_exc()
        
        print(flush=True)
        time.sleep(2)
    
    # Test extraction from all databases for one citation
    print("=" * 80, flush=True)
    print("TESTING EXTRACTION FROM ALL DATABASES", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    test_citation = "534 F.3d 1290"
    print(f"Extracting metadata for '{test_citation}' from all databases...", flush=True)
    
    try:
        all_results = scraper.extract_from_all_databases(test_citation)
        
        print(f"Found results from {len(all_results)} databases:", flush=True)
        print(flush=True)
        
        for database_name, metadata in all_results.items():
            print(f"Database: {database_name}", flush=True)
            print(f"  Canonical Name: {metadata.get('canonical_name', 'N/A')}", flush=True)
            print(f"  URL: {metadata.get('url', 'N/A')}", flush=True)
            print(f"  Year: {metadata.get('year', 'N/A')}", flush=True)
            print(f"  Court: {metadata.get('court', 'N/A')}", flush=True)
            print(f"  Docket: {metadata.get('docket', 'N/A')}", flush=True)
            print(f"  Parallel Citations: {metadata.get('parallel_citations', [])}", flush=True)
            print(f"  Search Source: {metadata.get('search_source', 'N/A')}", flush=True)
            print(f"  Search Score: {metadata.get('search_score', 0)}", flush=True)
            print(flush=True)
            
    except Exception as e:
        print(f"Error testing all databases: {e}", flush=True)
        traceback.print_exc()

def demonstrate_search_queries():
    """Demonstrate the search queries that would be generated."""
    
    scraper = EnhancedLegalScraper()
    test_citation = "534 F.3d 1290"
    
    print("=" * 80, flush=True)
    print("SEARCH QUERY DEMONSTRATION", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    for database_name in scraper.get_supported_databases():
        print(f"Database: {database_name}", flush=True)
        
        database_info = scraper.get_database_info(database_name)
        if database_info:
            queries = scraper._create_search_queries(test_citation, database_info)
            print("  Generated queries:", flush=True)
            for i, query in enumerate(queries, 1):
                print(f"    {i}. {query}", flush=True)
        else:
            print("  No database info available", flush=True)
        
        print(flush=True)

def show_implementation_notes():
    """Show implementation notes for production use."""
    
    print("=" * 80, flush=True)
    print("IMPLEMENTATION NOTES FOR PRODUCTION", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    print("To implement this in production, you would need:", flush=True)
    print(flush=True)
    print("1. Google Search API:", flush=True)
    print("   - Sign up for Google Custom Search API", flush=True)
    print("   - Get API key and Custom Search Engine ID", flush=True)
    print("   - Replace _search_google() method with actual API calls", flush=True)
    print(flush=True)
    print("2. Bing Search API:", flush=True)
    print("   - Sign up for Bing Search API (Microsoft Azure)", flush=True)
    print("   - Get API key and endpoint", flush=True)
    print("   - Replace _search_bing() method with actual API calls", flush=True)
    print(flush=True)
    print("3. Rate Limiting:", flush=True)
    print("   - Implement proper rate limiting for both APIs", flush=True)
    print("   - Respect API quotas and limits", flush=True)
    print("   - Add exponential backoff for failed requests", flush=True)
    print(flush=True)
    print("4. Caching:", flush=True)
    print("   - Cache search results to avoid repeated API calls", flush=True)
    print("   - Cache extracted metadata", flush=True)
    print("   - Implement cache invalidation strategy", flush=True)
    print(flush=True)
    print("5. Error Handling:", flush=True)
    print("   - Handle API rate limits gracefully", flush=True)
    print("   - Implement fallback strategies", flush=True)
    print("   - Log errors for monitoring", flush=True)
    print(flush=True)
    print("6. Configuration:", flush=True)
    print("   - Make API keys configurable", flush=True)
    print("   - Allow enabling/disabling specific search engines", flush=True)
    print("   - Configure timeouts and retry logic", flush=True)
    print(flush=True)

if __name__ == "__main__":
    # Test the enhanced scraper
    test_enhanced_scraper()
    
    # Demonstrate search queries
    demonstrate_search_queries()
    
    # Show implementation notes
    show_implementation_notes() 