#!/usr/bin/env python3
"""
Test script to process the Washington Supreme Court PDF and verify that the 'verified' field 
and canonical metadata are preserved in the final output.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from document_processing import process_document
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')

def test_full_pipeline():
    """Test the full document processing pipeline with the Washington Supreme Court PDF."""
    print("Testing full document processing pipeline with Washington Supreme Court PDF...")
    
    # URL of the Washington Supreme Court PDF
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/1029764.pdf"
    
    try:
        # Process the document
        print(f"\nProcessing PDF from URL: {pdf_url}")
        result = process_document(url=pdf_url)
        
        print(f"\nProcessing completed successfully: {result.get('success', False)}")
        print(f"Number of citations found: {len(result.get('citations', []))}")
        print(f"Number of case names extracted: {len(result.get('case_names', []))}")
        
        # Check verification status and canonical metadata
        citations = result.get('citations', [])
        verified_count = 0
        canonical_metadata_count = 0
        
        print(f"\nDetailed citation analysis:")
        for i, citation in enumerate(citations, 1):
            verified = citation.get('verified', 'false')
            canonical_name = citation.get('canonical_name', '')
            canonical_date = citation.get('canonical_date', '')
            url = citation.get('url', '')
            
            if verified in ['true', 'true_by_parallel']:
                verified_count += 1
            
            if canonical_name or canonical_date or url:
                canonical_metadata_count += 1
            
            print(f"  Citation {i}: {citation.get('citation', 'N/A')}")
            print(f"    Verified: {verified}")
            print(f"    Canonical Name: {canonical_name}")
            print(f"    Canonical Date: {canonical_date}")
            print(f"    URL: {url}")
            print(f"    Court: {citation.get('court', '')}")
            print(f"    Docket: {citation.get('docket_number', '')}")
            print()
        
        print(f"\nSummary:")
        print(f"  Total citations: {len(citations)}")
        print(f"  Verified citations: {verified_count}")
        print(f"  Citations with canonical metadata: {canonical_metadata_count}")
        print(f"  Verification rate: {verified_count/len(citations)*100:.1f}%" if citations else "N/A")
        
        # Save detailed results to file for inspection
        output_file = "full_pipeline_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nDetailed results saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_full_pipeline() 