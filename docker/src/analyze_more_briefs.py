#!/usr/bin/env python
"""
Script to download and analyze briefs from multiple Washington Courts divisions
to find unconfirmed citations.
"""
import os
import sys
import requests
import json
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URLs for Washington Courts
BASE_URL = "https://www.courts.wa.gov"
COURTS = {
    'supreme': "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A08",
    'div1': "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A01",
    'div2': "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A02",
    'div3': "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A03"
}

# Directory to save downloaded briefs
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloaded_briefs')

# Create download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Hardcoded example briefs for each court (in case web scraping fails)
HARDCODED_BRIEFS = {
    'supreme': [
        "https://www.courts.wa.gov/content/Briefs/A08/999597%20Answer%20to%20Petition%20for%20Review.pdf",
        "https://www.courts.wa.gov/content/Briefs/A08/999597%20Petition%20for%20Review.pdf",
        "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Appellant%20Brief.pdf",
        "https://www.courts.wa.gov/content/Briefs/A08/999597%20COA%2099959-7%20Respondent%20Brief.pdf",
        "https://www.courts.wa.gov/content/Briefs/A08/999597%20Petitioners%20Supplemental%20Brief.pdf"
    ],
    'div1': [
        "https://www.courts.wa.gov/content/Briefs/A01/814773%20Appellant's%20Opening%20Brief.pdf",
        "https://www.courts.wa.gov/content/Briefs/A01/814773%20Respondent's%20Brief.pdf",
        "https://www.courts.wa.gov/content/Briefs/A01/814773%20Reply%20Brief%20of%20Appellant.pdf"
    ],
    'div2': [
        "https://www.courts.wa.gov/content/Briefs/A02/559209%20Brief%20of%20Appellant.pdf",
        "https://www.courts.wa.gov/content/Briefs/A02/559209%20Brief%20of%20Respondent.pdf",
        "https://www.courts.wa.gov/content/Briefs/A02/559209%20Reply%20Brief%20of%20Appellant.pdf"
    ],
    'div3': [
        "https://www.courts.wa.gov/content/Briefs/A03/379384%20Brief%20of%20Appellant.pdf",
        "https://www.courts.wa.gov/content/Briefs/A03/379384%20Brief%20of%20Respondent.pdf",
        "https://www.courts.wa.gov/content/Briefs/A03/379384%20Reply%20Brief%20of%20Appellant.pdf"
    ]
}

def extract_brief_links(url, court_id):
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
        
        # If still no links found, use hardcoded briefs
        if not links and court_id in HARDCODED_BRIEFS:
            print(f"Using hardcoded briefs for {court_id}")
            links = HARDCODED_BRIEFS[court_id]
        
        return links
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        # Fall back to hardcoded briefs
        if court_id in HARDCODED_BRIEFS:
            print(f"Falling back to hardcoded briefs for {court_id}")
            return HARDCODED_BRIEFS[court_id]
        return []

def download_brief(url, output_path):
    """Download a brief from the Washington Courts website."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {os.path.basename(output_path)}")
        return output_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def analyze_brief(file_path):
    """Analyze a brief using the CaseStrainer API."""
    try:
        print(f"Analyzing brief: {file_path}")
        
        # Check if file exists and is readable
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return None
            
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        
        if file_size == 0:
            print(f"File is empty: {file_path}")
            return None
        
        # CaseStrainer API endpoint
        api_url = "http://0.0.0.0:5001/analyze"
        
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
            print(f"Analysis started with ID: {analysis_id}")
        
        # Poll for analysis results
        status_url = f"http://0.0.0.0:5001/status?id={analysis_id}"
        max_attempts = 60
        attempts = 0
        
        while attempts < max_attempts:
            time.sleep(3)
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
                    
                    # Save the results to a file
                    results_file = f"{os.path.splitext(file_path)[0]}_results.json"
                    with open(results_file, 'w', encoding='utf-8') as rf:
                        json.dump(status_result, rf, indent=2)
                    print(f"Results saved to {results_file}")
                    
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
        print(f"Error analyzing {file_path}: {e}")
        return None

def extract_unconfirmed_citations(analysis_result, source_path=None):
    """Extract unconfirmed citations from CaseStrainer analysis results."""
    if not analysis_result or 'citation_results' not in analysis_result:
        return []
    
    unconfirmed = []
    citation_results = analysis_result.get('citation_results', [])
    
    for citation in citation_results:
        # Check if citation is unconfirmed or hallucinated
        if not citation.get('court_listener_url') or citation.get('is_hallucinated', False):
            unconfirmed.append({
                'citation_text': citation.get('primary_citation', ''),
                'case_name': citation.get('case_name', ''),
                'confidence': citation.get('confidence', 0),
                'explanation': citation.get('explanation', ''),
                'source_path': source_path,  # Add the full source path for linking
                'hallucination_status': citation.get('hallucination_status', 'unconfirmed')
            })
    
    return unconfirmed

def main():
    """Main function to download and analyze briefs from multiple courts."""
    # Create directories for each court
    for court_id in COURTS:
        court_dir = os.path.join(DOWNLOAD_DIR, court_id)
        os.makedirs(court_dir, exist_ok=True)
    
    # Dictionary to store unconfirmed citations
    all_unconfirmed_citations = {}
    
    # Load existing unconfirmed citations if available
    existing_file = os.path.join(DOWNLOAD_DIR, 'all_unconfirmed_citations.json')
    if os.path.exists(existing_file):
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                all_unconfirmed_citations = json.load(f)
            print(f"Loaded {sum(len(citations) for citations in all_unconfirmed_citations.values())} existing unconfirmed citations")
        except Exception as e:
            print(f"Error loading existing citations: {e}")
    
    # Target number of unconfirmed citations
    target_citations = 100
    current_count = sum(len(citations) for citations in all_unconfirmed_citations.values())
    print(f"Currently have {current_count} unconfirmed citations. Target: {target_citations}")
    
    # Process briefs from each court until we reach the target
    court_cycle = 0
    while current_count < target_citations and court_cycle < 5:  # Limit to 5 cycles through all courts
        court_cycle += 1
        print(f"\n=== Starting court cycle {court_cycle} ===\n")
        
        for court_id, court_url in COURTS.items():
            if current_count >= target_citations:
                break
                
            print(f"\n=== Processing briefs from {court_id.upper()} court (Cycle {court_cycle}) ===\n")
            court_dir = os.path.join(DOWNLOAD_DIR, court_id)
            
            # Extract brief links
            brief_links = extract_brief_links(court_url, court_id)
            
            # Shuffle the links to get a diverse sample
            random.shuffle(brief_links)
            
            # Process up to 20 briefs from each court per cycle
            briefs_to_process = min(20, len(brief_links))
            for i, link in enumerate(brief_links[:briefs_to_process]):
                if current_count >= target_citations:
                    print(f"Reached target of {target_citations} unconfirmed citations!")
                    break
            # Extract filename from URL
            filename = os.path.basename(link)
            output_path = os.path.join(court_dir, filename)
            
            # Download the brief if it doesn't exist
            if not os.path.exists(output_path):
                print(f"\nDownloading brief {i+1}/5 from {court_id}: {filename}")
                downloaded_path = download_brief(link, output_path)
            else:
                print(f"\nBrief already exists: {filename}")
                downloaded_path = output_path
            
            if downloaded_path:
                # Check if results already exist
                results_file = f"{os.path.splitext(downloaded_path)[0]}_results.json"
                if os.path.exists(results_file):
                    print(f"Analysis results already exist: {os.path.basename(results_file)}")
                    with open(results_file, 'r', encoding='utf-8') as f:
                        analysis_result = json.load(f)
                else:
                    # Analyze the brief
                    analysis_result = analyze_brief(downloaded_path)
                
                if analysis_result:
                    # Extract unconfirmed citations with source path
                    unconfirmed = extract_unconfirmed_citations(analysis_result, downloaded_path)
                    
                    if unconfirmed:
                        all_unconfirmed_citations[filename] = unconfirmed
                        new_count = len(unconfirmed)
                        current_count += new_count
                        print(f"Found {new_count} unconfirmed citations in {filename}")
                        print(f"Total unconfirmed citations: {current_count}/{target_citations}")
                        
                        # Print unconfirmed citations
                        for i, citation in enumerate(unconfirmed, 1):
                            print(f"  {i}. {citation['citation_text']} - {citation['case_name']}")
                            print(f"     Confidence: {citation['confidence']}")
                            print(f"     Explanation: {citation['explanation']}")
                    else:
                        print(f"No unconfirmed citations found in {filename}")
            
            # Save intermediate results after each brief
            if all_unconfirmed_citations:
                intermediate_file = os.path.join(DOWNLOAD_DIR, 'all_unconfirmed_citations.json')
                with open(intermediate_file, 'w', encoding='utf-8') as f:
                    json.dump(all_unconfirmed_citations, f, indent=2)
                print(f"Saved {current_count} unconfirmed citations to {intermediate_file}")
                
                # Also save a flattened list for easier access
                flattened_citations = []
                for filename, citations in all_unconfirmed_citations.items():
                    for citation in citations:
                        citation['source_file'] = filename
                        flattened_citations.append(citation)
                
                flattened_file = os.path.join(DOWNLOAD_DIR, 'unconfirmed_citations_flat.json')
                with open(flattened_file, 'w', encoding='utf-8') as f:
                    json.dump(flattened_citations, f, indent=2)
    
    # Print final summary
    print("\n=== FINAL SUMMARY ===")
    total_unconfirmed = sum(len(citations) for citations in all_unconfirmed_citations.values())
    print(f"Found {total_unconfirmed} unconfirmed citations in {len(all_unconfirmed_citations)} briefs")
    
    # Save final results in both formats
    if all_unconfirmed_citations:
        # Save by-file format
        results_file = os.path.join(DOWNLOAD_DIR, 'all_unconfirmed_citations.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_unconfirmed_citations, f, indent=2)
        print(f"Results by file saved to {results_file}")
        
        # Save flattened format for the web interface
        flattened_citations = []
        for filename, citations in all_unconfirmed_citations.items():
            for citation in citations:
                citation['source_file'] = filename
                flattened_citations.append(citation)
        
        flattened_file = os.path.join(DOWNLOAD_DIR, 'unconfirmed_citations_flat.json')
        with open(flattened_file, 'w', encoding='utf-8') as f:
            json.dump(flattened_citations, f, indent=2)
        print(f"Flattened citations saved to {flattened_file}")
        
        # Print citation count by court
        print("\nCitations by court:")
        court_counts = {}
        for filename in all_unconfirmed_citations:
            court = next((court_id for court_id in COURTS if court_id in filename.lower()), 'unknown')
            court_counts[court] = court_counts.get(court, 0) + len(all_unconfirmed_citations[filename])
        
        for court, count in court_counts.items():
            print(f"  {court.upper()}: {count} citations")
    else:
        print("No unconfirmed citations found in any briefs")
        
    print(f"\nTarget was {target_citations} citations, found {total_unconfirmed}")
    if total_unconfirmed >= target_citations:
        print("Successfully reached the target number of unconfirmed citations!")
    else:
        print(f"Did not reach target. Consider running the script again or increasing the number of briefs processed.")
        
    print("\nNow you can add these citations to the CaseStrainer interface by updating the templates.")
    print(f"The flattened citations file is at: {os.path.join(DOWNLOAD_DIR, 'unconfirmed_citations_flat.json')}")
    return total_unconfirmed

if __name__ == "__main__":
    main()
