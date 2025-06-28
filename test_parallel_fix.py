#!/usr/bin/env python3

import sys
import traceback

def test_parallel_citations():
    print("Testing parallel citation handling...")
    
    try:
        from src.document_processing import process_document
        print("Import successful")
        
        # Test with a manually constructed long citation string
        test_citation = '410 U.S. 113, 93 S. Ct. 705, 35 L. Ed. 2d 147, 1973 U.S. LEXIS 159'
        print(f"Processing document with citation string: {test_citation}")
        result = process_document(content=f'Test with {test_citation}')
        print("Document processing completed")
        
        print(f'Total citations: {len(result.get("citations", []))}')
        print('Sample citations:')
        
        for i, citation in enumerate(result.get('citations', [])[:10], 1):
            print(f'  {i}. {citation.get("citation", "N/A")} (verified={citation.get("verified", "N/A")})')
            if citation.get('is_parallel_citation'):
                print(f'      -> Parallel citation of: {citation.get("primary_citation", "N/A")}')
        
        # Check verification statistics
        verified_count = sum(1 for c in result.get('citations', []) if c.get('verified') in ['true', 'true_by_parallel'])
        total_count = len(result.get('citations', []))
        print(f'\nVerification summary: {verified_count}/{total_count} citations verified')
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_parallel_citations() 