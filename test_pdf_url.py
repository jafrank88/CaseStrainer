#!/usr/bin/env python3
"""
Test script to check the specific PDF URL that was working before
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_pdf_url():
    """Test the specific PDF URL that was working before"""
    
    url = "https://www.courts.wa.gov/opinions/pdf/1029764.pdf"
    
    print("Testing PDF URL extraction...")
    print(f"URL: {url}")
    
    try:
        # Test the document processing
        from src.document_processing import process_document
        
        result = process_document(url=url, extract_case_names=True)
        
        print(f"Result: {result}")
        print(f"Success: {result.get('success', False)}")
        print(f"Text length: {result.get('text_length', 0)}")
        print(f"Citations: {len(result.get('citations', []))}")
        print(f"Case names: {len(result.get('case_names', []))}")
        
        if result.get('text_length', 0) > 0:
            print("Text extracted successfully!")
            print(f"First 500 characters: {result.get('text', '')[:500]}...")
        else:
            print("No text extracted - this is the problem!")
            
        if result.get('citations'):
            print("Citations found:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
        
        if result.get('case_names'):
            print("Case names found:")
            for i, case_name in enumerate(result['case_names'], 1):
                print(f"  {i}. {case_name}")
        
        return result.get('success', False) and result.get('text_length', 0) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("PDF URL Test")
    print("=" * 50)
    
    success = test_pdf_url()
    
    if success:
        print("\n🎉 Test PASSED - PDF extraction is working!")
    else:
        print("\n💥 Test FAILED - PDF extraction needs work")
    
    print("\nTest completed.") 