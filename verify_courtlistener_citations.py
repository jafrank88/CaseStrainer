#!/usr/bin/env python3
"""
Direct CourtListener Verification Tool

This script takes the CSV output from the brief processing and directly verifies
each citation against the CourtListener API to determine which ones are actually
in CourtListener vs. truly missing.
"""

import csv
import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()

def load_courtlistener_api_key():
    """Load CourtListener API key from environment."""
    # Try to load from .env file
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('COURTLISTENER_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    # Try environment variable
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if api_key:
        return api_key
    
    print("⚠️  Warning: No CourtListener API key found. Using free tier (limited requests).")
    return None

def verify_citation_with_courtlistener(citation_text, api_key=None, max_retries=3):
    """
    Directly verify a citation with CourtListener API v4.
    
    Returns:
        dict: {
            'found': bool,
            'canonical_name': str or None,
            'canonical_date': str or None,
            'url': str or None,
            'error': str or None
        }
    """
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer Citation Verifier'
    }
    
    if api_key:
        headers['Authorization'] = f'Token {api_key}'
    
    data = {"citation": citation_text}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    # Get the first (best) result
                    result = results[0]
                    clusters = result.get('clusters', [])
                    if clusters:
                        cluster = clusters[0]
                        return {
                            'found': True,
                            'canonical_name': cluster.get('case_name', ''),
                            'canonical_date': cluster.get('date_filed', ''),
                            'url': f"https://www.courtlistener.com{cluster.get('absolute_url', '')}",
                            'error': None
                        }
                
                return {
                    'found': False,
                    'canonical_name': None,
                    'canonical_date': None,
                    'url': None,
                    'error': None
                }
                
            elif response.status_code == 404:
                return {
                    'found': False,
                    'canonical_name': None,
                    'canonical_date': None,
                    'url': None,
                    'error': None
                }
                
            elif response.status_code == 429:
                # Rate limited
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            else:
                return {
                    'found': False,
                    'canonical_name': None,
                    'canonical_date': None,
                    'url': None,
                    'error': f"HTTP {response.status_code}: {response.text[:100]}"
                }
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                return {
                    'found': False,
                    'canonical_name': None,
                    'canonical_date': None,
                    'url': None,
                    'error': f"Request failed: {str(e)}"
                }
            time.sleep(1)
    
    return {
        'found': False,
        'canonical_name': None,
        'canonical_date': None,
        'url': None,
        'error': "Max retries exceeded"
    }

def process_csv_file(csv_file_path, output_file_path, api_key=None, max_citations=None):
    """Process the CSV file and verify each citation with CourtListener."""
    
    print(f"📁 Reading citations from: {csv_file_path}")
    print(f"📝 Output will be saved to: {output_file_path}")
    print(f"🔑 API Key: {'Present' if api_key else 'Not found (using free tier)'}")
    print("-" * 60)
    
    results = []
    processed_count = 0
    found_in_courtlistener = 0
    errors = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for row in reader:
                if max_citations and processed_count >= max_citations:
                    break
                
                citation_text = row.get('citation_text', '').strip()
                if not citation_text:
                    continue
                
                processed_count += 1
                print(f"[{processed_count}] Verifying: {citation_text}")
                
                # Verify with CourtListener
                cl_result = verify_citation_with_courtlistener(citation_text, api_key)
                
                # Create result record
                result = {
                    'original_file': row.get('file_name', ''),
                    'citation_text': citation_text,
                    'extracted_case_name': row.get('extracted_case_name', ''),
                    'extracted_date': row.get('extracted_date', ''),
                    'casestrainer_canonical_name': row.get('canonical_name', ''),
                    'casestrainer_canonical_date': row.get('canonical_date', ''),
                    'courtlistener_found': cl_result['found'],
                    'courtlistener_canonical_name': cl_result['canonical_name'] or '',
                    'courtlistener_canonical_date': cl_result['canonical_date'] or '',
                    'courtlistener_url': cl_result['url'] or '',
                    'verification_error': cl_result['error'] or '',
                    'status': 'error' if cl_result['error'] else ('found_in_courtlistener' if cl_result['found'] else 'not_in_courtlistener')
                }
                
                results.append(result)
                
                if cl_result['found']:
                    found_in_courtlistener += 1
                    print(f"  ✅ Found: {cl_result['canonical_name']}")
                elif cl_result['error']:
                    errors += 1
                    print(f"  ❌ Error: {cl_result['error']}")
                else:
                    print(f"  ❌ Not found in CourtListener")
                
                # Rate limiting - be respectful to CourtListener
                time.sleep(0.5)  # 500ms between requests
                
                # Progress update every 10 citations
                if processed_count % 10 == 0:
                    print(f"  Progress: {processed_count} processed, {found_in_courtlistener} found in CL, {errors} errors")
    
    except FileNotFoundError:
        print(f"❌ Error: Could not find file {csv_file_path}")
        return
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return
    
    # Save results
    print(f"\n💾 Saving results...")
    
    with open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
        if results:
            fieldnames = list(results[0].keys())
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    # Print summary
    not_in_courtlistener = processed_count - found_in_courtlistener - errors
    
    print(f"\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE")
    print("=" * 60)
    print(f"Total citations processed: {processed_count}")
    print(f"Found in CourtListener: {found_in_courtlistener} ({found_in_courtlistener/processed_count*100:.1f}%)")
    print(f"Not in CourtListener: {not_in_courtlistener} ({not_in_courtlistener/processed_count*100:.1f}%)")
    print(f"Errors: {errors} ({errors/processed_count*100:.1f}%)")
    print(f"\n📊 Results saved to: {output_file_path}")

def main():
    """Main function."""
    print("CourtListener Citation Verifier")
    print("=" * 40)
    
    # Load API key
    api_key = load_courtlistener_api_key()
    
    # Find the most recent CSV file
    csv_files = list(Path('.').glob('non_courtlistener_citations_*.csv'))
    if not csv_files:
        print("❌ No citation CSV files found in current directory.")
        print("Please run the brief processing script first.")
        return
    
    # Use the most recent file
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"courtlistener_verification_results_{timestamp}.csv"
    
    print(f"📁 Input file: {latest_csv}")
    print(f"📝 Output file: {output_file}")
    
    # Ask for processing limits
    try:
        max_citations = input("\nHow many citations to verify? (Enter for all, or number): ").strip()
        max_citations = int(max_citations) if max_citations else None
    except (ValueError, KeyboardInterrupt):
        max_citations = None
    
    if max_citations:
        print(f"Will process first {max_citations} citations")
    else:
        print("Will process all citations")
    
    print("\n🚀 Starting verification...")
    
    # Process the file
    process_csv_file(latest_csv, output_file, api_key, max_citations)

if __name__ == "__main__":
    main()
