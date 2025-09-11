import requests
import json

def test_analyze_endpoint():
    # The API endpoint for analysis
    url = "http://localhost:5000/api/analyze"
    
    # The test text with citations
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
    Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
    legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820."""
    
    # Request headers
    headers = {
        'Content-Type': 'application/json',
    }
    
    # Request payload
    payload = {
        'text': test_text
    }
    
    try:
        print("Sending request to /api/analyze endpoint...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("\nAPI Response:")
            print("=" * 80)
            
            # Pretty print the JSON response
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Extract and display just the citations if they exist
            if 'citations' in response_data:
                print("\nExtracted Citations:")
                print("-" * 40)
                for i, citation in enumerate(response_data['citations'], 1):
                    print(f"{i}. {citation.get('text', 'N/A')}")
                    print(f"   - Case Name: {citation.get('extracted_case_name', 'Not found')}")
                    print(f"   - Year: {citation.get('extracted_date', 'Not found')}")
                    print()
            
            print("=" * 80)
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        print("\nPlease ensure the backend service is running and accessible at http://localhost:5000")

if __name__ == "__main__":
    test_analyze_endpoint()
