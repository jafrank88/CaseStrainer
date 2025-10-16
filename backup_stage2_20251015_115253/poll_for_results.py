#!/usr/bin/env python3
"""
Poll the API for the results of an asynchronous task.
"""

import requests
import time
import json

def poll_for_results(task_id, max_attempts=10, delay=2):
    """Poll the API for the results of an asynchronous task."""
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    status_url = f"{base_url}/status/{task_id}"
    
    for attempt in range(max_attempts):
        try:
            print(f"Checking status (attempt {attempt + 1}/{max_attempts})...")
            response = requests.get(status_url)
            response.raise_for_status()
            result = response.json()
            
            # Print progress
            progress = result.get('progress_data', {})
            if progress:
                print(f"Status: {progress.get('status', 'unknown')}")
                print(f"Progress: {progress.get('overall_progress', 0)}%")
                print(f"Current step: {progress.get('current_message', 'N/A')}")
                print()
            
            # Check if processing is complete
            if result.get('status') == 'completed' or progress.get('status') == 'completed':
                return result
                
            if attempt < max_attempts - 1:
                time.sleep(delay)
                
        except requests.exceptions.RequestException as e:
            print(f"Error checking status: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None
    
    print("Max polling attempts reached. Try again later with the task ID.")
    return None

def main():
    # You can either:
    # 1. Run test_pdf_upload.py first to get a task ID, or
    # 2. Manually enter a task ID from a previous run
    
    task_id = input("Enter the task ID (or leave empty to run a new upload): ").strip()
    
    if not task_id:
        # Run the upload script and extract the task ID from the response
        print("No task ID provided. Running a new upload...")
        from test_pdf_upload import upload_pdf
        
        pdf_path = r"D:\dev\casestrainer\1033940.pdf"
        api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        
        result = upload_pdf(pdf_path, api_url)
        if not result:
            print("Upload failed.")
            return
            
        task_id = result.get('request_id')
        if not task_id:
            print("No task ID in the response.")
            print("Response:", json.dumps(result, indent=2))
            return
    
    print(f"\n=== Polling for results with task ID: {task_id} ===\n")
    
    # Poll for results
    result = poll_for_results(task_id, max_attempts=20, delay=3)
    
    # Save the final result
    if result:
        with open('final_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n=== Final Result ===")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        
        if 'citations' in result and result['citations']:
            print("\nCitations:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"{i}. {citation.get('citation', 'N/A')}")
                print(f"   Case: {citation.get('case_name', 'N/A')}")
                print(f"   Page: {citation.get('page', 'N/A')}")
                print()
        
        print(f"\nFull results saved to final_result.json")
    else:
        print("Failed to get results. You can try again later with the task ID:")
        print(task_id)

if __name__ == "__main__":
    main()
