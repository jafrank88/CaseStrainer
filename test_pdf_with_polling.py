#!/usr/bin/env python3
"""
Test PDF with async polling and analysis
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
                    print(f"   Progress: {progress}% - Status: {status} ({elapsed}s elapsed)")
            else:
                print(f"   Poll failed: {response.status_code}")
        except Exception as e:
            print(f"   Poll error: {e}")
        
        time.sleep(3)
    
    print(f"❌ Timeout after {max_wait} seconds")
    return None

def analyze_results(result):
    """Analyze citation results"""
    citations = result.get('citations', [])
    if 'result' in result and isinstance(result['result'], dict):
        citations = result['result'].get('citations', citations)
    
    clusters = result.get('clusters', [])
    if 'result' in result and isinstance(result['result'], dict):
        clusters = result['result'].get('clusters', clusters)
    
    print(f"\n{'='*80}")
    print("ANALYSIS RESULTS")
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
    
    header_details = []
    mismatch_details = []
    
    for cit in citations:
        extracted = cit.get('extracted_case_name', 'N/A')
        canonical = cit.get('canonical_name', '')
        is_verified = cit.get('verified', False) or cit.get('is_verified', False)
        name_mismatch = cit.get('name_mismatch', False)
        
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
                    'canonical': canonical
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
                    'similarity': cit.get('name_similarity', 0)
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
    print(f"\n✅ Match rate: {match_rate:.1f}% ({matches}/{total_with_canonical})")
    
    # Show header contamination
    if header_details:
        print(f"\n🚨 HEADER CONTAMINATION DETECTED ({len(header_details)} cases)")
        print("-" * 80)
        for detail in header_details[:10]:
            print(f"  Citation: {detail['citation']}")
            print(f"    Extracted: {detail['extracted']}")
            print(f"    Canonical: {detail['canonical']}")
            print()
        if len(header_details) > 10:
            print(f"  ... and {len(header_details) - 10} more")
    
    # Show top mismatches
    if mismatch_details:
        print(f"\n⚠️  NAME MISMATCHES ({len(mismatch_details)} cases)")
        print("-" * 80)
        # Sort by similarity (lowest first)
        mismatch_details.sort(key=lambda x: x.get('similarity', 0))
        for detail in mismatch_details[:10]:
            print(f"  Citation: {detail['citation']}")
            print(f"    Extracted: {detail['extracted']}")
            print(f"    Canonical: {detail['canonical']}")
            if detail.get('similarity'):
                print(f"    Similarity: {detail['similarity']:.2f}")
            print()
        if len(mismatch_details) > 10:
            print(f"  ... and {len(mismatch_details) - 10} more")
    
    return {
        'match_rate': match_rate,
        'header_count': header_count,
        'matches': matches,
        'mismatches': mismatches,
        'total_citations': len(citations)
    }

def test_pdf_with_polling():
    """Test PDF and poll for results"""
    pdf_path = r"D:\dev\casestrainer\1031351.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    print("=" * 80)
    print("TESTING PDF WITH ASYNC POLLING")
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
    
    # Upload file
    print("\n📤 Uploading PDF...")
    try:
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
                # Poll for results
                final_result = poll_task_status(base_url, task_id)
                if final_result:
                    return analyze_results(final_result)
                else:
                    return None
            else:
                # Immediate result
                return analyze_results(result)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    results = test_pdf_with_polling()
    if results:
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"Match Rate: {results.get('match_rate', 0):.1f}%")
        print(f"Header Contamination: {results.get('header_count', 0)}")
        print(f"Matches: {results.get('matches', 0)}")
        print(f"Mismatches: {results.get('mismatches', 0)}")
        print(f"Total Citations: {results.get('total_citations', 0)}")
        print(f"{'='*80}")

