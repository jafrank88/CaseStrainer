#!/usr/bin/env python3
"""
Test simple US citation detection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_us_citation():
    """Test simple US citation detection."""
    print("Testing simple US citation detection...")
    
    try:
        # Import the document processing
        from src.document_processing_unified import process_document
        
        # Test with a simple US citation
        test_text = "347 U.S. 483"
        
        print(f"Processing text: {test_text}")
        
        # Process the text
        result = process_document(content=test_text, extract_case_names=True)
        
        print(f"Success: {result.get('success')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Case names found: {len(result.get('case_names', []))}")
        
        if result.get('citations'):
            print("Citations:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
                print(f"     Verified: {citation.get('verified', 'N/A')}")
                print(f"     Case name: {citation.get('case_name', 'N/A')}")
        
        if result.get('case_names'):
            print("Case names:")
            for i, case_name in enumerate(result['case_names'], 1):
                print(f"  {i}. {case_name}")
        
        return len(result.get('citations', [])) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_us_citation()
    if success:
        print("\n🎉 US citation detection test passed!")
    else:
        print("\n❌ US citation detection test failed!")
        sys.exit(1) 