#!/usr/bin/env python3
"""
Quick PDF test with correct task status endpoint
"""

import requests
import json
import os
import time

def quick_pdf_test_fixed():
    """Quick test with correct task status endpoint"""
    
    print("🚀 QUICK PDF TEST (FIXED ENDPOINT)")
    print("=" * 50)
    
    pdf_path = r"d:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    # Test via file upload API
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            data = {
                'type': 'file',
                'extract_citations': 'true'
            }
            
            print("📤 Uploading PDF...")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'task_id' in result:
                    task_id = result['task_id']
                    print(f"🔄 Task ID: {task_id}")
                    
                    # Poll immediately and frequently with correct endpoint
                    for i in range(60):  # Try for 3 minutes
                        try:
                            poll_response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
                            
                            if poll_response.status_code == 200:
                                poll_result = poll_response.json()
                                status = poll_result.get('status', 'unknown')
                                
                                print(f"   Check {i+1}: Status = {status}")
                                
                                if status == 'completed':
                                    citations = poll_result.get('citations', [])
                                    print(f"   ✅ COMPLETED! Found {len(citations)} citations")
                                    
                                    # Quick verification check
                                    paradox_count = 0
                                    verified_with_canonical = 0
                                    
                                    for citation in citations[:20]:  # Check first 20
                                        has_canonical = bool(
                                            citation.get('canonical_name') and 
                                            citation.get('canonical_date') and 
                                            citation.get('canonical_url')
                                        )
                                        verified = citation.get('verified', False)
                                        
                                        if has_canonical and not verified:
                                            paradox_count += 1
                                        elif verified and has_canonical:
                                            verified_with_canonical += 1
                                    
                                    print(f"\n   📈 VERIFICATION SUMMARY:")
                                    print(f"   Citations checked: {min(len(citations), 20)}")
                                    print(f"   Verified with canonical data: {verified_with_canonical}")
                                    print(f"   Verification paradox cases: {paradox_count}")
                                    
                                    if paradox_count == 0 and verified_with_canonical > 0:
                                        print(f"   ✅ VERIFICATION PARADOX FIXED!")
                                    elif paradox_count > 0:
                                        print(f"   ⚠️  VERIFICATION PARADOX EXISTS: {paradox_count} cases")
                                    else:
                                        print(f"   ℹ️  No citations with canonical data found")
                                    
                                    return
                                    
                                elif status == 'failed':
                                    print(f"   ❌ FAILED: {poll_result.get('error', 'Unknown error')}")
                                    return
                                else:
                                    # Show progress if available
                                    progress = poll_result.get('progress_percent', 0)
                                    message = poll_result.get('current_message', 'Processing...')
                                    if progress > 0:
                                        print(f"   Check {i+1}: {progress}% - {message}")
                            
                            elif poll_response.status_code == 404:
                                print(f"   Check {i+1}: Task not found yet (still processing)")
                            else:
                                print(f"   Check {i+1}: HTTP {poll_response.status_code} - {poll_response.text}")
                        
                        except Exception as e:
                            print(f"   Check {i+1}: Error - {e}")
                        
                        time.sleep(3)  # Wait 3 seconds between checks
                    
                    print(f"   ⏰ Timeout after 3 minutes")
                else:
                    # Sync response
                    citations = result.get('result', {}).get('citations', [])
                    print(f"📋 Sync response - Found {len(citations)} citations")
            else:
                print(f"❌ Upload failed: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    quick_pdf_test_fixed()
