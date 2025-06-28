#!/usr/bin/env python3
"""
Test script to compare URL processing vs text processing.
"""

from src.document_processing import process_document

def test_url_vs_text():
    """Compare URL processing vs text processing."""
    print("Testing URL vs Text Processing")
    print("=" * 50)
    
    # Test URL processing
    print("\n1. Testing URL processing:")
    print("-" * 30)
    url = "https://www.law.cornell.edu/supct/html/02-102.ZS.html"
    
    try:
        url_result = process_document(url=url, extract_case_names=True)
        print(f"URL Success: {url_result.get('success', False)}")
        print(f"URL Citations: {len(url_result.get('citations', []))}")
        print(f"URL Case Names: {len(url_result.get('case_names', []))}")
        print(f"URL Text Length: {url_result.get('text_length', 0)}")
        
        if url_result.get('citations'):
            print("Sample URL citations:")
            for i, citation in enumerate(url_result.get('citations', [])[:3]):
                print(f"  {i+1}. {citation.get('citation', 'N/A')}")
        
    except Exception as e:
        print(f"URL processing error: {e}")
    
    # Test text processing with similar content
    print("\n2. Testing text processing:")
    print("-" * 30)
    
    # Sample text with citations
    text_content = """
    This document contains citations like Brown v. Board of Education, 347 U.S. 483 (1954).
    Another citation: Roe v. Wade, 410 U.S. 113 (1973).
    Washington case: State v. Smith, 123 Wn.2d 456 (1994).
    """
    
    try:
        text_result = process_document(content=text_content, extract_case_names=True)
        print(f"Text Success: {text_result.get('success', False)}")
        print(f"Text Citations: {len(text_result.get('citations', []))}")
        print(f"Text Case Names: {len(text_result.get('case_names', []))}")
        print(f"Text Text Length: {text_result.get('text_length', 0)}")
        
        if text_result.get('citations'):
            print("Sample text citations:")
            for i, citation in enumerate(text_result.get('citations', [])[:3]):
                print(f"  {i+1}. {citation.get('citation', 'N/A')}")
        
    except Exception as e:
        print(f"Text processing error: {e}")
    
    # Test with the actual text content from the URL
    print("\n3. Testing with actual URL content:")
    print("-" * 30)
    
    if url_result.get('success') and url_result.get('text_length', 0) > 0:
        # Use the first 1000 characters from the URL content
        url_text = url_result.get('text', '')[:1000] if 'text' in url_result else ''
        
        try:
            url_text_result = process_document(content=url_text, extract_case_names=True)
            print(f"URL Text Success: {url_text_result.get('success', False)}")
            print(f"URL Text Citations: {len(url_text_result.get('citations', []))}")
            print(f"URL Text Case Names: {len(url_text_result.get('case_names', []))}")
            print(f"URL Text Length: {url_text_result.get('text_length', 0)}")
            
            if url_text_result.get('citations'):
                print("Sample URL text citations:")
                for i, citation in enumerate(url_text_result.get('citations', [])[:3]):
                    print(f"  {i+1}. {citation.get('citation', 'N/A')}")
            
        except Exception as e:
            print(f"URL text processing error: {e}")
    
    # Compare the results
    print("\n4. Comparison Summary:")
    print("-" * 30)
    print(f"URL processing: {len(url_result.get('citations', []))} citations")
    print(f"Text processing: {len(text_result.get('citations', []))} citations")
    
    if url_result.get('success') and text_result.get('success'):
        if len(url_result.get('citations', [])) > len(text_result.get('citations', [])):
            print("URL processing found more citations than text processing.")
            print("Possible reasons:")
            print("- URL content is richer/more complete")
            print("- Text processing has different extraction logic")
            print("- URL content has better formatting")
        elif len(url_result.get('citations', [])) < len(text_result.get('citations', [])):
            print("Text processing found more citations than URL processing.")
        else:
            print("Both methods found the same number of citations.")

if __name__ == "__main__":
    test_url_vs_text() 