#!/usr/bin/env python3
"""
Simple test to verify citation extraction is working
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_citation_extraction():
    """Test citation extraction with simple text"""
    
    test_text = "The court in Smith v. Jones, 123 U.S. 456 (2020) held that..."
    
    print("Testing citation extraction...")
    print(f"Test text: {test_text}")
    
    try:
        # Test the document processing
        from src.document_processing import process_document
        
        result = process_document(content=test_text, extract_case_names=True)
        
        print(f"Result: {result}")
        print(f"Success: {result.get('success', False)}")
        print(f"Citations: {len(result.get('citations', []))}")
        print(f"Case names: {len(result.get('case_names', []))}")
        
        if result.get('citations'):
            print("Citations found:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
        
        if result.get('case_names'):
            print("Case names found:")
            for i, case_name in enumerate(result['case_names'], 1):
                print(f"  {i}. {case_name}")
        
        return result.get('success', False) and len(result.get('citations', [])) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Simple Citation Extraction Test")
    print("=" * 50)
    
    success = test_citation_extraction()
    
    if success:
        print("\n🎉 Test PASSED - Citation extraction is working!")
    else:
        print("\n💥 Test FAILED - Citation extraction needs work")
    
    print("\nTest completed.") 