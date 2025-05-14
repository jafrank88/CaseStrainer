"""
Supreme Court Brief Downloader (Improved)

This script downloads Supreme Court briefs from the Justice Department website
and saves them with unique filenames based on the docket number and brief type.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# Constants
BRIEFS_DIR = "downloaded_briefs"
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"
BRIEFS_CSV = "supreme_court_briefs.csv"
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

def get_brief_info(page=0, max_pages=10):
    """Get brief information from the Justice Department website."""
    print(f"Getting brief information from page {page}...")
    
    briefs_info = []
    
    try:
        # Set up user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        url = f"{SEARCH_URL}{page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error getting brief information: {response.status_code}")
            return briefs_info
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all table rows with brief information
        rows = soup.find_all('tr')
        
        for row in rows:
            # Skip header rows
            if row.find('th'):
                continue
                
            # Extract cells
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
                
            # Extract brief information
            try:
                docket_number = cells[1].text.strip() if len(cells) > 1 else "Unknown"
                caption = cells[2].text.strip() if len(cells) > 2 else "Unknown"
                brief_type = cells[3].text.strip() if len(cells) > 3 else "Unknown"
                filing_date = cells[4].text.strip() if len(cells) > 4 else "Unknown"
                
                # Find the PDF link
                pdf_link = None
                link_cell = cells[2] if len(cells) > 2 else None
                if link_cell:
                    pdf_a_tag = link_cell.find_next('a', href=lambda href: href and href.endswith('?inline'))
                    if pdf_a_tag:
                        pdf_link = urljoin(BASE_URL, pdf_a_tag['href'])
                
                if pdf_link:
                    # Extract media ID from the URL for unique filename
                    parsed_url = urlparse(pdf_link)
                    path_parts = parsed_url.path.split('/')
                    media_id = path_parts[-2] if len(path_parts) > 2 else "unknown"
                    
                    briefs_info.append({
                        'docket_number': docket_number,
                        'caption': caption,
                        'brief_type': brief_type,
                        'filing_date': filing_date,
                        'pdf_url': pdf_link,
                        'media_id': media_id
                    })
            except Exception as e:
                print(f"Error extracting brief information: {e}")
                continue
        
        # If we need more briefs and haven't reached the max pages, get more
        if len(briefs_info) < MAX_BRIEFS and page < max_pages - 1:
            time.sleep(random.uniform(1, 3))  # Add a small delay
            briefs_info.extend(get_brief_info(page + 1, max_pages))
        
        return briefs_info
    
    except Exception as e:
        print(f"Error getting brief information: {e}")
        traceback.print_exc()
        return briefs_info

def download_brief(brief_info):
    """Download a brief from a URL."""
    pdf_url = brief_info['pdf_url']
    print(f"Downloading brief: {brief_info['caption']} ({pdf_url})")
    
    try:
        # Set up user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(pdf_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error downloading brief: {response.status_code}")
            return None
        
        # Generate a unique filename based on the media ID and caption
        safe_caption = "".join(c if c.isalnum() else "_" for c in brief_info['caption'][:30])
        filename = f"{brief_info['media_id']}_{safe_caption}.pdf"
        filepath = os.path.join(BRIEFS_DIR, filename)
        
        # Save the brief
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved brief to {filepath}")
        
        # Update brief_info with local filepath
        brief_info['local_path'] = filepath
        return brief_info
    
    except Exception as e:
        print(f"Error downloading brief: {e}")
        traceback.print_exc()
        return None

def create_briefs_csv(briefs_info):
    """Create a CSV file with brief information."""
    print(f"Creating CSV file with {len(briefs_info)} briefs...")
    
    try:
        with open(BRIEFS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Docket Number', 'Caption', 'Brief Type', 'Filing Date', 'PDF URL', 'Local Path', 'Analyzed', 'Unverified Citations'])
            
            # Write brief information
            for brief in briefs_info:
                writer.writerow([
                    brief.get('docket_number', ''),
                    brief.get('caption', ''),
                    brief.get('brief_type', ''),
                    brief.get('filing_date', ''),
                    brief.get('pdf_url', ''),
                    brief.get('local_path', ''),
                    'No',
                    '0'
                ])
        
        print(f"Created CSV file: {BRIEFS_CSV}")
    
    except Exception as e:
        print(f"Error creating CSV file: {e}")
        traceback.print_exc()

def main():
    """Main function to download briefs."""
    print("Starting Supreme Court Brief Downloader (Improved)...")
    
    # Load processed briefs
    processed_briefs = load_processed_briefs()
    print(f"Loaded {len(processed_briefs)} previously processed briefs")
    
    # Get brief information
    briefs_info = get_brief_info()
    print(f"Found {len(briefs_info)} briefs")
    
    # Limit to MAX_BRIEFS
    briefs_info = briefs_info[:MAX_BRIEFS]
    
    # Download each brief
    downloaded_briefs = []
    for brief_info in briefs_info:
        # Skip if already processed
        if brief_info['pdf_url'] in processed_briefs:
            print(f"Skipping already processed brief: {brief_info['caption']}")
            continue
        
        # Download the brief
        downloaded_brief = download_brief(brief_info)
        if downloaded_brief:
            downloaded_briefs.append(downloaded_brief)
            processed_briefs.append(brief_info['pdf_url'])
            save_processed_briefs(processed_briefs)
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(random.uniform(1, 3))
        
        # Check if we've downloaded enough briefs
        if len(downloaded_briefs) >= MAX_BRIEFS:
            break
    
    # Create CSV file with brief information
    create_briefs_csv(downloaded_briefs)
    
    print(f"Finished downloading {len(downloaded_briefs)} briefs")
    print("You can now use CaseStrainer's File Tool to analyze these briefs.")
    print(f"The briefs are located in the {BRIEFS_DIR} directory.")
    print(f"Brief information is available in {BRIEFS_CSV}")

if __name__ == "__main__":
    main()
