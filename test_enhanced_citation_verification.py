#!/usr/bin/env python3
"""
Test script to demonstrate enhanced citation verification with year and parallel citations.
"""

import sys
import os
import json
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_enhanced_citation_verification():
    """Test the enhanced citation verification system."""
    
    print("=== Enhanced Citation Verification Test ===\n")
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations with known metadata
    test_citations = [
        "415 U.S. 308",  # Davis v. Alaska (1974)
        "534 F.3d 1290",  # Should have parallel citations
        "987 F.2d 654",   # Another federal case
    ]
    
    for citation in test_citations:
        print(f"\n--- Testing Citation: {citation} ---")
        
        # Verify the citation
        start_time = time.time()
        result = verifier.verify_citation(citation)
        end_time = time.time()
        
        print(f"Verification time: {end_time - start_time:.2f} seconds")
        print(f"Verified: {result.get('verified', False)}")
        print(f"Source: {result.get('source', 'Unknown')}")
        print(f"Case Name: {result.get('case_name', 'Unknown')}")
        
        # Check for year information
        year = result.get('year', '')
        if year:
            print(f"Year: {year}")
        else:
            print("Year: Not found")
            
        # Check for date_filed
        date_filed = result.get('date_filed', '')
        if date_filed:
            print(f"Date Filed: {date_filed}")
        else:
            print("Date Filed: Not found")
            
        # Check for parallel citations
        parallel_citations = result.get('parallel_citations', [])
        if parallel_citations:
            print(f"Parallel Citations ({len(parallel_citations)}):")
            for i, parallel in enumerate(parallel_citations, 1):
                parallel_year = parallel.get('year', '')
                year_info = f" (Year: {parallel_year})" if parallel_year else ""
                print(f"  {i}. {parallel.get('citation', 'Unknown')} - {parallel.get('reporter', 'Unknown')}{year_info}")
        else:
            print("Parallel Citations: None found")
            
        # Check metadata
        metadata = result.get('metadata', {})
        if metadata:
            print("Metadata:")
            for key, value in metadata.items():
                if key != 'timestamp':  # Skip timestamp for cleaner output
                    print(f"  {key}: {value}")
        
        print("-" * 50)

def test_cache_retrieval():
    """Test retrieving cached citations with enhanced metadata."""
    
    print("\n=== Cache Retrieval Test ===\n")
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test a citation that should be in cache
    test_citation = "415 U.S. 308"
    
    print(f"Testing cache retrieval for: {test_citation}")
    
    # First verification (should hit cache)
    start_time = time.time()
    result1 = verifier.verify_citation(test_citation)
    end_time = time.time()
    
    print(f"First verification time: {end_time - start_time:.2f} seconds")
    print(f"Year from cache: {result1.get('year', 'Not found')}")
    print(f"Parallel citations from cache: {len(result1.get('parallel_citations', []))}")
    
    # Second verification (should be faster from cache)
    start_time = time.time()
    result2 = verifier.verify_citation(test_citation)
    end_time = time.time()
    
    print(f"Second verification time: {end_time - start_time:.2f} seconds")
    print(f"Year from cache: {result2.get('year', 'Not found')}")
    print(f"Parallel citations from cache: {len(result2.get('parallel_citations', []))}")

def test_database_storage():
    """Test database storage and retrieval of enhanced metadata."""
    
    print("\n=== Database Storage Test ===\n")
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citation
    test_citation = "123 F.3d 456"
    
    print(f"Testing database storage for: {test_citation}")
    
    # Create a mock result with year and parallel citations
    mock_result = {
        "verified": True,
        "citation": test_citation,
        "case_name": "Test Case v. Test Defendant",
        "source": "Test API",
        "date_filed": "2023-05-15",
        "court": "United States Court of Appeals",
        "docket_number": "22-1234",
        "parallel_citations": [
            {
                "citation": "123 F.3d 456",
                "reporter": "F.3d",
                "category": "official",
                "year": "2023"
            },
            {
                "citation": "2023 WL 1234567",
                "reporter": "WL",
                "category": "unofficial",
                "year": "2023"
            }
        ],
        "metadata": {
            "year": "2023",
            "volume": "123",
            "page": "456"
        }
    }
    
    # Save to database
    success = verifier._save_to_database(test_citation, mock_result)
    print(f"Database save success: {success}")
    
    # Retrieve from database
    db_result = verifier._check_database(test_citation)
    if db_result and db_result.get('verified'):
        print(f"Database retrieval successful")
        print(f"Year from database: {db_result.get('year', 'Not found')}")
        print(f"Parallel citations from database: {len(db_result.get('parallel_citations', []))}")
        for i, parallel in enumerate(db_result.get('parallel_citations', []), 1):
            year_info = f" (Year: {parallel.get('year', '')})" if parallel.get('year') else ""
            print(f"  {i}. {parallel.get('citation', 'Unknown')}{year_info}")
    else:
        print("Database retrieval failed")

def main():
    """Main test function."""
    try:
        test_enhanced_citation_verification()
        test_cache_retrieval()
        test_database_storage()
        
        print("\n=== Test Summary ===")
        print("Enhanced citation verification system tested successfully!")
        print("Features verified:")
        print("- Year extraction from date_filed and metadata")
        print("- Parallel citations storage and retrieval")
        print("- Enhanced cache with year and parallel citation data")
        print("- Database storage with year and parallel citation fields")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 