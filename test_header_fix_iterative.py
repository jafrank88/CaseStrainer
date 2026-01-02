#!/usr/bin/env python3
"""
Iterative test script to process PDF and analyze case name matching
"""

import requests
import json
import time
import os
from collections import defaultdict

def test_pdf_and_analyze():
    """Test PDF processing and analyze case name matching"""
    
    # The PDF that was causing header contamination issues
    pdf_path = r"D:\dev\casestrainer\1031351.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    
    print("=" * 80)
    print("TESTING PDF PROCESSING - CASE NAME MATCHING ANALYSIS")
    print("=" * 80)
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"Size: {os.path.getsize(pdf_path):,} bytes")
    print()
    
    # Wait for service to be ready
    print("⏳ Waiting for service to be ready...")
    base_url = "http://localhost:5000/casestrainer/api"
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Service is ready")
                break
        except:
            pass
        time.sleep(1)
        if i == max_retries - 1:
            print("❌ Service not ready after 30 seconds")
            return None
    
    # Process PDF
    print("\n📤 Uploading PDF for processing...")
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            data = {
                'type': 'file',
                'enable_verification': 'true'
            }
            
            response = requests.post(f"{base_url}/analyze", files=files, data=data, timeout=300)
            
            if response.status_code != 200:
                print(f"❌ Failed to process PDF: {response.status_code}")
                print(response.text[:1000])
                return None
            
            result = response.json()
            
            # Check if async processing
            if result.get('task_id') or result.get('status') == 'processing':
                task_id = result.get('task_id')
                print(f"⏳ Processing asynchronously, task_id: {task_id}")
                print("   Polling for results...")
                
                # Poll for results
                max_polls = 60
                poll_interval = 2
                for poll in range(max_polls):
                    time.sleep(poll_interval)
                    status_response = requests.get(f"{base_url}/task-status/{task_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', '')
                        progress = status_data.get('progress', 0)
                        print(f"   Progress: {progress}% - Status: {status}")
                        
                        if status == 'completed':
                            result = status_data
                            break
                        elif status == 'failed':
                            print(f"❌ Processing failed: {status_data.get('error', 'Unknown error')}")
                            return None
                    else:
                        print(f"   Poll {poll + 1}/{max_polls} - Waiting...")
                
                if result.get('status') != 'completed':
                    print("❌ Processing timed out")
                    return None
            
            # Debug: Print full response structure
            print(f"\n📋 Response keys: {list(result.keys())}")
            if 'result' in result:
                print(f"📋 Result keys: {list(result.get('result', {}).keys())}")
            
            # Handle different response structures
            if 'result' in result and isinstance(result['result'], dict):
                citations = result['result'].get('citations', result.get('citations', []))
                clusters = result['result'].get('clusters', result.get('clusters', []))
            else:
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
            
            # Analyze results
            print("\n" + "=" * 80)
            print("ANALYSIS RESULTS")
            print("=" * 80)
            
            print(f"Total citations: {len(citations)}")
            print(f"Total clusters: {len(clusters)}")
            print()
            
            # Analyze name matching
            name_matches = 0
            name_mismatches = 0
            header_contamination = 0
            no_extraction = 0
            verified = 0
            unverified = 0
            
            mismatch_details = []
            header_details = []
            
            for cit in citations:
                extracted = cit.get('extracted_case_name', 'N/A')
                canonical = cit.get('canonical_name', '')
                is_verified = cit.get('verified', False) or cit.get('is_verified', False)
                name_mismatch = cit.get('name_mismatch', False)
                
                if is_verified:
                    verified += 1
                else:
                    unverified += 1
                
                # Check for header contamination
                if extracted and extracted != 'N/A':
                    extracted_upper = extracted.upper()
                    has_et_al = 'ET AL' in extracted_upper
                    has_role_word = any(role in extracted_upper for role in ['PETITIONER', 'RESPONDENT', 'APPELLANT', 'APPELLEE', 'PLAINTIFF', 'DEFENDANT'])
                    has_no = 'NO.' in extracted_upper or ' NO ' in extracted_upper or extracted_upper.endswith(' NO')
                    
                    if (has_et_al and has_role_word) or (has_role_word and has_no):
                        header_contamination += 1
                        header_details.append({
                            'citation': cit.get('citation', ''),
                            'extracted': extracted,
                            'canonical': canonical
                        })
                
                if extracted == 'N/A' or not extracted:
                    no_extraction += 1
                elif canonical:
                    # Check if names match
                    if name_mismatch or not cit.get('names_equivalent', True):
                        name_mismatches += 1
                        mismatch_details.append({
                            'citation': cit.get('citation', ''),
                            'extracted': extracted,
                            'canonical': canonical,
                            'similarity': cit.get('name_similarity', 0)
                        })
                    else:
                        name_matches += 1
            
            # Print statistics
            print("📊 STATISTICS")
            print("-" * 80)
            print(f"Verified citations: {verified}")
            print(f"Unverified citations: {unverified}")
            print(f"Name matches: {name_matches}")
            print(f"Name mismatches: {name_mismatches}")
            print(f"Header contamination: {header_contamination}")
            print(f"No extraction: {no_extraction}")
            print()
            
            # Calculate match rate
            total_with_canonical = name_matches + name_mismatches
            if total_with_canonical > 0:
                match_rate = (name_matches / total_with_canonical) * 100
                print(f"✅ Match rate: {match_rate:.1f}% ({name_matches}/{total_with_canonical})")
            else:
                print("⚠️  No citations with canonical names to compare")
            
            print()
            
            # Show header contamination details
            if header_details:
                print("🚨 HEADER CONTAMINATION DETECTED")
                print("-" * 80)
                for detail in header_details[:10]:  # Show first 10
                    print(f"  Citation: {detail['citation']}")
                    print(f"    Extracted: {detail['extracted']}")
                    print(f"    Canonical: {detail['canonical']}")
                    print()
                if len(header_details) > 10:
                    print(f"  ... and {len(header_details) - 10} more")
                print()
            
            # Show mismatch details
            if mismatch_details:
                print("⚠️  NAME MISMATCHES")
                print("-" * 80)
                for detail in mismatch_details[:10]:  # Show first 10
                    print(f"  Citation: {detail['citation']}")
                    print(f"    Extracted: {detail['extracted']}")
                    print(f"    Canonical: {detail['canonical']}")
                    if detail.get('similarity'):
                        print(f"    Similarity: {detail['similarity']:.2f}")
                    print()
                if len(mismatch_details) > 10:
                    print(f"  ... and {len(mismatch_details) - 10} more")
                print()
            
            return {
                'match_rate': match_rate if total_with_canonical > 0 else 0,
                'name_matches': name_matches,
                'name_mismatches': name_mismatches,
                'header_contamination': header_contamination,
                'no_extraction': no_extraction,
                'verified': verified,
                'unverified': unverified,
                'total_citations': len(citations)
            }
            
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    results = test_pdf_and_analyze()
    if results:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Match Rate: {results['match_rate']:.1f}%")
        print(f"Header Contamination: {results['header_contamination']}")
        print(f"Name Matches: {results['name_matches']}")
        print(f"Name Mismatches: {results['name_mismatches']}")

