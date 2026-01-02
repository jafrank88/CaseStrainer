#!/usr/bin/env python3
"""
Compare eyecite case name metadata vs regular extraction
"""

import requests
import json
import time
import os
from collections import defaultdict

def poll_task_status(base_url, task_id, max_wait=300):
    """Poll for task status until complete"""
    print(f"⏳ Polling task {task_id}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/task_status/{task_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', '')
                progress = data.get('progress', 0)
                
                if status == 'completed':
                    print(f"✅ Processing complete!")
                    return data
                elif status == 'failed':
                    print(f"❌ Processing failed: {data.get('error', 'Unknown error')}")
                    return None
                else:
                    elapsed = int(time.time() - start_time)
                    if elapsed % 30 == 0:  # Print every 30 seconds
                        print(f"   Progress: {progress}% - Status: {status} ({elapsed}s elapsed)")
        except Exception as e:
            if int(time.time() - start_time) % 30 == 0:
                print(f"   Poll error: {e}")
        
        time.sleep(3)
    
    print(f"❌ Timeout after {max_wait} seconds")
    return None

def analyze_results(result, label):
    """Analyze citation results"""
    citations = result.get('citations', [])
    if 'result' in result and isinstance(result['result'], dict):
        citations = result['result'].get('citations', citations)
    
    clusters = result.get('clusters', [])
    if 'result' in result and isinstance(result['result'], dict):
        clusters = result['result'].get('clusters', clusters)
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS: {label}")
    print(f"{'='*80}")
    print(f"Total citations: {len(citations)}")
    print(f"Total clusters: {len(clusters)}")
    print()
    
    # Analyze
    header_count = 0
    matches = 0
    mismatches = 0
    no_extraction = 0
    verified = 0
    eyecite_names = 0
    
    header_details = []
    mismatch_details = []
    
    for cit in citations:
        extracted = cit.get('extracted_case_name', 'N/A')
        canonical = cit.get('canonical_name', '')
        is_verified = cit.get('verified', False) or cit.get('is_verified', False)
        name_mismatch = cit.get('name_mismatch', False)
        method = cit.get('method', '')
        metadata = cit.get('metadata', {})
        
        # Check if name came from eyecite
        if metadata.get('eyecite_extracted') or 'eyecite' in method.lower():
            eyecite_names += 1
        
        if is_verified:
            verified += 1
        
        # Check for header contamination
        if extracted and extracted != 'N/A':
            extracted_upper = extracted.upper()
            has_et_al = 'ET AL' in extracted_upper
            has_role_word = any(role in extracted_upper for role in ['PETITIONER', 'RESPONDENT', 'APPELLANT', 'APPELLEE', 'PLAINTIFF', 'DEFENDANT'])
            has_no = 'NO.' in extracted_upper or ' NO ' in extracted_upper or extracted_upper.endswith(' NO')
            
            if (has_et_al and has_role_word) or (has_role_word and has_no):
                header_count += 1
                header_details.append({
                    'citation': cit.get('citation', ''),
                    'extracted': extracted,
                    'canonical': canonical,
                    'method': method
                })
        
        if extracted == 'N/A' or not extracted:
            no_extraction += 1
        elif canonical:
            if name_mismatch or not cit.get('names_equivalent', True):
                mismatches += 1
                mismatch_details.append({
                    'citation': cit.get('citation', ''),
                    'extracted': extracted,
                    'canonical': canonical,
                    'method': method
                })
            else:
                matches += 1
    
    # Statistics
    total_with_canonical = matches + mismatches
    match_rate = (matches / total_with_canonical * 100) if total_with_canonical > 0 else 0
    
    print(f"📊 STATISTICS")
    print("-" * 80)
    print(f"Verified: {verified}")
    print(f"Name matches: {matches}")
    print(f"Name mismatches: {mismatches}")
    print(f"Header contamination: {header_count} ⚠️")
    print(f"No extraction: {no_extraction}")
    print(f"Eyecite names: {eyecite_names}")
    print(f"\n✅ Match rate: {match_rate:.1f}% ({matches}/{total_with_canonical})")
    
    # Show header contamination
    if header_details:
        print(f"\n🚨 HEADER CONTAMINATION DETECTED ({len(header_details)} cases)")
        print("-" * 80)
        for detail in header_details[:5]:
            print(f"  Citation: {detail['citation']}")
            print(f"    Extracted: {detail['extracted']}")
            print(f"    Method: {detail['method']}")
            print()
        if len(header_details) > 5:
            print(f"  ... and {len(header_details) - 5} more")
    
    return {
        'match_rate': match_rate,
        'header_count': header_count,
        'matches': matches,
        'mismatches': mismatches,
        'total_citations': len(citations),
        'eyecite_names': eyecite_names,
        'no_extraction': no_extraction
    }

def test_with_eyecite(pdf_path, base_url):
    """Test with eyecite metadata enabled (current behavior)"""
    print("\n" + "="*80)
    print("TEST 1: WITH EYECITE METADATA (Current Behavior)")
    print("="*80)
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {
            'type': 'file',
            'enable_verification': 'true'
        }
        
        response = requests.post(f"{base_url}/analyze", files=files, data=data, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            print(response.text[:1000])
            return None
        
        result = response.json()
        
        # Check if async
        task_id = result.get('task_id')
        if task_id:
            final_result = poll_task_status(base_url, task_id)
            if final_result:
                return analyze_results(final_result, "WITH EYECITE METADATA")
            else:
                return None
        else:
            return analyze_results(result, "WITH EYECITE METADATA")

def test_without_eyecite(pdf_path, base_url):
    """Test without eyecite metadata (force regular extraction)"""
    print("\n" + "="*80)
    print("TEST 2: WITHOUT EYECITE METADATA (Force Regular Extraction)")
    print("="*80)
    print("⚠️  Setting USE_EYECITE_METADATA=false to disable eyecite metadata")
    print("="*80)
    
    # Set environment variable to disable eyecite metadata
    import subprocess
    import sys
    
    # We need to set this in the container, so we'll need to restart with the env var
    # For now, let's check if we can pass it via the API or modify the container
    print("⚠️  Note: This requires setting USE_EYECITE_METADATA=false in the container")
    print("   For a proper test, restart the container with: docker-compose -f docker-compose.prod.yml up -d --env USE_EYECITE_METADATA=false")
    print("   For now, analyzing which names came from eyecite...")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {
            'type': 'file',
            'enable_verification': 'true'
        }
        
        response = requests.post(f"{base_url}/analyze", files=files, data=data, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            print(response.text[:1000])
            return None
        
        result = response.json()
        
        # Check if async
        task_id = result.get('task_id')
        if task_id:
            final_result = poll_task_status(base_url, task_id)
            if final_result:
                # Filter out eyecite names for comparison
                citations = final_result.get('citations', [])
                if 'result' in final_result and isinstance(final_result['result'], dict):
                    citations = final_result['result'].get('citations', citations)
                
                # Count how many would be different if we skipped eyecite
                eyecite_header_count = 0
                non_eyecite_header_count = 0
                
                for cit in citations:
                    extracted = cit.get('extracted_case_name', 'N/A')
                    method = cit.get('method', '')
                    metadata = cit.get('metadata', {})
                    
                    is_eyecite = metadata.get('eyecite_extracted') or 'eyecite' in method.lower()
                    
                    if extracted and extracted != 'N/A':
                        extracted_upper = extracted.upper()
                        has_et_al = 'ET AL' in extracted_upper
                        has_role_word = any(role in extracted_upper for role in ['PETITIONER', 'RESPONDENT', 'APPELLANT', 'APPELLEE', 'PLAINTIFF', 'DEFENDANT'])
                        has_no = 'NO.' in extracted_upper or ' NO ' in extracted_upper or extracted_upper.endswith(' NO')
                        
                        if (has_et_al and has_role_word) or (has_role_word and has_no):
                            if is_eyecite:
                                eyecite_header_count += 1
                            else:
                                non_eyecite_header_count += 1
                
                print(f"\n📊 EYECITE vs NON-EYECITE HEADER ANALYSIS")
                print("-" * 80)
                print(f"Headers from eyecite: {eyecite_header_count}")
                print(f"Headers from regular extraction: {non_eyecite_header_count}")
                
                return analyze_results(final_result, "ANALYZING EYECITE CONTRIBUTION")
            else:
                return None
        else:
            return analyze_results(result, "ANALYZING EYECITE CONTRIBUTION")

def main():
    pdf_path = r"D:\dev\casestrainer\1031351.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print("=" * 80)
    print("EYECITE vs REGULAR EXTRACTION COMPARISON")
    print("=" * 80)
    print(f"PDF: {os.path.basename(pdf_path)}")
    print()
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Wait for service
    print("⏳ Waiting for service...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Service ready")
                break
        except:
            pass
        time.sleep(1)
    
    # Test with eyecite (current behavior)
    results_with_eyecite = test_with_eyecite(pdf_path, base_url)
    
    # Wait a bit between tests
    print("\n⏳ Waiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test without eyecite (analyze contribution)
    results_without_eyecite = test_without_eyecite(pdf_path, base_url)
    
    # Comparison
    if results_with_eyecite and results_without_eyecite:
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        print(f"\nWITH EYECITE:")
        print(f"  Match Rate: {results_with_eyecite.get('match_rate', 0):.1f}%")
        print(f"  Header Contamination: {results_with_eyecite.get('header_count', 0)}")
        print(f"  Eyecite Names: {results_with_eyecite.get('eyecite_names', 0)}")
        print(f"  No Extraction: {results_with_eyecite.get('no_extraction', 0)}")
        
        print(f"\nANALYSIS:")
        print(f"  Total Citations: {results_without_eyecite.get('total_citations', 0)}")
        print(f"  Header Contamination: {results_without_eyecite.get('header_count', 0)}")
        
        print("\n" + "="*80)

if __name__ == '__main__':
    main()

