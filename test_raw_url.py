#!/usr/bin/env python3
"""
Test raw URL extraction without HTML cleaning
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.services.citation_service import CitationService

def test_raw_url():
    """Test raw URL extraction"""
    
    service = CitationService()
    url = "https://supreme.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing raw URL: {url}")
    
    # Temporarily modify the service to skip HTML cleaning
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    
    # Retry strategy for reliability
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Fetch with timeout and size limit
    response = session.get(
        url,
        timeout=10,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        stream=True
    )
    
    # Download content
    content = ""
    downloaded = 0
    max_size = 1024 * 1024  # 1MB max
    
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            content += chunk
            downloaded += len(chunk.encode('utf-8'))
            if downloaded > max_size:
                print(f"Content exceeded size limit: {downloaded} bytes")
                break
    
    print(f"Downloaded {downloaded} bytes")
    
    # Check content type
    content_type = response.headers.get('content-type', '')
    print(f"Content-Type: {content_type}")
    
    # Extract text without cleaning
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find largest div
    all_divs = soup.find_all('div')
    largest_div = None
    max_length = 0
    
    for i, div in enumerate(all_divs):
        text = div.get_text().strip()
        text = ' '.join(text.split())
        if len(text) > max_length and len(text) > 1000:
            max_length = len(text)
            largest_div = div
            print(f"Div {i}: {len(text)} chars")
    
    if largest_div:
        raw_text = largest_div.get_text()
        print(f"\nRaw text from largest div: {len(raw_text)} characters")
        print(f"First 500 chars: {raw_text[:500]}")
        
        # Check for legal citations
        import re
        citations = re.findall(r'390\s*U\.S\.\s*747', raw_text)
        print(f"\nFound citations: {len(citations)}")
        
        # Check if it would be sync or async
        if len(raw_text.encode('utf-8')) < 5120:
            print("✅ Would process synchronously")
        else:
            print("🔄 Would process asynchronously")

if __name__ == "__main__":
    test_raw_url()
