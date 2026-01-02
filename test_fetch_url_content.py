#!/usr/bin/env python3
"""
Test the fetch_url_content function that the API uses
"""

import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from progress_manager import fetch_url_content

def main():
    url = "https://www.courts.wa.gov/opinions/pdf/D2%2060382-9-II%20Published%20Opinion.pdf"
    
    print("=== Testing fetch_url_content (API method) ===")
    try:
        content = fetch_url_content(url)
        print(f"Success! Extracted {len(content)} characters")
        print(f"Content preview: {content[:200]}...")
        
        if len(content.strip()) < 10:
            print("❌ CONTENT TOO SHORT - This would trigger the API error!")
        else:
            print("✅ Content length sufficient for API")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
