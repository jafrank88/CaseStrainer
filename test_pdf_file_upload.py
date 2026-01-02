#!/usr/bin/env python3
"""
Test PDF via file upload method (more reliable than URL)
"""

import requests
import json
import time
import os
from collections import defaultdict

def test_pdf_file_upload():
    """Test PDF processing via file upload"""
    
    pdf_path = r"D:\dev\casestrainer\1031351.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    print("=" * 80)
    print("TESTING PDF VIA FILE UPLOAD")
    print("=" * 80)
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"Size: {os.path.getsize(pdf_path):,} bytes")
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
    
    # Process via file upload
    print("\n📤 Uploading PDF file...")
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
            if result.get('task_id') or result.get('status') == 'processing':
                print(f"⏳ Processing async, task_id: {result.get('task_id')}")
                print("   (This may take a while - check frontend for results)")
                print("\n💡 TIP: Check the frontend to see the full results when processing completes")
                return {'status': 'async', 'task_id': result.get('task_id')}
            
            # Extract citations
            citations = result.get('citations', [])
            if 'result' in result and isinstance(result['result'], dict):
                citations = result['result'].get('citations', citations)
            
            clusters = result.get('clusters', [])
            if 'result' in result and isinstance(result['result'], dict):
                clusters = result['result'].get('clusters', clusters)
            
            print(f"\n✅ Found {len(citations)} citations, {len(clusters)} clusters")
            
            # Analyze results
            print("\n" + "=" * 80)
            print("ANALYSIS")
            print("=" * 80)
            
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
                            'canonical': canonical
                        })
                    else:
                        matches += 1
            
            # Print statistics
            total_with_canonical = matches + mismatches
            match_rate = (matches / total_with_canonical * 100) if total_with_canonical > 0 else 0
            
            print(f"\n📊 STATISTICS")
            print("-" * 80)
            print(f"Total citations: {len(citations)}")
            print(f"Verified: {verified}")
            print(f"Name matches: {matches}")
            print(f"Name mismatches: {mismatches}")
            print(f"Header contamination: {header_count}")
            print(f"No extraction: {no_extraction}")
            print(f"\n✅ Match rate: {match_rate:.1f}% ({matches}/{total_with_canonical})")
            
            # Show header contamination
            if header_details:
                print(f"\n🚨 HEADER CONTAMINATION ({len(header_details)} cases)")
                print("-" * 80)
                for detail in header_details[:5]:
                    print(f"  {detail['citation']}: {detail['extracted']}")
                if len(header_details) > 5:
                    print(f"  ... and {len(header_details) - 5} more")
            
            # Show mismatches
            if mismatch_details:
                print(f"\n⚠️  NAME MISMATCHES ({len(mismatch_details)} cases)")
                print("-" * 80)
                for detail in mismatch_details[:5]:
                    print(f"  {detail['citation']}")
                    print(f"    Extracted: {detail['extracted']}")
                    print(f"    Canonical: {detail['canonical']}")
                if len(mismatch_details) > 5:
                    print(f"  ... and {len(mismatch_details) - 5} more")
            
            return {
                'match_rate': match_rate,
                'header_count': header_count,
                'matches': matches,
                'mismatches': mismatches
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    results = test_pdf_file_upload()
    if results and results.get('status') != 'async':
        print(f"\n{'='*80}")
        print(f"FINAL MATCH RATE: {results.get('match_rate', 0):.1f}%")
        print(f"Header Contamination: {results.get('header_count', 0)}")
        print(f"{'='*80}")

