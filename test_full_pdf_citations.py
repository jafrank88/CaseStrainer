#!/usr/bin/env python3
"""
Test citation extraction on full PDF text content
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.robust_pdf_extractor import RobustPDFExtractor
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_full_pdf_citations():
    """Test citation extraction on full PDF text content"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing citation extraction on full PDF text...")
    print(f"PDF: {pdf_path}")
    
    extractor = RobustPDFExtractor()
    
    try:
        result = extractor.extract_text(pdf_path)
        if isinstance(result, tuple):
            text = result[0]
        else:
            text = result
            
        print(f"Extracted text length: {len(text)} characters")
        
        # Process with citation processor
        processor = UnifiedCitationProcessorV2()
        
        async def run_test():
            print(f"\n=== Processing Full PDF Text ===")
            
            result = await processor.process_text(text)
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            if citations:
                print(f"\nFirst 10 citations:")
                for i, cit in enumerate(citations[:10]):
                    print(f"  {i+1}. {cit.citation} - {cit.extracted_case_name} ({cit.extracted_date})")
                
                # Count by citation type
                p2d_count = sum(1 for cit in citations if 'P.2d' in cit.citation)
                p3d_count = sum(1 for cit in citations if 'P.3d' in cit.citation)
                us_count = sum(1 for cit in citations if 'U.S.' in cit.citation)
                
                print(f"\n=== Citation Summary ===")
                print(f"P.2d citations: {p2d_count}")
                print(f"P.3d citations: {p3d_count}")
                print(f"U.S. citations: {us_count}")
                print(f"Total: {len(citations)}")
                
                # Show verified citations
                verified_count = sum(1 for cit in citations if cit.verified)
                print(f"Verified citations: {verified_count}/{len(citations)}")
        
        # Run the async test
        asyncio.run(run_test())
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_pdf_citations()
