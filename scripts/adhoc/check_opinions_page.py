#!/usr/bin/env python3
"""Check Washington State Courts opinions page structure"""

import requests
from bs4 import BeautifulSoup
import re

def check_page_structure():
    """Check the structure of the recent opinions page"""
    
    url = "https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.recent"
    
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Look for any patterns that might contain PDF URLs
        text = response.text
        
        # Search for .pdf patterns
        pdf_patterns = re.findall(r'[^"\s]*\.pdf[^"\s]*?|/[^"\s]*\.pdf', text, re.IGNORECASE)
        
        print(f"\nFound {len(pdf_patterns)} potential PDF patterns:")
        for i, pattern in enumerate(pdf_patterns[:10], 1):
            print(f"  {i}. {pattern}")
        
        # Also check for opinion links (they might be dynamic)
        soup = BeautifulSoup(text, 'html.parser')
        
        # Look for tables or divs that might contain opinions
        tables = soup.find_all('table')
        print(f"\nFound {len(tables)} tables")
        
        # Look for links with specific patterns
        all_links = soup.find_all('a', href=True)
        print(f"\nFound {len(all_links)} total links")
        
        opinion_links = []
        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)
            if 'opinion' in href.lower() or 'opinions' in href.lower() or '.pdf' in href.lower():
                opinion_links.append((href, text))
        
        print(f"\nFound {len(opinion_links)} opinion-related links:")
        for i, (href, text) in enumerate(opinion_links[:10], 1):
            print(f"  {i}. {href} -> {text[:50]}")
        
        # Check for form data or JavaScript that might load opinions
        scripts = soup.find_all('script')
        print(f"\nFound {len(scripts)} script tags")
        
        # Look for any forms that might submit for opinions
        forms = soup.find_all('form')
        print(f"\nFound {len(forms)} forms")
        
        return text
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    check_page_structure()
