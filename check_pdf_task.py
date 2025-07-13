#!/usr/bin/env python3
"""
Check task status for PDF upload to see canonical information results
"""

import requests
import json
import time

def check_task_status(task_id):
    """Check the status of a task"""
    
    url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
    
    print(f"🧪 Checking task status for: {task_id}")
    print(f"URL: {url}")
    print("-" * 50)
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(url, timeout=30)
            
            print(f"Attempt {attempt + 1}: Status Code {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                print(f"Task Status: {status}")
                
                if status == 'completed':
                    print("✅ Task completed! Analyzing results...")
                    
                    # Check citations
                    citations = result.get('citations', [])
                    if citations:
                        print(f"\n🔍 CANONICAL INFORMATION ANALYSIS ({len(citations)} citations):")
                        for i, citation in enumerate(citations):
                            print(f"\nCitation {i + 1}:")
                            print(f"  Citation: {citation.get('citation', 'N/A')}")
                            print(f"  Canonical Name: '{citation.get('canonical_name', 'N/A')}'")
                            print(f"  Canonical Date: '{citation.get('canonical_date', 'N/A')}'")
                            print(f"  Extracted Case Name: '{citation.get('extracted_case_name', 'N/A')}'")
                            print(f"  Extracted Date: '{citation.get('extracted_date', 'N/A')}'")
                            print(f"  Verified: {citation.get('verified', False)}")
                            print(f"  URL: '{citation.get('url', 'N/A')}'")
                            
                            # Check if canonical information is present
                            canonical_name = citation.get('canonical_name')
                            canonical_date = citation.get('canonical_date')
                            
                            if canonical_name and canonical_name != 'N/A':
                                print(f"  ✅ CANONICAL NAME FOUND: {canonical_name}")
                            else:
                                print(f"  ❌ NO CANONICAL NAME")
                                
                            if canonical_date and canonical_date != 'N/A':
                                print(f"  ✅ CANONICAL DATE FOUND: {canonical_date}")
                            else:
                                print(f"  ❌ NO CANONICAL DATE")
                                
                        # Summary
                        verified_count = sum(1 for c in citations if c.get('verified', False))
                        canonical_count = sum(1 for c in citations if c.get('canonical_name') and c.get('canonical_name') != 'N/A')
                        
                        print(f"\n📊 SUMMARY:")
                        print(f"  Total Citations: {len(citations)}")
                        print(f"  Verified Citations: {verified_count}")
                        print(f"  Citations with Canonical Names: {canonical_count}")
                    else:
                        print("⚠️  No citations found in completed task")
                        
                    # Check clusters
                    clusters = result.get('clusters', [])
                    if clusters:
                        print(f"\n🔍 CLUSTER ANALYSIS ({len(clusters)} clusters):")
                        for i, cluster in enumerate(clusters):
                            print(f"\nCluster {i + 1}:")
                            print(f"  Canonical Name: '{cluster.get('canonical_name', 'N/A')}'")
                            print(f"  Canonical Date: '{cluster.get('canonical_date', 'N/A')}'")
                            print(f"  Extracted Case Name: '{cluster.get('extracted_case_name', 'N/A')}'")
                            print(f"  Extracted Date: '{cluster.get('extracted_date', 'N/A')}'")
                            print(f"  Citations Count: {len(cluster.get('citations', []))}")
                    
                    return True
                    
                elif status == 'failed':
                    print(f"❌ Task failed!")
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    return False
                    
                elif status == 'processing':
                    print(f"⏳ Still processing... (attempt {attempt + 1}/{max_attempts})")
                    if 'progress' in result:
                        print(f"Progress: {result.get('progress', 0)}%")
                    if 'current_step' in result:
                        print(f"Current Step: {result.get('current_step', 'Unknown')}")
                else:
                    print(f"❓ Unknown status: {status}")
                    
            else:
                print(f"❌ Status check failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        attempt += 1
        if attempt < max_attempts:
            time.sleep(2)
    
    print(f"⏰ Timeout after {max_attempts} attempts")
    return False

if __name__ == "__main__":
    # Use the task ID from the previous PDF upload
    task_id = "4fb0d4dd-d21d-47ea-9f1b-d1e7e11e9a72"
    check_task_status(task_id) 