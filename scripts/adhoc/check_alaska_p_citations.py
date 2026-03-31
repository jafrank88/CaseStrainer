#!/usr/bin/env python3
"""
Check for Alaska P.2d and P.3d citations in the PDF
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.robust_pdf_extractor import RobustPDFExtractor
import re

def check_alaska_p_citations():
    """Check for Alaska P.2d and P.3d citations"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Checking for Alaska P.2d and P.3d citations...")
    print(f"PDF: {pdf_path}")
    
    extractor = RobustPDFExtractor()
    
    try:
        result = extractor.extract_text(pdf_path)
        if isinstance(result, tuple):
            text = result[0]
        else:
            text = result
            
        print(f"Extracted text length: {len(text)} characters")
        
        # Search for P.2d and P.3d citations
        p2d_citations = re.findall(r'\b\d+\s+P\.2d\s+\d+\b', text)
        p3d_citations = re.findall(r'\b\d+\s+P\.3d\s+\d+\b', text)
        
        print(f"\nP.2d citations found: {len(p2d_citations)}")
        for cite in sorted(set(p2d_citations)):
            print(f"  - {cite}")
            
        print(f"\nP.3d citations found: {len(p3d_citations)}")
        for cite in sorted(set(p3d_citations)):
            print(f"  - {cite}")
        
        # Find context around P.2d/P.3d citations
        all_p_citations = p2d_citations + p3d_citations
        
        if all_p_citations:
            print(f"\n=== Citation Context ===")
            for cite in sorted(set(all_p_citations))[:5]:  # Show first 5
                # Find the citation in text
                match = re.search(re.escape(cite), text)
                if match:
                    start = max(0, match.start() - 150)
                    end = min(len(text), match.end() + 150)
                    context = text[start:end].replace('\n', ' ').strip()
                    print(f"\n{cite}:")
                    print(f"  ...{context}...")
        
        # Also check for Alaska-specific patterns
        print(f"\n=== Alaska Citation Patterns ===")
        
        # Look for "Alaska" in context with citations
        alaska_contexts = []
        for match in re.finditer(r'.{0,100}Alaska.{0,100}', text):
            context = match.group(0).strip()
            if re.search(r'\d+\s+[A-Za-z\.\s]+\d+', context):
                alaska_contexts.append(context)
        
        print(f"Found {len(alaska_contexts)} contexts mentioning 'Alaska' with citations")
        for i, context in enumerate(alaska_contexts[:3]):
            print(f"\nContext {i+1}:")
            print(f"  {context}")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_alaska_p_citations()
