import requests
import json
import time

def test_citation_analysis():
    # Test with a local file
    test_file = "test_files/1029764.pdf"
    api_url = "http://localhost:5000/casestrainer/api/analyze"
    
    print(f"Sending file {test_file} to {api_url}...")
    
    with open(test_file, 'rb') as f:
        files = {'file': (test_file, f, 'application/pdf')}
        try:
            response = requests.post(
                api_url,
                files=files,
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending request: {e}")
            return
    
    print(f"Status code: {response.status_code}")
    
    try:
        result = response.json()
        print("Initial response:", json.dumps(result, indent=2))
        
        # Check if this is an async response
        if response.status_code == 202 or (result and result.get('status') == 'processing'):
            print("\nRequest accepted for async processing")
            task_id = result.get('task_id') or result.get('request_id')
            if not task_id:
                print("Error: No task_id or request_id in response")
                return
                
            print(f"Task ID: {task_id}")
            
            # Poll for results
            status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
            max_attempts = 30
            attempt = 0
            last_status = None
            
            while attempt < max_attempts:
                attempt += 1
                print(f"\n--- Polling attempt {attempt}/{max_attempts} ---")
                
                try:
                    status_response = requests.get(status_url, timeout=10)
                    status_data = status_response.json()
                    print(f"Status: {json.dumps(status_data, indent=2)}")
                    
                    status = status_data.get('status')
                    
                    # Check for completion
                    if status == 'completed' or status_data.get('result'):
                        print("\n✅ Analysis completed successfully!")
                        result_data = status_data.get('result', {})
                        print(f"Citations found: {len(result_data.get('citations', []))}")
                        print(f"Clusters found: {len(result_data.get('clusters', []))}")
                        
                        # Save results to file
                        with open('test_results.json', 'w') as f:
                            json.dump(status_data, f, indent=2)
                        print("Results saved to test_results.json")
                        return
                        
                    elif status in ('failed', 'error'):
                        error_msg = status_data.get('error', 'Unknown error')
                        print(f"\n❌ Analysis failed: {error_msg}")
                        if 'traceback' in status_data:
                            print("\nTraceback:", status_data['traceback'])
                        return
                        
                    # Show progress
                    if status != last_status:
                        print(f"Status changed: {last_status} -> {status}")
                        last_status = status
                    
                    # Show progress if available
                    if 'progress' in status_data:
                        print(f"Progress: {status_data['progress']}%")
                    
                except requests.exceptions.RequestException as e:
                    print(f"Error polling status: {str(e)}")
                
                # Wait before polling again with exponential backoff
                wait_time = min(2 ** (attempt // 3), 10)  # Cap at 10 seconds
                print(f"Waiting {wait_time} seconds before next poll...")
                time.sleep(wait_time)
            
            print("\n⚠️ Max polling attempts reached. Analysis may still be in progress.")
            
        else:
            # Immediate response
            print("\nReceived immediate response:")
            print(json.dumps(result, indent=2))
            
    except json.JSONDecodeError:
        print("Error: Could not parse response as JSON")
        print("Response content:", response.text)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Response content: {response.text}")

if __name__ == "__main__":
    test_citation_analysis()
