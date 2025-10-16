#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import time
import sys

# Force UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test the PDF upload
pdf_path = r"D:\dev\casestrainer\25-2808.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"  # Test local backend directly

print(f"[UPLOAD] Uploading {pdf_path} to {url}")
print(f"[MODE] Forcing SYNC processing to avoid cache")

with open(pdf_path, 'rb') as f:
    files = {'file': ('25-2808.pdf', f, 'application/pdf')}
    data = {'force_mode': 'sync'}  # Force sync processing
    
    try:
        response = requests.post(url, files=files, data=data, timeout=120)
        print(f"\n[OK] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[RESPONSE] Summary:")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Task ID: {data.get('task_id', data.get('request_id', 'N/A'))}")
            print(f"   Citations: {len(data.get('citations', []))}")
            print(f"   Clusters: {len(data.get('clusters', []))}")
            
            # Check if we have immediate results (sync mode)
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            if len(citations) > 0:
                # Sync mode - results are immediate
                print(f"\n[SYNC] Immediate results received!")
                verified = sum(1 for c in citations if c.get('verified'))
                print(f"\n[RESULTS] Detailed Results:")
                print(f"   Total Citations: {len(citations)}")
                print(f"   Total Clusters: {len(clusters)}")
                print(f"   Verified Citations: {verified}/{len(citations)} ({verified/len(citations)*100:.1f}%)")
                
                # Show ALL case names to check for truncations
                print(f"\n[ALL CASE NAMES]:")
                for i, citation in enumerate(citations, 1):
                    case_name = citation.get('extracted_case_name', 'N/A')
                    citation_text = citation.get('citation', '')
                    verified = citation.get('verified', False)
                    status = "OK" if verified else "FAIL"
                    print(f"   {i}. [{status}] {citation_text[:30]:30s} -> {case_name}")
            
            # Check for both task_id and request_id
            task_id = data.get('task_id') or data.get('request_id')
            
            # If it's async and no immediate results, poll for results
            if task_id and len(citations) == 0:
                print(f"\n[POLLING] Task {task_id}...")
                
                status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                
                for i in range(60):  # Poll for up to 5 minutes
                    time.sleep(5)
                    status_response = requests.get(status_url)
                    status_data = status_response.json()
                    
                    current_status = status_data.get('status', 'unknown')
                    progress = status_data.get('progress', 0)
                    current_step = status_data.get('current_step', 'N/A')
                    
                    print(f"   [{i+1}/60] Status: {current_status} | Progress: {progress}% | Step: {current_step}")
                    
                    if current_status == 'completed':
                        print(f"\n[COMPLETED] Task finished!")
                        
                        # The completed status response contains the full data
                        citations = status_data.get('citations', [])
                        clusters = status_data.get('clusters', [])
                        
                        print(f"   Citations in status_data: {len(citations)}")
                        print(f"   Clusters in status_data: {len(clusters)}")
                        
                        print(f"\n[RESULTS] Detailed Results:")
                        print(f"   Total Citations: {len(citations)}")
                        print(f"   Total Clusters: {len(clusters)}")
                        
                        # Count verified citations
                        verified = sum(1 for c in citations if c.get('verified'))
                        print(f"   Verified Citations: {verified}/{len(citations)} ({verified/len(citations)*100:.1f}%)")
                        
                        # Show sample case names
                        print(f"\n[SAMPLES] Case Names (first 5):")
                        for i, citation in enumerate(citations[:5]):
                            case_name = citation.get('extracted_case_name', 'N/A')
                            verified_status = '[OK]' if citation.get('verified') else '[FAIL]'
                            print(f"   {i+1}. {verified_status} {case_name}")
                        
                        break
                    elif current_status in ['failed', 'error']:
                        print(f"\n[ERROR] Task failed: {status_data.get('message', 'Unknown error')}")
                        break
            else:
                # Immediate results
                citations = data.get('citations', [])
                verified = sum(1 for c in citations if c.get('verified'))
                print(f"\n[IMMEDIATE] Results:")
                if len(citations) > 0:
                    print(f"   Verified: {verified}/{len(citations)} ({verified/len(citations)*100:.1f}%)")
                else:
                    print(f"   No citations found or processing is async without task_id")
        else:
            print(f"\n[ERROR] Response: {response.text}")
            
    except Exception as e:
        print(f"\n[EXCEPTION] {e}")
