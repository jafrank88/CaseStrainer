#!/usr/bin/env python3
"""
Check# Use the most recent task ID from the test
"""
import requests
import json

def check_task_status():
    task_id = "5aa5eeac-bb29-467d-9661-fb0a7c5e9426"  # Will be updated by test_pdf_url.py
    
    try:
        response = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}", verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
            
            # Check if we have results
            if result.get('result'):
                citations = result['result'].get('citations', [])
                clusters = result['result'].get('clusters', [])
                print(f"\n=== SUMMARY ===")
                print(f"Citations found: {len(citations)}")
                print(f"Clusters found: {len(clusters)}")
                
                if citations:
                    print(f"\nFirst 5 citations:")
                    for i, citation in enumerate(citations[:5], 1):
                        print(f"\n{i}. {citation.get('citation', 'N/A')}")
                        print(f"   Case: {citation.get('case_name', 'N/A')}")
                        print(f"   Verified: {citation.get('verified', False)}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_task_status()
