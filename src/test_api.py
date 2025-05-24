#!/usr/bin/env python
"""
Test script to directly interact with the CaseStrainer API
"""
import os
import sys
import requests
import json
import time


def test_verify_citation(citation_text, case_name=None):
    """Test the /casestrainer/api/verify_citation endpoint with a citation text."""
    print(
        f"Testing /casestrainer/api/verify_citation endpoint with citation: {citation_text}"
    )
    api_url = "http://127.0.0.1:5000/casestrainer/api/verify_citation"
    payload = {"citation": citation_text}
    if case_name:
        payload["case_name"] = case_name
    headers = {"Content-Type": "application/json"}
    response = requests.post(api_url, json=payload, headers=headers)
    print(f"Response status code: {response.status_code}")
    try:
        result = response.json()
        print(f"Response JSON: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Invalid JSON response: {response.text}")


def test_analyze_text(citation_text):
    """Test the /casestrainer/api/analyze endpoint with pasted text."""
    print(f"Testing /casestrainer/api/analyze endpoint with text: {citation_text}")
    api_url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    payload = {"text": citation_text}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Invalid JSON response: {response.text}")
    except Exception as e:
        print(f"Exception during test_analyze_text: {e}")


def test_analyze_url(url):
    """Test the /casestrainer/api/analyze endpoint with a URL input."""
    print(f"Testing /casestrainer/api/analyze endpoint with URL: {url}")
    api_url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    payload = {"url": url}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Invalid JSON response: {response.text}")
    except Exception as e:
        print(f"Exception during test_analyze_url: {e}")


def test_analyze_file(file_path):
    """Test the /casestrainer/api/analyze endpoint with a file upload."""
    print(f"Testing /casestrainer/api/analyze endpoint with file: {file_path}")
    api_url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        response = requests.post(api_url, files=files)
        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Invalid JSON response: {response.text}")


# Deprecated: test_analyze_brief used legacy endpoint and polling, which is no longer supported
# def test_analyze_brief(file_path):
#     ...


def test_analyze_brief(file_path):
    """Test the analyze endpoint with a brief file."""
    print(f"Testing analyze endpoint with file: {file_path}")

    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    # CaseStrainer API endpoint
    api_url = "http://127.0.0.1:5001/analyze"

    # Prepare the file for upload
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}

        # Make the request to the CaseStrainer API
        print(f"Sending file to CaseStrainer API at {api_url}")
        response = requests.post(api_url, files=files)

        # Check response status
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")

        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")

            # If analysis started successfully, poll for results
            if result.get("status") == "success" and "analysis_id" in result:
                analysis_id = result["analysis_id"]
                print(f"Analysis started with ID: {analysis_id}")

                # Poll for analysis results
                status_url = f"http://127.0.0.1:5001/status?id={analysis_id}"
                max_attempts = 60
                attempts = 0

                while attempts < max_attempts:
                    time.sleep(3)  # Wait 3 seconds between polls
                    print(f"Checking status (attempt {attempts+1}/{max_attempts})...")

                    status_response = requests.get(status_url)
                    status_result = status_response.json()

                    print(f"Status response: {json.dumps(status_result, indent=2)}")

                    # Check if analysis is complete
                    if status_result.get("completed", False):
                        print(f"Analysis completed!")

                        # Save the results to a file
                        results_file = f"{os.path.splitext(file_path)[0]}_results.json"
                        with open(results_file, "w", encoding="utf-8") as rf:
                            json.dump(status_result, rf, indent=2)
                        print(f"Results saved to {results_file}")

                        # Extract unconfirmed citations
                        results = status_result.get("results", {})
                        citation_results = results.get("citation_results", [])

                        unconfirmed = []
                        for citation in citation_results:
                            if not citation.get("is_confirmed", False):
                                unconfirmed.append(
                                    {
                                        "citation_text": citation.get(
                                            "citation_text", ""
                                        ),
                                        "confidence": citation.get("confidence", 0),
                                        "explanation": citation.get("explanation", ""),
                                    }
                                )

                        print(f"\nFound {len(unconfirmed)} unconfirmed citations:")
                        for i, citation in enumerate(unconfirmed, 1):
                            print(f"  {i}. {citation['citation_text']}")
                            print(f"     Confidence: {citation['confidence']}")
                            print(f"     Explanation: {citation['explanation']}")

                        return

                    # Print progress
                    progress = status_result.get("progress", 0)
                    total_steps = status_result.get("total_steps", 1)
                    message = status_result.get("message", "")
                    print(f"Progress: {progress}/{total_steps} - {message}")

                    attempts += 1

                print("Timeout waiting for analysis to complete")
            else:
                print(
                    f"Analysis failed to start: {result.get('message', 'Unknown error')}"
                )

        except json.JSONDecodeError:
            print(f"Invalid JSON response: {response.text}")


if __name__ == "__main__":
    print("\n==== Testing /casestrainer/api/verify_citation (single citation) ====")
    test_verify_citation("347 U.S. 483")

    print("\n==== Testing /casestrainer/api/analyze (file upload) ====")
    test_analyze_file("test_files/test.pdf")  # Ensure this file exists

    print("\n==== Testing /casestrainer/api/analyze (pasted text) ====")
    test_analyze_text("Brown v. Board of Education, 347 U.S. 483 (1954)")

    print("\n==== Testing /casestrainer/api/analyze (URL input) ====")
    test_analyze_url(
        "https://www.supremecourt.gov/opinions/USReports/347/347.US.483.pdf"
    )

    # If a file path is provided, use file analysis with the unified endpoint
    if len(sys.argv) == 2:
        file_path = sys.argv[1]
        test_analyze_file(file_path)
    else:
        print(
            "No file argument provided. Running text citation analysis test with sample citation."
        )
        sample_citation = "347 U.S. 483"
        test_analyze_text(sample_citation)
        print(
            "\nTo test a different citation, edit test_api.py or pass a file path as an argument."
        )
