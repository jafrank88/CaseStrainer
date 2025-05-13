"""
Supreme Court Brief Downloader

This script downloads Supreme Court briefs from the Justice Department website.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Constants
BRIEFS_DIR = "downloaded_briefs"
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"
MAX_BRIEFS = 100  # Maximum number of briefs to download
BASE_URL = "https://www.justice.gov/osg/supreme-court-briefs"
SEARCH_URL = "https://www.justice.gov/osg/supreme-court-briefs?text=&sc_term=All&type=All&subject=All&order=field_date&sort=desc&page="

# Create directories if they don't exist
if not os.path.exists(BRIEFS_DIR):
    os.makedirs(BRIEFS_DIR)

def load_processed_briefs():
    """Load the list of already processed briefs."""
    if os.path.exists(PROCESSED_BRIEFS_CACHE):
        try:
            with open(PROCESSED_BRIEFS_CACHE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading processed briefs cache: {e}")
    return []

def save_processed_briefs(processed_briefs):
    """Save the list of processed briefs."""
    try:
        with open(PROCESSED_BRIEFS_CACHE, 'w') as f:
            json.dump(processed_briefs, f)
    except Exception as e:
        print(f"Error saving processed briefs cache: {e}")

def get_brief_urls(page=0, max_pages=10):
    """Get brief URLs from the Justice Department website."""
    print(f"Getting brief URLs from page {page}...")
    
    brief_urls = []
    
    try:
        # Set up user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        url = f"{SEARCH_URL}{page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error getting brief URLs: {response.status_code}")
            return brief_urls
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all PDF links
        pdf_links = soup.find_all('a', href=lambda href: href and href.endswith('?inline'))
        
        for link in pdf_links:
            brief_url = urljoin(BASE_URL, link['href'])
            brief_urls.append(brief_url)
        
        # If we need more briefs and haven't reached the max pages, get more
        if len(brief_urls) < MAX_BRIEFS and page < max_pages - 1:
            time.sleep(random.uniform(1, 3))  # Add a small delay
            brief_urls.extend(get_brief_urls(page + 1, max_pages))
        
        return brief_urls
    
    except Exception as e:
        print(f"Error getting brief URLs: {e}")
        traceback.print_exc()
        return brief_urls

def download_brief(brief_url):
    """Download a brief from a URL."""
    print(f"Downloading brief: {brief_url}")
    
    try:
        # Set up user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(brief_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error downloading brief: {response.status_code}")
            return None
        
        # Generate a filename based on the URL
        filename = os.path.join(BRIEFS_DIR, os.path.basename(brief_url).replace('?inline', '.pdf'))
        
        # Save the brief
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved brief to {filename}")
        return filename
    
    except Exception as e:
        print(f"Error downloading brief: {e}")
        traceback.print_exc()
        return None

def main():
    """Main function to download briefs."""
    print("Starting Supreme Court Brief Downloader...")
    
    # Load processed briefs
    processed_briefs = load_processed_briefs()
    print(f"Loaded {len(processed_briefs)} previously processed briefs")
    
    # Get brief URLs
    brief_urls = get_brief_urls()
    print(f"Found {len(brief_urls)} brief URLs")
    
    # Limit to MAX_BRIEFS
    brief_urls = brief_urls[:MAX_BRIEFS]
    
    # Process each brief
    downloaded_briefs = []
    for brief_url in brief_urls:
        # Skip if already processed
        if brief_url in processed_briefs:
            print(f"Skipping already processed brief: {brief_url}")
            continue
        
        # Download the brief
        brief_path = download_brief(brief_url)
        if brief_path:
            downloaded_briefs.append(brief_path)
            processed_briefs.append(brief_url)
            save_processed_briefs(processed_briefs)
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(random.uniform(1, 3))
        
        # Check if we've downloaded enough briefs
        if len(downloaded_briefs) >= MAX_BRIEFS:
            break
    
    print(f"Finished downloading {len(downloaded_briefs)} briefs")
    print("You can now use CaseStrainer's File Tool to analyze these briefs.")
    print(f"The briefs are located in the {BRIEFS_DIR} directory.")

if __name__ == "__main__":
    main()
