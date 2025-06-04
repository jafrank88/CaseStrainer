import requests
import json
import time
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Test server URL
BASE_URL = "http://localhost:5000"


def test_citation_validation():
    """Test the citation validation endpoint."""
    print("\nTesting citation validation...")

    # Test cases from comprehensive_test.txt
    test_citations = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Roe v. Wade, 410 U.S. 113 (1973)",
        "Marbury v. Madison, 5 U.S. 137 (1803)",
        "Smith v. Jones, 123 F.3d 456 (9th Cir. 1999)",
        "Jones v. Smith, 123 F. Supp. 2d 456 (S.D.N.Y. 2001)",
        "People v. Smith, 123 Cal. App. 4th 456 (2005)",
        "Plessy v. Ferguson, 163 U.S. 537 (1896)",
        "Smith v. Jones, 123 F.4th 456 (9th Cir. 1999)",  # Unusual format
        "Smith v. Jones, 999 F.9d 999 (99th Cir. 2999)",  # Malformed
    ]

    for citation in test_citations:
        print(f"\nTesting citation: {citation}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/enhanced-validate-citation",
                json={"citation": citation},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                print(
                    f"Status: {'Verified' if result.get('verified') else 'Not Verified'}"
                )
                print(f"Method: {result.get('validation_method', 'N/A')}")
                print(f"Case Name: {result.get('case_name', 'N/A')}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception: {str(e)}")


def test_document_analysis():
    """Test the document analysis endpoint."""
    print("\nTesting document analysis...")

    # Read test document
    with open(
        os.path.join(os.path.dirname(__file__), "comprehensive_test.txt"), "r"
    ) as f:
        test_document = f.read()

    try:
        response = requests.post(
            f"{BASE_URL}/api/enhanced-analyze",
            data={"text": test_document},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Analysis ID: {result.get('analysis_id')}")
            print(f"Document Length: {result.get('document_length')}")
            print(f"Citations Found: {result.get('citations_count')}")

            # Print grouped results
            grouped_results = result.get("grouped_results", {})
            for group, citations in grouped_results.items():
                print(f"\n{group} Citations ({len(citations)}):")
                for citation in citations[:3]:  # Show first 3 citations in each group
                    print(f"- {citation.get('citation')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")


def test_url_analysis():
    """Test the URL analysis endpoint."""
    print("\nTesting URL analysis...")

    # Test URL (using a sample legal document URL)
    test_url = "https://www.supremecourt.gov/opinions/22pdf/21-476_3f14.pdf"

    try:
        response = requests.post(
            f"{BASE_URL}/api/fetch_url",
            json={"url": test_url},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status')}")
            if result.get("status") == "success":
                print(f"Text Length: {len(result.get('text', ''))}")
                print(f"Eyecite Processed: {result.get('eyecite_processed', False)}")
                print(f"Citations Count: {result.get('citations_count', 0)}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")


def main():
    """Run all tests."""
    print("Starting Enhanced Validator tests...")

    # Wait for the server to start
    print("Waiting for server to start...")
    time.sleep(5)

    # Run tests
    test_citation_validation()
    test_document_analysis()
    test_url_analysis()

    print("\nTests completed!")


if __name__ == "__main__":
    main()
