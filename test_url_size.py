#!/usr/bin/env python3
"""
Test how much text a URL extracts
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.services.citation_service import CitationService

def test_url_text_size():
    """Test how much text a URL extracts"""
    
    service = CitationService()
    url = "https://supreme.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing URL: {url}")
    
    # Extract text from URL
    text = service._fetch_url_content(url)
    
    if text:
        print(f"✅ Extracted {len(text)} characters")
        print(f"📏 Size: {len(text.encode('utf-8'))} bytes")
        print(f"🔍 Sync threshold: {service.SYNC_THRESHOLD} bytes")
        
        if len(text.encode('utf-8')) < service.SYNC_THRESHOLD:
            print("✅ Would process synchronously")
        else:
            print("🔄 Would process asynchronously (too large)")
            
        print(f"\n📝 Text preview (first 500 chars):")
        print(text[:500])
    else:
        print("❌ Failed to extract text")

if __name__ == "__main__":
    test_url_text_size()
