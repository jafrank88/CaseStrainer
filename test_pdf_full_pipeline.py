#!/usr/bin/env python3
"""
Test PDF processing through the full pipeline
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor

def test_pdf_full_pipeline():
    """Test PDF processing through the full pipeline"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing PDF through full pipeline...")
    print(f"PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found")
        return
    
    # Read PDF as bytes
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    
    print(f"PDF size: {len(pdf_data):,} bytes")
    
    # Create file input structure (same as API)
    file_input = {
        'type': 'file',
        'file': pdf_data,
        'filename': 'sp-7788.pdf',
        'content_type': 'application/pdf',
        'file_size': len(pdf_data)
    }
    
    # Process with UnifiedInputProcessor (same as API)
    processor = UnifiedInputProcessor()
    
    print(f"\n=== Processing with UnifiedInputProcessor ===")
    
    try:
        result = processor.process_any_input(
            file_input,
            'file',
            'test-request-123',
            force_mode='sync'  # Force sync for testing
        )
        
        print(f"✅ Processing completed")
        print(f"Result keys: {list(result.keys())}")
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\nCitations found: {len(citations)}")
        print(f"Clusters found: {len(clusters)}")
        
        if citations:
            print(f"\nFirst 5 citations:")
            for i, cit in enumerate(citations[:5]):
                print(f"  {i+1}. {cit.citation} - {cit.extracted_case_name} ({cit.extracted_date})")
        
        if clusters:
            print(f"\nFirst 3 clusters:")
            for i, cluster in enumerate(clusters[:3]):
                cluster_id = cluster.get('cluster_id', 'N/A')
                cluster_name = cluster.get('canonical_name', 'N/A')
                citation_count = len(cluster.get('citations', []))
                print(f"  {i+1}. Cluster {cluster_id}: {cluster_name} ({citation_count} citations)")
        
        # Check extraction details
        extraction_info = result.get('extraction_info', {})
        if extraction_info:
            print(f"\nExtraction info:")
            for key, value in extraction_info.items():
                print(f"  {key}: {value}")
        
        # Check if text was extracted properly
        if 'text' in result:
            text = result['text']
            print(f"\nExtracted text length: {len(text)} characters")
            
            # Look for U.S. citations in the text
            import re
            us_cites = re.findall(r'\d+\s+U\.\S\.\s+\d+', text)
            print(f"U.S. citations found in text: {len(us_cites)}")
            for cite in us_cites[:5]:
                print(f"  - {cite}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_full_pipeline()
