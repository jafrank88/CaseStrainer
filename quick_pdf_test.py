#!/usr/bin/env python3
"""
Quick PDF test with immediate polling
"""

import requests
import json
import os
import time

def quick_pdf_test():
    """Quick test with immediate polling"""
    
    print("🚀 QUICK PDF TEST")
    print("=" * 40)
    
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
                    
                    # Poll immediately and frequently
                    for i in range(60):  # Try for 3 minutes
                        try:
                            poll_response = requests.get(f"http://localhost:5000/casestrainer/api/task/{task_id}")
                            
                            if poll_response.status_code == 200:
                                poll_result = poll_response.json()
                                status = poll_result.get('status', 'unknown')
                                
                                print(f"   Check {i+1}: Status = {status}")
                                
                                if status == 'completed':
                                    citations = poll_result.get('result', {}).get('citations', [])
                                    print(f"   ✅ COMPLETED! Found {len(citations)} citations")
                                    
                                    # Quick verification check
                                    paradox_count = 0
                                    for citation in citations[:20]:  # Check first 20
                                        has_canonical = bool(
                                            citation.get('canonical_name') and 
                                            citation.get('canonical_date') and 
                                            citation.get('canonical_url')
                                        )
                                        verified = citation.get('verified', False)
                                        
                                        if has_canonical and not verified:
                                            paradox_count += 1
                                    
                                    if paradox_count == 0 and citations:
                                        print(f"   ✅ VERIFICATION PARADOX FIXED!")
                                    elif paradox_count > 0:
                                        print(f"   ⚠️  Found {paradox_count} citations with verification paradox")
                                    
                                    return
                                    
                                elif status == 'failed':
                                    print(f"   ❌ FAILED: {poll_result.get('error', 'Unknown error')}")
                                    return
                            
                            elif poll_response.status_code == 404:
                                print(f"   Check {i+1}: Task not found yet (still processing)")
                            
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
    quick_pdf_test()
