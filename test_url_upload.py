import requests
import json

def test_url_upload():
    # The API endpoint for URL analysis
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # The test URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    # Request headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    # Form data
    data = {
        'url': test_url,
        'type': 'url'
    }
    
    try:
        print(f"Sending request to analyze URL: {test_url}")
        response = requests.post(url, headers=headers, data=data, timeout=60)  # 60 second timeout
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\nAPI Response:")
            print("=" * 80)
            
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2))
                
                # Save the response to a file for further inspection
                with open('url_analysis_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                print("\nResponse saved to url_analysis_response.json")
                
                # Extract and display just the citations if they exist
                if 'citations' in response_data:
                    print("\nExtracted Citations:")
                    print("-" * 40)
                    for i, citation in enumerate(response_data['citations'], 1):
                        print(f"{i}. {citation.get('text', 'N/A')}")
                        print(f"   - Case Name: {citation.get('extracted_case_name', 'Not found')}")
                        print(f"   - Year: {citation.get('extracted_date', 'Not found')}")
                        print(f"   - Verified: {citation.get('is_verified', False)}")
                        print()
                else:
                    print("No citations found in the response")
                    
                # Print any error messages if present
                if 'error' in response_data:
                    print(f"Error: {response_data['error']}")
                    
            except json.JSONDecodeError:
                print(f"Could not parse JSON response. Raw response: {response.text}")
            
            print("=" * 80)
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_url_upload()
