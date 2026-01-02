#!/usr/bin/env python3
"""
Test the clean extraction pipeline directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.robust_pdf_extractor import RobustPDFExtractor
from src.clean_extraction_pipeline import extract_citations_clean

def test_clean_pipeline():
    """Test the clean extraction pipeline on PDF text"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing clean extraction pipeline...")
    print(f"PDF: {pdf_path}")
    
    extractor = RobustPDFExtractor()
    
    try:
        result = extractor.extract_text(pdf_path)
        if isinstance(result, tuple):
            text = result[0]
        else:
            text = result
            
        print(f"Extracted text length: {len(text)} characters")
        
        # Test with clean extraction pipeline (what the API uses)
        print(f"\n=== Testing Clean Extraction Pipeline ===")
        
        citations = extract_citations_clean(text)
        
        print(f"Citations found: {len(citations)}")
        
        if citations:
            print(f"\nFirst 10 citations:")
            for i, cit in enumerate(citations[:10]):
                print(f"  {i+1}. {cit.citation} - {cit.extracted_case_name} ({cit.extracted_date})")
            
            # Count citation types
            p2d_count = sum(1 for cit in citations if 'P.2d' in cit.citation)
            p3d_count = sum(1 for cit in citations if 'P.3d' in cit.citation)
            us_count = sum(1 for cit in citations if 'U.S.' in cit.citation)
            
            print(f"\n=== Citation Summary ===")
            print(f"P.2d citations: {p2d_count}")
            print(f"P.3d citations: {p3d_count}")
            print(f"U.S. citations: {us_count}")
            print(f"Total: {len(citations)}")
            
        else:
            print("❌ No citations found with clean pipeline!")
            
            # Let's see if the text contains citations
            print(f"\n=== Debugging Text Content ===")
            if '463 U.S. 29' in text:
                print("✅ Text contains '463 U.S. 29'")
            else:
                print("❌ Text does NOT contain '463 U.S. 29'")
                
            if '486 P.2d 906' in text:
                print("✅ Text contains '486 P.2d 906'")
            else:
                print("❌ Text does NOT contain '486 P.2d 906'")
                
            # Show first 1000 chars
            print(f"\nFirst 1000 characters:")
            print("-" * 50)
            print(text[:1000])
            print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clean_pipeline()
