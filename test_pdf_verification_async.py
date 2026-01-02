#!/usr/bin/env python3
"""
Test verification fix with D2 60382-9-II Published Opinion.pdf - with async polling
"""

import requests
import json
import os
import time

def test_pdf_verification_async():
    """Test the verification fix with the PDF document using async polling"""
    
    print("🔧 TESTING VERIFICATION FIX WITH PDF DOCUMENT (ASYNC)")
    print("=" * 60)
    
    pdf_path = r"d:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"📄 PDF file: {os.path.basename(pdf_path)}")
    print(f"📊 File size: {os.path.getsize(pdf_path):,} bytes")
    print()
    
    # Test via file upload API
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            data = {
                'type': 'file',
                'extract_citations': 'true'
            }
            
            print("📤 Uploading PDF for processing...")
            response = requests.post(url, files=files, data=data)
            
            print(f"📊 Initial Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if this is an async response
                if 'task_id' in result:
                    task_id = result['task_id']
                    print(f"🔄 Async processing started - Task ID: {task_id}")
                    print(f"⏳ Polling for results...")
                    
                    # Poll for results
                    max_wait_time = 120  # 2 minutes max
                    poll_interval = 3   # Check every 3 seconds
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait_time:
                        try:
                            poll_response = requests.get(f"http://localhost:5000/casestrainer/api/task/{task_id}")
                            
                            if poll_response.status_code == 200:
                                poll_result = poll_response.json()
                                status = poll_result.get('status', 'unknown')
                                
                                print(f"   📊 Status: {status}")
                                
                                if status == 'completed':
                                    print(f"   ✅ Processing completed!")
                                    result = poll_result
                                    break
                                elif status == 'failed':
                                    print(f"   ❌ Processing failed: {poll_result.get('error', 'Unknown error')}")
                                    return
                                else:
                                    # Still processing
                                    progress = poll_result.get('metadata', {}).get('progress_data', {})
                                    if progress:
                                        print(f"   🔄 Progress: {progress.get('message', 'Processing...')}")
                                    
                            time.sleep(poll_interval)
                            
                        except Exception as e:
                            print(f"   ⚠️  Poll error: {e}")
                            time.sleep(poll_interval)
                    
                    else:
                        print(f"   ⏰ Timeout after {max_wait_time} seconds")
                        return
                
                # Now process the results
                citations = result.get('result', {}).get('citations', [])
                
                print(f"\n📋 Found {len(citations)} citations:")
                
                verified_count = 0
                canonical_data_count = 0
                
                for i, citation in enumerate(citations[:10]):  # Show first 10
                    print(f"\n  Citation {i+1}: {citation.get('citation', 'N/A')}")
                    
                    verified = citation.get('verified', False)
                    canonical_name = citation.get('canonical_name', 'N/A')
                    canonical_date = citation.get('canonical_date', 'N/A')
                    canonical_url = citation.get('canonical_url', 'N/A')
                    
                    has_canonical_data = bool(canonical_name and canonical_date and canonical_url)
                    
                    print(f"    Verified: {verified}")
                    print(f"    Canonical Name: {canonical_name}")
                    print(f"    Canonical Date: {canonical_date}")
                    print(f"    Canonical URL: {canonical_url}")
                    
                    if verified:
                        verified_count += 1
                    if has_canonical_data:
                        canonical_data_count += 1
                    
                    # Check for verification paradox
                    if has_canonical_data and not verified:
                        print(f"    ⚠️  VERIFICATION PARADOX: Has canonical data but not verified!")
                    elif verified and has_canonical_data:
                        print(f"    ✅ VERIFICATION WORKING: Correctly verified with canonical data!")
                
                print(f"\n📈 SUMMARY:")
                print(f"   Total citations: {len(citations)}")
                print(f"   Verified citations: {verified_count}")
                print(f"   Citations with canonical data: {canonical_data_count}")
                
                # Check if verification paradox is fixed
                paradox_citations = []
                for citation in citations:
                    has_canonical = bool(
                        citation.get('canonical_name') and 
                        citation.get('canonical_date') and 
                        citation.get('canonical_url')
                    )
                    if has_canonical and not citation.get('verified', False):
                        paradox_citations.append(citation.get('citation', 'Unknown'))
                
                if paradox_citations:
                    print(f"   ⚠️  Citations with verification paradox: {len(paradox_citations)}")
                    for cit in paradox_citations[:5]:  # Show first 5
                        print(f"      - {cit}")
                else:
                    print(f"   ✅ VERIFICATION PARADOX FIXED: No citations with canonical data marked as unverified!")
                
                # Show metadata
                metadata = result.get('result', {}).get('metadata', {})
                print(f"\n📋 PROCESSING METADATA:")
                print(f"   Processing mode: {metadata.get('processing_mode', 'N/A')}")
                print(f"   Verification count: {metadata.get('verification_count', 'N/A')}")
                print(f"   Stages completed: {metadata.get('stages_completed', 'N/A')}")
                print(f"   Status: {metadata.get('status', 'N/A')}")
                
            else:
                print(f"❌ Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_verification_async()
