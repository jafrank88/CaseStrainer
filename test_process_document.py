#!/usr/bin/env python3
"""
Test script to directly test the process_document function.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_process_document():
    """Test the process_document function directly."""
    print("=== Testing process_document Function ===\n")
    
    try:
        from src.document_processing_unified import process_document
        
        # Test 1: Direct text processing
        print("1. Testing direct text processing...")
        test_text = "410 U.S. 113"
        result = process_document(content=test_text, extract_case_names=True)
        
        print(f"   Success: {result.get('success', False)}")
        print(f"   Citations found: {len(result.get('citations', []))}")
        print(f"   Case names found: {len(result.get('case_names', []))}")
        
        if result.get('citations'):
            for i, citation in enumerate(result['citations'], 1):
                print(f"   Citation {i}: {citation.get('citation', 'N/A')} -> {citation.get('verified', 'N/A')}")
        
        # Test 2: URL processing
        print("\n2. Testing URL processing...")
        test_url = "https://supreme.justia.com/cases/federal/us/410/113/"
        result = process_document(url=test_url, extract_case_names=True)
        
        print(f"   Success: {result.get('success', False)}")
        print(f"   Citations found: {len(result.get('citations', []))}")
        print(f"   Case names found: {len(result.get('case_names', []))}")
        print(f"   Text length: {result.get('text_length', 0)}")
        
        if result.get('citations'):
            for i, citation in enumerate(result['citations'], 1):
                print(f"   Citation {i}: {citation.get('citation', 'N/A')} -> {citation.get('verified', 'N/A')}")
        else:
            print("   ❌ No citations found from URL!")
            print(f"   Error: {result.get('error', 'None')}")
        
        # Test 3: Check what text was extracted from URL
        print("\n3. Checking extracted text from URL...")
        from src.document_processing_unified import extract_text_from_url
        text_result = extract_text_from_url(test_url)
        
        if isinstance(text_result, dict):
            text = text_result.get('text', '')
            status = text_result.get('status', 'unknown')
            error = text_result.get('error', '')
        else:
            text = text_result
            status = 'success'
            error = ''
        
        print(f"   Status: {status}")
        print(f"   Error: {error}")
        print(f"   Text length: {len(text)}")
        print(f"   Text sample (first 500 chars): {text[:500]}...")
        
        # Test 4: Extract citations from the extracted text
        print("\n4. Testing citation extraction from extracted text...")
        if text:
            result = process_document(content=text, extract_case_names=True)
            print(f"   Success: {result.get('success', False)}")
            print(f"   Citations found: {len(result.get('citations', []))}")
            
            if result.get('citations'):
                for i, citation in enumerate(result['citations'], 1):
                    print(f"   Citation {i}: {citation.get('citation', 'N/A')} -> {citation.get('verified', 'N/A')}")
            else:
                print("   ❌ No citations found from extracted text!")
        
    except Exception as e:
        print(f"❌ Error testing process_document: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the test."""
    test_process_document()
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 