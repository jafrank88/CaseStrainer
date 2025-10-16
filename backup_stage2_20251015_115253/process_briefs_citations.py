#!/usr/bin/env python3
"""
Script to process a folder of briefs through CaseStrainer and extract citations
that are not found in CourtListener, categorizing them by verification status.
"""

import os
import sys
import json
import csv
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
import re

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add src directory to path
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def load_text_file(file_path):
    """Load text content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def process_single_brief(file_path, api_base_url):
    """Process a single brief file and return citation analysis."""
    print(f"Processing: {os.path.basename(file_path)}")
    
    # Load the text content
    text_content = load_text_file(file_path)
    if not text_content:
        return None
    
    # Process through CaseStrainer API
    try:
        # Use the CaseStrainer API to analyze the text
        # Handle different API endpoint formats
        if "wolf.law.uw.edu" in api_base_url:
            api_url = f"{api_base_url}/api/analyze"  # Production endpoint
        else:
            api_url = f"{api_base_url}/api/analyze"  # Local endpoint
        
        # Prepare the request data
        data = {
            'text': text_content,
            'source': 'text_input'
        }
        
        print(f"  Sending text to CaseStrainer API...")
        response = requests.post(api_url, json=data, timeout=300)  # 5 minute timeout
        
        if response.status_code == 202:
            # Async processing - get job_id and poll for results
            job_data = response.json()
            job_id = job_data.get('job_id') or job_data.get('task_id')
            if not job_id:
                print(f"  No job_id in async response: {response.text}")
                return None
            
            print(f"  Job queued, polling for results (job_id: {job_id[:8]}...)")
            result = poll_for_results(api_base_url, job_id)
            if not result:
                print(f"  Failed to get results for job {job_id[:8]}...")
                return None
                
        elif response.status_code == 200:
            # Synchronous processing
            result = response.json()
        else:
            print(f"  API Error: {response.status_code} - {response.text}")
            return None
        
        # Handle different API response formats
        if 'citations' in result:
            # Direct citations format from production API
            all_citations = result['citations']
        elif result.get('success', False):
            # Wrapped success format
            citations_data = result.get('data', {})
            all_citations = citations_data.get('all_citations', [])
        else:
            print(f"  Processing failed: {result.get('error', 'Unknown error')}")
            return None
        
        if not all_citations:
            print(f"  No citations found in {os.path.basename(file_path)}")
            return {
                'file': os.path.basename(file_path),
                'total_citations': 0,
                'courtlistener_verified': 0,
                'non_courtlistener_citations': []
            }
        
        print(f"  Found {len(all_citations)} citations")
        
        # Analyze which citations are not in CourtListener
        non_courtlistener_citations = []
        courtlistener_verified_count = 0
        
        for citation in all_citations:
            # Map API response fields to our expected format
            citation_text = citation.get('citation', citation.get('text', ''))
            canonical_date = citation.get('canonical_date')
            canonical_name = citation.get('canonical_name')
            source = citation.get('source', '')
            verified = citation.get('verified', False)
            confidence = citation.get('confidence', 0.0)
            
            # Check if citation was verified by CourtListener
            # The CaseStrainer API already uses enhanced verification with name similarity matching
            # Trust the API's verification result instead of second-guessing it
            
            # The 'verified' field from CaseStrainer indicates if it was successfully verified
            api_verified = citation.get('verified', False)
            
            # Convert string boolean to actual boolean if needed
            if isinstance(api_verified, str):
                api_verified = api_verified.lower() == 'true'
            
            # Check if we have canonical data (indicates CourtListener found something)
            has_canonical_data = bool(canonical_date and canonical_name)
            
            # Consider it CourtListener verified if:
            # 1. API says it's verified AND we have canonical data, OR
            # 2. We have meaningful canonical data (not just placeholder values)
            is_courtlistener = (api_verified and has_canonical_data) or (
                has_canonical_data and 
                canonical_name != 'N/A' and 
                canonical_date != 'N/A' and
                len(canonical_name.strip()) > 0 and
                len(canonical_date.strip()) > 0
            )
            
            if is_courtlistener:
                courtlistener_verified_count += 1
            else:
                # This citation was not found in CourtListener
                citation_info = {
                    'citation_text': citation_text,
                    'extracted_case_name': citation.get('extracted_case_name', citation.get('case_name', '')),
                    'extracted_date': citation.get('extracted_date', citation.get('date', '')),
                    'verification_status': 'found_via_fallback' if verified else 'unverified',
                    'fallback_sources': [source] if verified and source else [],
                    'canonical_date': canonical_date,
                    'canonical_name': canonical_name,
                    'canonical_url': citation.get('url', citation.get('canonical_url', '')),
                    'source': source,
                    'verified': str(verified).lower(),
                    'confidence': confidence,
                    'verification_details': {}
                }
                
                # Determine verification status based on source and verification
                if verified and source:
                    citation_info['verification_status'] = 'found_via_fallback'
                    citation_info['fallback_sources'].append(source)
                
                # Add verification details
                citation_info['verification_details'] = {
                    'source': source,
                    'verified': verified,
                    'has_canonical_data': bool(citation.get('canonical_date') or citation.get('canonical_name')),
                    'confidence': citation.get('confidence', 0.0)
                }
                
                non_courtlistener_citations.append(citation_info)
        
        print(f"  CourtListener verified: {courtlistener_verified_count}")
        print(f"  Non-CourtListener: {len(non_courtlistener_citations)}")
        
        return {
            'file': os.path.basename(file_path),
            'total_citations': len(all_citations),
            'courtlistener_verified': courtlistener_verified_count,
            'non_courtlistener_citations': non_courtlistener_citations
        }
        
    except requests.exceptions.Timeout:
        print(f"  Timeout processing {os.path.basename(file_path)}")
        return None
    except Exception as e:
        print(f"  Error processing {os.path.basename(file_path)}: {e}")
        return None

def save_results_to_csv(results, output_file):
    """Save results to a CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'file_name', 'citation_text', 'extracted_case_name', 'extracted_date',
            'verification_status', 'fallback_sources', 'canonical_date', 'canonical_name', 'canonical_url',
            'source', 'verified', 'confidence', 'has_canonical_data'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            if result and result['non_courtlistener_citations']:
                for citation in result['non_courtlistener_citations']:
                    row = {
                        'file_name': result['file'],
                        'citation_text': citation['citation_text'],
                        'extracted_case_name': citation['extracted_case_name'],
                        'extracted_date': citation['extracted_date'],
                        'verification_status': citation['verification_status'],
                        'fallback_sources': '; '.join(citation['fallback_sources']),
                        'canonical_date': citation['canonical_date'],
                        'canonical_name': citation['canonical_name'],
                        'canonical_url': citation.get('canonical_url', ''),
                        'source': citation['source'],
                        'verified': citation['verified'],
                        'confidence': citation['confidence'],
                        'has_canonical_data': citation['verification_details']['has_canonical_data']
                    }
                    writer.writerow(row)

def save_summary_to_json(results, output_file):
    """Save a summary of results to a JSON file."""
    summary = {
        'processing_date': datetime.now().isoformat(),
        'total_files_processed': len([r for r in results if r is not None]),
        'total_files_with_errors': len([r for r in results if r is None]),
        'total_citations_found': sum(r['total_citations'] for r in results if r),
        'total_courtlistener_verified': sum(r['courtlistener_verified'] for r in results if r),
        'total_non_courtlistener': sum(len(r['non_courtlistener_citations']) for r in results if r),
        'files_summary': []
    }
    
    # Count verification statuses
    status_counts = {'unverified': 0, 'found_via_fallback': 0}
    fallback_source_counts = {}
    
    for result in results:
        if result and result['non_courtlistener_citations']:
            file_summary = {
                'file': result['file'],
                'total_citations': result['total_citations'],
                'courtlistener_verified': result['courtlistener_verified'],
                'non_courtlistener_count': len(result['non_courtlistener_citations']),
                'verification_breakdown': {'unverified': 0, 'found_via_fallback': 0}
            }
            
            for citation in result['non_courtlistener_citations']:
                status = citation['verification_status']
                status_counts[status] += 1
                file_summary['verification_breakdown'][status] += 1
                
                # Count fallback sources
                for source in citation['fallback_sources']:
                    fallback_source_counts[source] = fallback_source_counts.get(source, 0) + 1
            
            summary['files_summary'].append(file_summary)
    
    summary['verification_status_counts'] = status_counts
    summary['fallback_source_counts'] = fallback_source_counts
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

def download_additional_briefs(download_folder, text_folder, max_downloads=10):
    """Download additional briefs from WA courts website and convert to text."""
    base_url = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A08"
    
    print(f"\nDownloading additional briefs from: {base_url}")
    print(f"PDF download folder: {download_folder}")
    print(f"Text output folder: {text_folder}")
    
    # Create directories if they don't exist
    os.makedirs(download_folder, exist_ok=True)
    os.makedirs(text_folder, exist_ok=True)
    
    try:
        # Get the main page
        response = requests.get(base_url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to access WA courts website: {response.status_code}")
            return False
        
        # Look for PDF links in the page
        pdf_links = re.findall(r'href="([^"]*\.pdf[^"]*?)"', response.text, re.IGNORECASE)
        
        if not pdf_links:
            print("No PDF links found on the page")
            return False
        
        print(f"Found {len(pdf_links)} potential PDF links")
        
        downloaded_count = 0
        for i, pdf_link in enumerate(pdf_links[:max_downloads]):
            if downloaded_count >= max_downloads:
                break
                
            # Make the link absolute
            if pdf_link.startswith('/'):
                pdf_url = f"https://www.courts.wa.gov{pdf_link}"
            elif not pdf_link.startswith('http'):
                pdf_url = urljoin(base_url, pdf_link)
            else:
                pdf_url = pdf_link
            
            # Extract filename
            filename = os.path.basename(urlparse(pdf_url).path)
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            pdf_path = os.path.join(download_folder, filename)
            txt_path = os.path.join(text_folder, filename.replace('.pdf', '.txt'))
            
            # Skip if already exists
            if os.path.exists(txt_path):
                print(f"  Skipping {filename} - text file already exists")
                continue
            
            print(f"  [{i+1}/{min(len(pdf_links), max_downloads)}] Downloading: {filename}")
            
            try:
                # Download PDF
                pdf_response = requests.get(pdf_url, timeout=60)
                if pdf_response.status_code == 200:
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_response.content)
                    
                    # Convert to text
                    if convert_pdf_to_text(pdf_path, txt_path):
                        downloaded_count += 1
                        print(f"    ✅ Successfully converted to text")
                    else:
                        print(f"    ❌ Failed to convert to text")
                        # Clean up PDF if conversion failed
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                else:
                    print(f"    ❌ Failed to download: {pdf_response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error downloading {filename}: {e}")
            
            # Small delay to be respectful
            time.sleep(1)
        
        print(f"\nDownloaded and converted {downloaded_count} briefs")
        return downloaded_count > 0
        
    except Exception as e:
        print(f"Error downloading briefs: {e}")
        return False

def convert_pdf_to_text(pdf_path, txt_path):
    """Convert PDF to text using available tools."""
    try:
        # Try using PyMuPDF (fitz) first
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return True
            
        except ImportError:
            # Fall back to pdfplumber
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                return True
                
            except ImportError:
                # Fall back to pdftotext command line tool
                try:
                    result = subprocess.run(
                        ['pdftotext', pdf_path, txt_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    return result.returncode == 0
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    print("    No PDF conversion tools available (PyMuPDF, pdfplumber, or pdftotext)")
                    return False
                    
    except Exception as e:
        print(f"    Error converting PDF: {e}")
        return False

def poll_for_results(api_base_url, job_id, max_wait_time=300, poll_interval=5):
    """Poll for async job results."""
    import time
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            # Try different possible status endpoints
            status_urls = [
                f"{api_base_url}/api/task_status/{job_id}",
                f"{api_base_url}/api/processing_progress?task_id={job_id}",
                f"{api_base_url}/api/status/{job_id}"
            ]
            
            for status_url in status_urls:
                try:
                    status_response = requests.get(status_url, timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Check if job is complete
                        if status_data.get('status') == 'completed' or status_data.get('state') == 'SUCCESS':
                            # Return the result data
                            return status_data.get('result', status_data.get('data', status_data))
                        elif status_data.get('status') == 'failed' or status_data.get('state') == 'FAILURE':
                            print(f"  Job failed: {status_data.get('error', 'Unknown error')}")
                            return None
                        elif status_data.get('status') in ['pending', 'processing'] or status_data.get('state') == 'PENDING':
                            print(f"  Job still processing... ({int(time.time() - start_time)}s)")
                            break  # Continue polling
                        else:
                            # Unknown status, continue to next URL
                            continue
                except requests.exceptions.RequestException:
                    continue  # Try next URL
            
            time.sleep(poll_interval)
            
        except Exception as e:
            print(f"  Error polling for results: {e}")
            time.sleep(poll_interval)
    
    print(f"  Timeout waiting for job results after {max_wait_time}s")
    return None

def check_server_status(api_base_url):
    """Check if CaseStrainer server is running."""
    try:
        response = requests.get(f"{api_base_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def process_batch_with_auto_download(briefs_folder, pdf_download_folder, api_base_url, batch_size=50, max_total_downloads=500):
    """Process briefs in batches, automatically downloading more as needed."""
    all_results = []
    total_processed = 0
    total_downloaded = 0
    batch_number = 1
    
    while total_downloaded < max_total_downloads:
        print(f"\n{'='*80}")
        print(f"BATCH {batch_number} - Processing existing briefs")
        print(f"{'='*80}")
        
        # Get current text files
        text_files = [f for f in os.listdir(briefs_folder) if f.endswith('.txt')]
        text_files.sort()
        
        # Skip files we've already processed
        files_to_process = text_files[total_processed:]
        
        if not files_to_process:
            print("No new briefs to process in current batch.")
        else:
            print(f"Processing {len(files_to_process)} briefs in this batch...")
            
            # Process current batch
            for i, filename in enumerate(files_to_process):
                file_path = os.path.join(briefs_folder, filename)
                print(f"[{total_processed + i + 1}] Processing: {filename}")
                
                result = process_single_brief(file_path, api_base_url)
                all_results.append(result)
                
                if result:
                    print(f"  Total citations: {result['total_citations']}")
                    print(f"  CourtListener verified: {result['courtlistener_verified']}")
                    print(f"  Non-CourtListener: {len(result['non_courtlistener_citations'])}")
                
                print("-" * 40)
            
            total_processed += len(files_to_process)
        
        # Try to download more briefs for the next batch
        print(f"\n{'='*80}")
        print(f"BATCH {batch_number} - Downloading additional briefs")
        print(f"{'='*80}")
        
        print(f"Attempting to download up to {batch_size} additional briefs...")
        downloaded_count = download_additional_briefs(pdf_download_folder, briefs_folder, batch_size)
        
        if downloaded_count == 0:
            print("No new briefs were downloaded. Processing complete.")
            break
        
        total_downloaded += downloaded_count
        batch_number += 1
        
        print(f"\nBatch {batch_number - 1} Summary:")
        print(f"  Processed: {len(files_to_process)} briefs")
        print(f"  Downloaded: {downloaded_count} new briefs")
        print(f"  Total processed so far: {total_processed}")
        print(f"  Total downloaded so far: {total_downloaded}")
        
        if total_downloaded >= max_total_downloads:
            print(f"\nReached maximum download limit ({max_total_downloads}). Stopping.")
            break
    
    return all_results, total_processed, total_downloaded

def main():
    """Main function to process all briefs in the folder."""
    briefs_folder = r"D:\dev\casestrainer\wa_briefs_txt"
    pdf_download_folder = r"D:\dev\casestrainer\wa_briefs"
    output_folder = r"D:\dev\casestrainer"
    
    # Try production server first, fallback to local if needed
    production_url = "https://wolf.law.uw.edu/casestrainer"
    local_url = "http://localhost:5000"
    
    print("Checking server availability...")
    if check_server_status(production_url):
        api_base_url = production_url
        print(f"✅ Using production server: {api_base_url}")
    elif check_server_status(local_url):
        api_base_url = local_url
        print(f"✅ Using local server: {api_base_url}")
    else:
        print("❌ Neither production nor local server is available!")
        print("Please ensure one of the following is running:")
        print(f"  - Production: {production_url}")
        print(f"  - Local: {local_url}")
        return
    
    # Create output filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_output = os.path.join(output_folder, f"non_courtlistener_citations_{timestamp}.csv")
    json_output = os.path.join(output_folder, f"citation_processing_summary_{timestamp}.json")
    
    print(f"CaseStrainer Batch Citation Processor")
    print(f"=====================================")
    print(f"Processing briefs from: {briefs_folder}")
    print(f"PDF download folder: {pdf_download_folder}")
    print(f"Output files will be saved to: {output_folder}")
    print(f"CSV output: {os.path.basename(csv_output)}")
    print(f"JSON summary: {os.path.basename(json_output)}")
    print(f"API base URL: {api_base_url}")
    print("-" * 60)
    
    # Configuration options - use defaults for non-interactive mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # Non-interactive mode with defaults
        batch_size = 50
        max_total = 500
        auto_mode = True
        print("\nRunning in non-interactive mode with default settings...")
    else:
        # Interactive mode
        try:
            print("\nBatch Processing Configuration:")
            batch_size = input("Briefs to download per batch (default 50): ").strip()
            batch_size = int(batch_size) if batch_size else 50
            
            max_total = input("Maximum total briefs to download (default 500): ").strip()
            max_total = int(max_total) if max_total else 500
            
            auto_mode = input("\nEnable automatic batch processing? (y/n, default y): ").strip().lower()
            auto_mode = auto_mode in ['y', 'yes', ''] or auto_mode == ''
            
        except (ValueError, KeyboardInterrupt):
            print("\nUsing default settings...")
            batch_size = 50
            max_total = 500
            auto_mode = True
    
    print(f"\nConfiguration:")
    print(f"  Batch size: {batch_size} briefs")
    print(f"  Maximum total downloads: {max_total} briefs")
    print(f"  Auto-batch mode: {'Enabled' if auto_mode else 'Disabled'}")
    print("-" * 60)
    
    # Choose processing mode
    if auto_mode:
        print("\n▶️ Starting automated batch processing...")
        results, total_processed, total_downloaded = process_batch_with_auto_download(
            briefs_folder, pdf_download_folder, api_base_url, batch_size, max_total
        )
        
        print(f"\n✅ Automated batch processing complete!")
        print(f"  Total briefs processed: {total_processed}")
        print(f"  Total new briefs downloaded: {total_downloaded}")
        
    else:
        # Original single-batch processing
        print("\n▶️ Starting single-batch processing...")
        
        # Get all text files in the briefs folder
        text_files = [f for f in os.listdir(briefs_folder) if f.endswith('.txt')]
        text_files.sort()  # Process in alphabetical order
        
        print(f"Found {len(text_files)} text files to process")
        print("-" * 60)
        
        # Process each file
        results = []
        for i, filename in enumerate(text_files, 1):
            file_path = os.path.join(briefs_folder, filename)
            print(f"[{i}/{len(text_files)}] Processing: {filename}")
            
            result = process_single_brief(file_path, api_base_url)
            results.append(result)
            
            if result:
                print(f"  Total citations: {result['total_citations']}")
                print(f"  CourtListener verified: {result['courtlistener_verified']}")
                print(f"  Non-CourtListener: {len(result['non_courtlistener_citations'])}")
            
            print("-" * 40)
    
    # Save results
    print("\nὋe Saving results...")
    save_results_to_csv(results, csv_output)
    save_summary_to_json(results, json_output)
    
    # Print final summary
    total_citations = sum(r['total_citations'] for r in results if r)
    total_non_courtlistener = sum(len(r['non_courtlistener_citations']) for r in results if r)
    
    print("\n" + "=" * 80)
    print("✅ PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Files processed: {len([r for r in results if r])}")
    print(f"Total citations found: {total_citations}")
    print(f"Citations not in CourtListener: {total_non_courtlistener}")
    print(f"Percentage not in CourtListener: {(total_non_courtlistener/total_citations*100):.1f}%" if total_citations > 0 else "N/A")
    
    # Show breakdown by verification status
    verified_fallback = sum(1 for r in results if r for c in r['non_courtlistener_citations'] if c['verification_status'] == 'found_via_fallback')
    unverified = sum(1 for r in results if r for c in r['non_courtlistener_citations'] if c['verification_status'] == 'unverified')
    
    print(f"\nNon-CourtListener Citation Breakdown:")
    print(f"  Found via fallback sources: {verified_fallback}")
    print(f"  Completely unverified: {unverified}")
    
    print(f"\nὌ1 Detailed results saved to:")
    print(f"  CSV: {csv_output}")
    print(f"  Summary: {json_output}")
    
    print(f"\nὌa The CSV file contains all non-CourtListener citations with:")
    print(f"  - Citation text and extracted metadata")
    print(f"  - Verification status and sources")
    print(f"  - Canonical URLs, names, and dates (when available)")
    print(f"  - Confidence scores and source information")

if __name__ == "__main__":
    main()
