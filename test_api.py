import requests
import json
import os

def test_citation_validation():
    # Test direct citation input with valid citations
    valid_citations = [
        "347 U.S. 483",  # Brown v. Board of Education
        "554 U.S. 570",  # District of Columbia v. Heller
        "576 U.S. 644",  # Obergefell v. Hodges
        "163 U.S. 537"   # Plessy v. Ferguson
    ]
    for citation in valid_citations:
        print(f"\nTesting direct citation input: {citation}")
        response = requests.post(
            'http://localhost:5000/api/validate_citations',
            json={'text': citation}
        )
        print("Status Code:", response.status_code)
        print("Response:", json.dumps(response.json(), indent=2))

    # Test PDF file input
    print("\nTesting PDF file input:")
    test_pdf_path = 'test_files/test.pdf'
    if os.path.exists(test_pdf_path):
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = requests.post(
                'http://localhost:5000/api/validate_citations',
                files=files
            )
            print("Status Code:", response.status_code)
            print("Response:", json.dumps(response.json(), indent=2))
    else:
        print(f"Test PDF file not found at {test_pdf_path}")

if __name__ == '__main__':
    test_citation_validation() 