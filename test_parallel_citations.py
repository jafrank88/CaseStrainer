#!/usr/bin/env python3
"""
Test script to check propagation of extracted and canonical metadata for primary and parallel citations.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from document_processing import extract_and_verify_citations

def test_parallel_citation_extraction():
    """Test parallel citation extraction from various sources."""
    print("=== Testing Parallel Citation Extraction ===\n")
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations that should have parallel citations
    test_citations = [
        "199 Wn. App. 280",  # Should have parallel citation "399 P.3d 1195"
        "149 Wash. 2d 647",  # Should have parallel citation "71 P.3d 638"
        "115 Wash. 2d 294",  # Should have parallel citation "797 P.2d 1141"
    ]
    
    for citation in test_citations:
        print(f"Testing citation: {citation}")
        print("-" * 50)
        
        try:
            # Verify the citation
            result = verifier.verify_citation_unified_workflow(citation)
            
            print(f"Verification result: {result.get('verified', 'unknown')}")
            print(f"Source: {result.get('source', 'unknown')}")
            print(f"Case name: {result.get('case_name', 'unknown')}")
            
            # Check for parallel citations
            parallel_citations = result.get('parallel_citations', [])
            print(f"Parallel citations found: {len(parallel_citations)}")
            
            if parallel_citations:
                print("Parallel citations:")
                for i, parallel in enumerate(parallel_citations, 1):
                    if isinstance(parallel, dict):
                        print(f"  {i}. {parallel.get('citation', 'unknown')}")
                        print(f"     Reporter: {parallel.get('reporter', 'unknown')}")
                        print(f"     Category: {parallel.get('category', 'unknown')}")
                        print(f"     URL: {parallel.get('url', 'unknown')}")
                    else:
                        print(f"  {i}. {parallel}")
            else:
                print("  No parallel citations found")
            
            print()
            
        except Exception as e:
            print(f"Error testing citation {citation}: {e}")
            print()

def check_database_parallel_citations():
    """Check the database for parallel citations."""
    print("=== Checking Database for Parallel Citations ===\n")
    
    db_path = "src/citations.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if parallel_citations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parallel_citations'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✓ parallel_citations table exists")
            
            # Check table schema
            cursor.execute("PRAGMA table_info(parallel_citations)")
            columns = cursor.fetchall()
            print(f"Table schema: {[col[1] for col in columns]}")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM parallel_citations")
            count = cursor.fetchone()[0]
            print(f"Number of parallel citation records: {count}")
            
            # Show some examples
            if count > 0:
                cursor.execute("""
                    SELECT pc.citation, pc.reporter, pc.category, pc.year, c.citation_text as primary_citation
                    FROM parallel_citations pc
                    JOIN citations c ON pc.citation_id = c.id
                    LIMIT 10
                """)
                examples = cursor.fetchall()
                print("\nExample parallel citations:")
                for example in examples:
                    print(f"  Primary: {example[4]}")
                    print(f"  Parallel: {example[0]} (Reporter: {example[1]}, Category: {example[2]}, Year: {example[3]})")
                    print()
        else:
            print("✗ parallel_citations table does not exist")
        
        # Check main citations table for parallel_citations column
        cursor.execute("PRAGMA table_info(citations)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'parallel_citations' in column_names:
            print("✓ parallel_citations column exists in citations table")
            
            # Check for non-empty parallel citations
            cursor.execute("""
                SELECT citation_text, parallel_citations 
                FROM citations 
                WHERE parallel_citations IS NOT NULL AND parallel_citations != '' 
                LIMIT 5
            """)
            examples = cursor.fetchall()
            
            if examples:
                print(f"Found {len(examples)} citations with parallel citations data:")
                for citation, parallel_data in examples:
                    try:
                        parsed = json.loads(parallel_data) if parallel_data else []
                        print(f"  {citation}: {parsed}")
                    except json.JSONDecodeError:
                        print(f"  {citation}: {parallel_data} (raw)")
            else:
                print("No citations found with parallel citations data")
        else:
            print("✗ parallel_citations column does not exist in citations table")
        
        # Check total citations
        cursor.execute("SELECT COUNT(*) FROM citations")
        total_citations = cursor.fetchone()[0]
        print(f"\nTotal citations in database: {total_citations}")
        
        # Check verified citations
        cursor.execute("SELECT COUNT(*) FROM citations WHERE found = 1")
        verified_citations = cursor.fetchone()[0]
        print(f"Verified citations: {verified_citations}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

def test_specific_citation_verification():
    """Test verification of a specific citation to see parallel citation handling."""
    print("=== Testing Specific Citation Verification ===\n")
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test the specific citation from the user's question
    citation = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    
    print(f"Testing citation: {citation}")
    print("-" * 60)
    
    try:
        # Verify the citation
        result = verifier.verify_citation_unified_workflow(citation)
        
        print(f"Verification result: {result.get('verified', 'unknown')}")
        print(f"Source: {result.get('source', 'unknown')}")
        print(f"Case name: {result.get('case_name', 'unknown')}")
        print(f"Canonical citation: {result.get('canonical_citation', 'unknown')}")
        
        # Check for parallel citations
        parallel_citations = result.get('parallel_citations', [])
        print(f"Parallel citations found: {len(parallel_citations)}")
        
        if parallel_citations:
            print("Parallel citations:")
            for i, parallel in enumerate(parallel_citations, 1):
                if isinstance(parallel, dict):
                    print(f"  {i}. {parallel.get('citation', 'unknown')}")
                    print(f"     Reporter: {parallel.get('reporter', 'unknown')}")
                    print(f"     Category: {parallel.get('category', 'unknown')}")
                    print(f"     URL: {parallel.get('url', 'unknown')}")
                else:
                    print(f"  {i}. {parallel}")
        else:
            print("  No parallel citations found")
        
        # Check if the parallel citation "399 P.3d 1195" is in the result
        if isinstance(result.get('canonical_citation'), list):
            citations_list = result['canonical_citation']
            if "399 P.3d 1195" in citations_list:
                print("\n✓ Parallel citation '399 P.3d 1195' found in canonical_citation")
            else:
                print("\n✗ Parallel citation '399 P.3d 1195' NOT found in canonical_citation")
                print(f"Canonical citations: {citations_list}")
        
        print()
        
    except Exception as e:
        print(f"Error testing citation {citation}: {e}")
        print()

def main():
    """Run all tests."""
    print("Parallel Citation Extraction and Storage Test")
    print("=" * 50)
    print(f"Test run at: {datetime.now()}")
    print()
    
    # Test 1: Check database structure and existing data
    check_database_parallel_citations()
    print()
    
    # Test 2: Test specific citation verification
    test_specific_citation_verification()
    
    # Test 3: Test parallel citation extraction
    test_parallel_citation_extraction()
    
    # Test 4: Test extraction and verification pipeline
    test_text = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    print("Testing extraction and verification for:")
    print(test_text)
    print("-" * 60)
    results, _ = extract_and_verify_citations(test_text)
    print("Backend output:")
    for i, citation in enumerate(results, 1):
        print(f"\nCitation {i}: {citation.get('citation')}")
        print(json.dumps(citation, indent=2, ensure_ascii=False))
    
    print("Test completed!")

if __name__ == "__main__":
    main() 