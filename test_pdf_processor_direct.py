#!/usr/bin/env python3
"""Test the OptimizedPDFProcessor directly"""

import requests
import tempfile
import os
import sys

# Add src to path
sys.path.insert(0, 'src')

try:
    from src.optimized_pdf_processor import OptimizedPDFProcessor
except ImportError as e:
    print(f"Failed to import OptimizedPDFProcessor: {e}")
    sys.exit(1)

def test_pdf_processor():
    """Test the PDF processor directly"""
    
    # Download PDF
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/863215.pdf"
    print(f"Downloading PDF from: {pdf_url}")
    
    try:
        response = requests.get(pdf_url, timeout=30, verify=False)
        response.raise_for_status()
        print(f"Downloaded {len(response.content)} bytes")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        print(f"Saved to temporary file: {temp_path}")
        
        try:
            # Process PDF
            print("\nStarting PDF processing...")
            processor = OptimizedPDFProcessor()
            
            import time
            start_time = time.time()
            
            result = processor.process_pdf(temp_path)
            
            elapsed_time = time.time() - start_time
            print(f"Processing completed in {elapsed_time:.2f} seconds")
            
            if result:
                print(f"Extracted {len(result.text)} characters")
                print(f"Number of pages: {result.page_count if hasattr(result, 'page_count') else 'N/A'}")
                print(f"Metadata: {result.metadata if hasattr(result, 'metadata') else 'N/A'}")
                
                # Show first 500 characters
                print("\nFirst 500 characters:")
                print("=" * 80)
                print(result.text[:500])
                print("=" * 80)
                
                # Check for citations in extracted text
                import re
                us_citations = re.findall(r'\d+\s+U\.S\.\s+\d+', result.text)
                f3d_citations = re.findall(r'\d+\s+F\.\d+d\s+\d+', result.text)
                wn2d_citations = re.findall(r'\d+\s+Wn\.?\d*d\s+\d+', result.text)
                
                print(f"\nCitations found in extracted text:")
                print(f"  U.S. citations: {len(us_citations)}")
                print(f"  F.3d citations: {len(f3d_citations)}")
                print(f"  Wn.2d citations: {len(wn2d_citations)}")
                
                if us_citations:
                    print(f"  First few U.S. citations: {us_citations[:3]}")
                
            else:
                print("No result returned from PDF processor")
                
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"\nCleaned up temporary file: {temp_path}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_processor()
