#!/usr/bin/env python3
"""
Test citation extraction from PDF directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor

def test_pdf_citations():
    """Test citation extraction from PDF"""
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing citation extraction from PDF...")
    print(f"PDF: {pdf_path}")
    
    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    
    print(f"PDF size: {len(pdf_data):,} bytes")
    
    # Create file input structure
    file_input = {
        'type': 'file',
        'file': pdf_data,
        'filename': 'sp-7788.pdf',
        'content_type': 'application/pdf',
        'file_size': len(pdf_data)
    }
    
    # Process with UnifiedInputProcessor
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
                print(f"  {i+1}. {cit}")
        
        if clusters:
            print(f"\nFirst 3 clusters:")
            for i, cluster in enumerate(clusters[:3]):
                print(f"  {i+1}. {cluster}")
        
        # Check extraction details
        extraction_info = result.get('extraction_info', {})
        if extraction_info:
            print(f"\nExtraction info:")
            for key, value in extraction_info.items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_citations()
