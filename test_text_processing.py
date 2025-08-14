"""
Test script for the /analyze endpoint with sample legal text.
"""
import requests
import json
import sys

def test_analyze_endpoint():
    """Test the /analyze endpoint with sample legal text."""
    # Sample legal text with citations
    sample_text = """
    In Luis v. United States, 578 U.S. 5 (2016), the Supreme Court held that 
    a pretrial freeze of untainted assets violates a defendant's Sixth Amendment 
    right to counsel of choice. This decision was later cited in United States 
    v. Jones, 950 F.3d 1106 (9th Cir. 2020), where the court further clarified 
    the scope of this protection. Additionally, the case of Carpenter v. United States, 
    138 S. Ct. 2206 (2018) addressed Fourth Amendment issues in the digital age.
    """
    
    # Endpoint URL - using the Nginx proxy
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Headers with additional security
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Forwarded-Prefix': '/casestrainer',
        'Host': 'wolf.law.uw.edu'
    }
    
    # Request payload
    data = {
        'text': sample_text
    }
    
    try:
        # Make the request with SSL verification disabled for testing
        # In production, you should use proper SSL certificates
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=30,
            verify=False  # Disable SSL verification for testing only
        )
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            result = response.json()
            print("\nResponse JSON:")
            print(json.dumps(result, indent=2))
            
            # Check if we have citations in the response
            if 'citations' in result and result['citations']:
                print("\nCitations found:")
                for i, citation in enumerate(result['citations'], 1):
                    print(f"\nCitation {i}:")
                    print(f"  Extracted Name: {citation.get('extracted_case_name')}")
                    print(f"  Extracted Date: {citation.get('extracted_date')}")
                    print(f"  Canonical Name: {citation.get('canonical_name')}")
                    print(f"  Canonical Date: {citation.get('canonical_date')}")
                    print(f"  Canonical URL: {citation.get('canonical_url')}")
                    print(f"  Verified: {citation.get('verified')}")
            else:
                print("\nNo citations found in response")
                if 'error' in result:
                    print(f"Error: {result['error']}")
        except ValueError:
            print("\nResponse (not JSON):")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return False
    
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing /analyze endpoint...")
    success = test_analyze_endpoint()
    sys.exit(0 if success else 1)
