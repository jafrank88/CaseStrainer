#!/usr/bin/env python
"""
Script to download briefs from the Washington Courts website and process them through the CaseStrainer tool
to identify unconfirmed citations.
"""
import os
import sys
import requests
import time
import json
import re
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import argparse

# Number of briefs to process
MAX_BRIEFS = 100

# Directory to save downloaded briefs
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloaded_briefs')

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# URLs for Washington Courts website
BASE_URL = "https://www.courts.wa.gov"
SUPREME_COURT_BRIEFS_URL = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A08"
DIV1_BRIEFS_URL = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A01"
DIV2_BRIEFS_URL = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A02"
DIV3_BRIEFS_URL = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A03"

# Function to download a brief
def download_brief(brief_url, output_path):
    """Download a brief from the Washington Courts website."""
    try:
        try:
        response = requests.get(brief_url, stream=True, timeout=30)
    except requests.Timeout:
        print(f"Timeout occurred while downloading {brief_url}")
        return None
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {os.path.basename(output_path)}")
        return output_path
    except Exception as e:
        print(f"Error downloading {brief_url}: {e}")
        return None

# Function to extract brief links from a page
def extract_brief_links(url):
    """Extract links to briefs from a Washington Courts page."""
    try:
        print(f"Fetching briefs from {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Find all links to PDF files
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.endswith('.pdf') and '/content/Briefs/' in href:
                full_url = urljoin(BASE_URL, href)
                links.append(full_url)
        
        # If no links found, try a different approach - look for specific patterns
        if not links:
            print("No links found with standard approach, trying alternative method...")
            # Look for links containing PDF patterns
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if '.pdf' in href.lower():
                    full_url = urljoin(BASE_URL, href)
                    links.append(full_url)
        
        print(f"Found {len(links)} brief links on {url}")
        return links
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        traceback.print_exc()
        return []

# Function to process a brief through CaseStrainer
def process_brief(file_path):
    """Process a brief through the CaseStrainer tool to identify unconfirmed citations."""
    try:
        # CaseStrainer API endpoint
        api_url = "http://0.0.0.0:5001/analyze"
        
        print(f"Processing file: {file_path}")
        # Check if file exists and is readable
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return None
            
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        
        if file_size == 0:
            print(f"File is empty: {file_path}")
            return None
        
        # Prepare the file for upload
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            
            # Make the request to the CaseStrainer API
            print(f"Sending file to CaseStrainer API at {api_url}")
            response = requests.post(api_url, files=files)
            
            # Check response status
            if response.status_code != 200:
                print(f"Error from API: {response.status_code} - {response.text}")
                return None
            
            # Get the analysis ID from the response
            try:
                result = response.json()
            except json.JSONDecodeError:
                print(f"Invalid JSON response: {response.text}")
                return None
                
            if result.get('status') != 'success':
                print(f"Error processing {file_path}: {result.get('message')}")
                return None
            
            analysis_id = result.get('analysis_id')
            print(f"Analysis started for {os.path.basename(file_path)} with ID: {analysis_id}")
        
        # Poll for analysis results
        status_url = f"http://0.0.0.0:5001/status?id={analysis_id}"
        max_attempts = 60  # Increased timeout
        attempts = 0
        
        while attempts < max_attempts:
            time.sleep(3)  # Wait 3 seconds between polls
            try:
                status_response = requests.get(status_url)
                status_response.raise_for_status()
                
                try:
                    status_result = status_response.json()
                except json.JSONDecodeError:
                    print(f"Invalid JSON in status response: {status_response.text}")
                    attempts += 1
                    continue
                
                # Check if analysis is complete
                if status_result.get('completed', False):
                    print(f"Analysis completed for {os.path.basename(file_path)}")
                    return status_result
                
                # Print progress
                progress = status_result.get('progress', 0)
                total_steps = status_result.get('total_steps', 1)
                message = status_result.get('message', '')
                print(f"Progress: {progress}/{total_steps} - {message}")
                
            except requests.RequestException as e:
                print(f"Error checking status: {e}")
            
            attempts += 1
        
        print(f"Timeout waiting for analysis of {file_path}")
        return None
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        traceback.print_exc()
        return None

# Function to extract unconfirmed citations from analysis results
def extract_unconfirmed_citations(analysis_result):
    """Extract unconfirmed citations from CaseStrainer analysis results."""
    if not analysis_result or 'results' not in analysis_result:
        return []
    
    unconfirmed = []
    results = analysis_result.get('results', {})
    
    # Extract citations from the results
    citation_results = results.get('citation_results', [])
    for citation in citation_results:
        if not citation.get('is_confirmed', False):
            unconfirmed.append({
                'citation_text': citation.get('citation_text', ''),
                'confidence': citation.get('confidence', 0),
                'explanation': citation.get('explanation', '')
            })
    
    return unconfirmed

# Main function
def main():
    """Main function to download and process briefs."""
    parser = argparse.ArgumentParser(description='Download and process briefs from Washington Courts website')
    parser.add_argument('--court', choices=['supreme', 'div1', 'div2', 'div3', 'all'], default='supreme',
                        help='Court to download briefs from (default: supreme)')
    parser.add_argument('--max-briefs', type=int, default=MAX_BRIEFS,
                        help=f'Maximum number of briefs to process (default: {MAX_BRIEFS})')
    parser.add_argument('--test-server', action='store_true',
                        help='Test if the CaseStrainer server is running')
    args = parser.parse_args()
    
    # Test if the CaseStrainer server is running
    if args.test_server:
        try:
            response = requests.get("http://0.0.0.0:5001/")
            print(f"CaseStrainer server is running. Status code: {response.status_code}")
            return
        except requests.RequestException as e:
            print(f"CaseStrainer server is not running: {e}")
            return
    
    # Determine which court(s) to process
    courts = []
    if args.court == 'all':
        courts = [
            ('supreme', SUPREME_COURT_BRIEFS_URL),
            ('div1', DIV1_BRIEFS_URL),
            ('div2', DIV2_BRIEFS_URL),
            ('div3', DIV3_BRIEFS_URL)
        ]
    else:
        if args.court == 'supreme':
            courts = [('supreme', SUPREME_COURT_BRIEFS_URL)]
        elif args.court == 'div1':
            courts = [('div1', DIV1_BRIEFS_URL)]
        elif args.court == 'div2':
            courts = [('div2', DIV2_BRIEFS_URL)]
        elif args.court == 'div3':
            courts = [('div3', DIV3_BRIEFS_URL)]
    
    # Create subdirectories for each court
    for court_name, _ in courts:
        court_dir = os.path.join(DOWNLOAD_DIR, court_name)
        os.makedirs(court_dir, exist_ok=True)
    
    # Download and process briefs
    all_unconfirmed_citations = {}
    brief_count = 0
    
    for court_name, court_url in courts:
        if brief_count >= args.max_briefs:
            break
        
        print(f"\nProcessing briefs from {court_name.upper()} court...")
        court_dir = os.path.join(DOWNLOAD_DIR, court_name)
        
        # Extract brief links
        brief_links = extract_brief_links(court_url)
        
        if not brief_links:
            print(f"No brief links found for {court_name}. Trying direct approach...")
            # Try a direct approach for Supreme Court briefs
            if court_name == 'supreme':
                # Hardcoded example briefs from the Supreme Court
                brief_links = [
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20Answer%20to%20Petition%20for%20Review.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20Petition%20for%20Review.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Appellant%20Brief.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Respondent%20Brief.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20Petitioners%20Supplemental%20Brief.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20Amicus%20-%20Fred%20T%20Korematsu%20Center.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Pro%20Se%20Stmt%20Add%27l%20Grounds.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Pro%20Se%20Stmt%20Add%27l%20Grounds%2010-29-20.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Pro%20Se%20Stmt%20Add%27l%20Grounds%208-27-20.pdf",
                    "https://www.courts.wa.gov/content/Briefs/A08/999597%20Respondent%20Answer%20to%20Amicus.pdf"
                ]
                print(f"Added {len(brief_links)} hardcoded brief links for Supreme Court")
        
        # Process each brief
        for link in brief_links:
            if brief_count >= args.max_briefs:
                break
            
            # Extract filename from URL
            filename = os.path.basename(link)
            output_path = os.path.join(court_dir, filename)
            
            # Download the brief
            print(f"\nDownloading brief {brief_count + 1}/{args.max_briefs}: {filename}")
            downloaded_path = download_brief(link, output_path)
            
            if downloaded_path:
                # Process the brief through CaseStrainer
                print(f"Processing brief: {filename}")
                analysis_result = process_brief(downloaded_path)
                
                if analysis_result:
                    # Extract unconfirmed citations
                    unconfirmed = extract_unconfirmed_citations(analysis_result)
                    
                    if unconfirmed:
                        all_unconfirmed_citations[filename] = unconfirmed
                        print(f"Found {len(unconfirmed)} unconfirmed citations in {filename}")
                    else:
                        print(f"No unconfirmed citations found in {filename}")
            
            brief_count += 1
            
            # Save intermediate results after each brief
            intermediate_results_file = os.path.join(DOWNLOAD_DIR, 'unconfirmed_citations_intermediate.json')
            with open(intermediate_results_file, 'w', encoding='utf-8') as f:
                json.dump(all_unconfirmed_citations, f, indent=2)
    
    # Save results to a JSON file
    results_file = os.path.join(DOWNLOAD_DIR, 'unconfirmed_citations.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_unconfirmed_citations, f, indent=2)
    
    # Print summary
    total_unconfirmed = sum(len(citations) for citations in all_unconfirmed_citations.values())
    print(f"\n=== SUMMARY ===")
    print(f"Processed {brief_count} briefs")
    print(f"Found {total_unconfirmed} unconfirmed citations in {len(all_unconfirmed_citations)} briefs")
    print(f"Results saved to {results_file}")
    
    # Print all unconfirmed citations
    print("\n=== UNCONFIRMED CITATIONS ===")
    for brief, citations in all_unconfirmed_citations.items():
        print(f"\nBrief: {brief}")
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {citation['citation_text']}")
            print(f"     Confidence: {citation['confidence']}")
            print(f"     Explanation: {citation['explanation']}")

if __name__ == "__main__":
    main()
