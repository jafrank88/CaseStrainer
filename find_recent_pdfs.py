#!/usr/bin/env python3
"""Find recent PDF URLs from Washington State Courts"""

import requests
from bs4 import BeautifulSoup
import re

def find_recent_pdfs():
    """Find recent PDF URLs from Washington State Courts opinions"""
    
    url = "https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.recent"
    
    try:
        print(f"Fetching recent opinions from: {url}")
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links that end with .pdf
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf'):
                # Make absolute URL if needed
                if href.startswith('/'):
                    href = 'https://www.courts.wa.gov' + href
                pdf_links.append(href)
        
        print(f"\nFound {len(pdf_links)} PDF links:")
        for i, pdf_url in enumerate(pdf_links[:10], 1):
            print(f"  {i}. {pdf_url}")
        
        # Test the first PDF to see if it's accessible
        if pdf_links:
            test_url = pdf_links[0]
            print(f"\nTesting first PDF: {test_url}")
            
            try:
                head_response = requests.head(test_url, timeout=10, verify=False)
                print(f"Status: {head_response.status_code}")
                print(f"Content-Type: {head_response.headers.get('Content-Type', 'N/A')}")
                print(f"Content-Length: {head_response.headers.get('Content-Length', 'N/A')}")
                
                if head_response.status_code == 200:
                    print("✅ PDF is accessible!")
                    return test_url
                else:
                    print("❌ PDF not accessible")
            except Exception as e:
                print(f"❌ Error testing PDF: {e}")
        
        return None
        
    except Exception as e:
        print(f"Error fetching recent opinions: {e}")
        return None

if __name__ == "__main__":
    pdf_url = find_recent_pdfs()
    if pdf_url:
        print(f"\nUse this URL for testing: {pdf_url}")
