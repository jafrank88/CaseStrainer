import requests
import os
import time

# Base URL for the API
BASE_URL = "http://localhost:8080/casestrainer"


def test_upload_and_check_tabs():
    """Test uploading a file and checking all tabs for proper data."""
    print("Starting test...")

    # Step 1: Upload a file with citations
    test_file_path = "comprehensive_test_citations.txt"

    if not os.path.exists(test_file_path):
        print(f"Error: Test file {test_file_path} not found")
        return

    with open(test_file_path, "rb") as f:
        files = {"file": f}
        print(f"Uploading test file: {test_file_path}")
        response = requests.post(f"{BASE_URL}/api/analyze", files=files)

    if response.status_code != 200:
        print(f"Error uploading file: {response.status_code} - {response.text}")
        return

    print("File uploaded successfully")
    print(f"Response: {response.json()}")

    # Wait a moment for processing to complete
    print("Waiting for processing to complete...")
    time.sleep(5)

    # Step 2: Check the CourtListener Gaps tab
    print("\nChecking CourtListener Gaps tab...")
    response = requests.get(f"{BASE_URL}/api/courtlistener_gaps")
    if response.status_code != 200:
        print(
            f"Error getting CourtListener gaps: {response.status_code} - {response.text}"
        )
    else:
        data = response.json()
        print(
            f"Found {len(data.get('citations', []))} citations in CourtListener Gaps tab"
        )
        # Check if there's any data and it's not sample data
        if data.get("citations"):
            sample_citations = [
                "Roe v. Wade, 410 U.S. 113 (1973)",
                "Smith v. Jones, 123 U.S. 456 (2000)",
            ]
            found_sample = False
            for citation in data["citations"][:5]:  # Check first 5 citations
                print(f"  - {citation.get('citation_text', '')}")
                if citation.get("citation_text") in sample_citations:
                    found_sample = True

            if found_sample:
                print("WARNING: Sample data found in CourtListener Gaps tab!")
            else:
                print("SUCCESS: No sample data found in CourtListener Gaps tab")
        else:
            print("No citations found in CourtListener Gaps tab")

    # Step 3: Check the Multitool tab
    print("\nChecking Multitool tab...")
    response = requests.get(f"{BASE_URL}/api/confirmed_with_multitool_data")
    if response.status_code != 200:
        print(f"Error getting multitool data: {response.status_code} - {response.text}")
    else:
        data = response.json()
        print(f"Found {len(data.get('citations', []))} citations in Multitool tab")
        # Check if there's any data and it's not sample data
        if data.get("citations"):
            sample_citations = [
                "Roe v. Wade, 410 U.S. 113 (1973)",
                "Brown v. Board of Education, 347 U.S. 483 (1954)",
            ]
            found_sample = False
            for citation in data["citations"][:5]:  # Check first 5 citations
                print(f"  - {citation.get('citation_text', '')}")
                if citation.get("citation_text") in sample_citations:
                    found_sample = True

            if found_sample:
                print("WARNING: Sample data found in Multitool tab!")
            else:
                print("SUCCESS: No sample data found in Multitool tab")
        else:
            print("No citations found in Multitool tab")

    # Step 4: Check the Unconfirmed Citations tab
    print("\nChecking Unconfirmed Citations tab...")
    response = requests.get(f"{BASE_URL}/api/unconfirmed_citations_data")
    if response.status_code != 200:
        print(
            f"Error getting unconfirmed citations: {response.status_code} - {response.text}"
        )
    else:
        data = response.json()
        print(
            f"Found {len(data.get('citations', []))} citations in Unconfirmed Citations tab"
        )
        # Check if there's any data and it's not sample data
        if data.get("citations"):
            sample_citations = [
                "Smith v. Jones, 123 U.S. 456 (2000)",
                "Doe v. State, 789 F.3d 123 (11th Cir. 2015)",
            ]
            found_sample = False
            for citation in data["citations"][:5]:  # Check first 5 citations
                print(f"  - {citation.get('citation_text', '')}")
                if citation.get("citation_text") in sample_citations:
                    found_sample = True

            if found_sample:
                print("WARNING: Sample data found in Unconfirmed Citations tab!")
            else:
                print("SUCCESS: No sample data found in Unconfirmed Citations tab")
        else:
            print("No citations found in Unconfirmed Citations tab")

    print("\nTest completed!")


if __name__ == "__main__":
    test_upload_and_check_tabs()
