#!/usr/bin/env python3
"""
Test the CitationService.extract_text_from_input method that the API actually uses
"""

import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from api.services.citation_service import CitationService

def main():
    url = "https://www.courts.wa.gov/opinions/pdf/D2%2060382-9-II%20Published%20Opinion.pdf"
    
    print("=== Testing CitationService.extract_text_from_input (API method) ===")
    try:
        service = CitationService()
        input_data = {'type': 'url', 'url': url}
        result = service.extract_text_from_input(input_data)
        
        print(f"Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"Success: {result.get('success')}")
            print(f"Error: {result.get('error')}")
            text = result.get('text', '')
            print(f"Text length: {len(text)}")
            print(f"Text preview: {text[:200]}...")
            
            if len(text.strip()) < 10:
                print("❌ TEXT TOO SHORT - This would trigger the API error!")
            else:
                print("✅ Text length sufficient for API")
        else:
            print(f"Unexpected result type: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
