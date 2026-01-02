#!/usr/bin/env python3
"""
Simple PDF content debug
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.robust_pdf_extractor import RobustPDFExtractor

def simple_pdf_debug():
    """Simple debug of PDF content"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Debugging PDF: {pdf_path}")
    
    extractor = RobustPDFExtractor()
    
    # Get auto-extracted text
    try:
        result = extractor.extract_text(pdf_path)
        
        # Handle both string and tuple return types
        if isinstance(result, tuple):
            text = result[0]  # First element is the text
            print(f"Extractor returned tuple with {len(result)} elements")
        else:
            text = result
            
        print(f"Extracted {len(text)} characters")
        
        # Show first 1000 characters
        print(f"\nFirst 1000 characters:")
        print("-" * 50)
        print(text[:1000])
        print("-" * 50)
        
        # Look for any legal citations
        import re
        
        # Federal citations
        fed_cites = re.findall(r'\d+\s+F\.\d+\s+\d+', text)
        print(f"\nFederal citations found: {len(fed_cites)}")
        for cite in fed_cites[:5]:
            print(f"  - {cite}")
        
        # US Supreme Court citations
        us_cites = re.findall(r'\d+\s+U\.\S\.\s+\d+', text)
        print(f"\nUS citations found: {len(us_cites)}")
        for cite in us_cites[:5]:
            print(f"  - {cite}")
        
        # State citations
        state_cites = re.findall(r'\d+\s+[A-Z\.]+\s+\d+', text)
        print(f"\nState citations found: {len(state_cites)}")
        for cite in state_cites[:5]:
            print(f"  - {cite}")
        
        # Check if this looks like a legal document
        legal_keywords = ['v.', 'Court', 'App.', 'Cir.', 'Supreme', 'District']
        keyword_count = sum(1 for keyword in legal_keywords if keyword in text)
        print(f"\nLegal keywords found: {keyword_count}/6")
        
        if keyword_count < 2:
            print("⚠️  This might not be a legal document with citations")
        
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_pdf_debug()
