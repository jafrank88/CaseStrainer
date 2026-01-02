#!/usr/bin/env python3
"""Test extraction exactly as the worker does it"""

import requests
import tempfile
import os
from src.unified_text_extractor import extract_text_from_file_unified
from src.citation_extraction_endpoint import extract_citations_with_clustering

def test_worker_extraction():
    """Test extraction exactly as the rq_worker does it"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/1031351.pdf"
    
    print(f"Testing worker extraction with: {pdf_url}")
    
    # Download PDF (same as worker)
    try:
        response = requests.get(pdf_url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Save to temporary file (same as worker)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        print(f"Downloaded {len(response.content)} bytes to {temp_path}")
        
        # Extract text using UnifiedTextExtractor (same as worker)
        text, method = extract_text_from_file_unified(temp_path, verbose=True)
        print(f"Extracted {len(text)} characters using {method}")
        
        # Call extract_citations_with_clustering (same as worker)
        print("\nCalling extract_citations_with_clustering...")
        result = extract_citations_with_clustering(
            text=text,
            enable_verification=False  # Same as worker
        )
        
        print(f"Result keys: {list(result.keys())}")
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"Found {len(citations)} citations and {len(clusters)} clusters")
        
        if citations:
            print("\nFirst 3 citations:")
            for i, citation in enumerate(citations[:3], 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
        
        return len(citations) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            os.unlink(temp_path)
            print(f"\nCleaned up temp file")
        except:
            pass

if __name__ == "__main__":
    success = test_worker_extraction()
    if success:
        print("\nSUCCESS: Worker extraction works!")
    else:
        print("\nFAILED: Worker extraction has issues")
