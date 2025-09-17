import requests
import json
import os

def test_file_upload():
    # The API endpoint for file upload
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Path to a test file (you may need to adjust this)
    test_file_path = "test_document.pdf"
    
    # Check if test file exists
    if not os.path.exists(test_file_path):
        print(f"Error: Test file not found at {test_file_path}")
        print("Please make sure the file exists and try again.")
        return
    
    # Prepare the file for upload
    files = {
        'file': (os.path.basename(test_file_path), open(test_file_path, 'rb'), 'application/pdf')
    }
    
    # Additional form data
    data = {
        'type': 'file',
        'source': 'file_upload'
    }
    
    try:
        print(f"Uploading file: {test_file_path}")
        response = requests.post(url, files=files, data=data, timeout=300)  # 5 minute timeout
        
        print(f"Status code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print("Response JSON:")
            print(json.dumps(response_data, indent=2))
            
            # Save the full response to a file
            with open('file_upload_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            # Check if we have citations in the response
            if 'citations' in response_data:
                citations = response_data['citations']
                print(f"\nFound {len(citations)} citations:")
                for i, citation in enumerate(citations[:5], 1):
                    print(f"{i}. {citation.get('text', 'N/A')}")
                    print(f"   - Case: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"   - Year: {citation.get('extracted_date', 'N/A')}")
                    print(f"   - Verified: {citation.get('is_verified', False)}")
                    print()
            else:
                print("\nNo citations found in the response")
                
        except json.JSONDecodeError as je:
            print(f"Failed to parse JSON response: {je}")
            print(f"Response content: {response.text[:1000]}...")
            
    except requests.exceptions.RequestException as re:
        print(f"Request failed: {re}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_file_upload()
