#!/usr/bin/env python3
from src.improved_year_extraction_comparison import process_document

def test_single_brief():
    brief_file = 'wa_briefs_text/003_COA  Appellant Brief.txt'
    print(f"Testing with: {brief_file}")
    
    result = process_document(brief_file)
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
    
    toa_citations = result['toa_citations']
    body_citations = result['body_citations']
    comparison = result['comparison']
    
    print(f"\nResults:")
    print(f"ToA citations: {len(toa_citations)}")
    print(f"Body citations: {len(body_citations)}")
    print(f"Case name mismatches: {len(comparison['different_case_names'])}")
    
    print("\nSample ToA case names (first 5):")
    for i, cit in enumerate(toa_citations[:5]):
        print(f"  {i+1}. {cit.get('case_name', 'No name')}")

if __name__ == "__main__":
    test_single_brief() 