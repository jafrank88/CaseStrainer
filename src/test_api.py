#!/usr/bin/env python
"""
Test script to directly interact with the CaseStrainer API
"""
import os
import sys
import requests
import json
import time
import logging

# Configure logging to console only
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info("Logging to console")


def test_verify_citation(citation_text, case_name=None):
    """Test the /casestrainer/api/verify-citation endpoint with a citation text."""
    print(
        f"Testing /casestrainer/api/verify-citation endpoint with citation: {citation_text}"
    )
    api_url = "http://127.0.0.1:5000/casestrainer/api/verify-citation"
    payload = {"citation": citation_text}
    if case_name:
        payload["case_name"] = case_name
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")


def test_analyze_text(citation_text):
    """Test the /casestrainer/api/analyze endpoint with pasted text."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING CITATION ANALYSIS FOR TEXT: {citation_text}")
    logger.info(f"{'='*80}\n")

    api_url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}

    # Log the request details
    logger.debug(f"Sending request to {api_url}")
    logger.debug(f"Request headers: {headers}")
    logger.debug(f'Request payload: {{"text": "{citation_text[:100]}..."}}')

    try:
        # Send as JSON with the correct Content-Type header
        start_time = time.time()
        response = requests.post(api_url, json={"text": citation_text}, headers=headers)
        elapsed_time = time.time() - start_time

        # Log response details
        logger.info(f"Response received in {elapsed_time:.2f} seconds")
        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        try:
            result = response.json()
            logger.info("Successfully parsed JSON response")

            # Log detailed citation results
            if "results" in result:
                logger.info(
                    f"Found {len(result['results'])} citation(s) in the response"
                )
                for i, citation_result in enumerate(result["results"], 1):
                    logger.info(f"\n--- Citation {i} ---")

                    # Log basic citation info
                    if "citation" in citation_result:
                        citation = citation_result["citation"]
                        logger.info(f"Citation text: {citation.get('text', 'N/A')}")
                        logger.info(f"Case name: {citation.get('name', 'N/A')}")
                        logger.info(f"Valid: {citation.get('valid', 'N/A')}")

                        # Log metadata if available
                        if "metadata" in citation:
                            logger.info("Metadata:")
                            for key, value in citation["metadata"].items():
                                if value:  # Only log non-null values
                                    logger.info(f"  {key}: {value}")

                    # Log verification details
                    if "details" in citation_result:
                        logger.info("Verification details:")
                        for key, value in citation_result["details"].items():
                            logger.info(f"  {key}: {value}")

                    logger.info(f"Exists: {citation_result.get('exists', 'N/A')}")
                    logger.info(f"Method: {citation_result.get('method', 'N/A')}")

            logger.debug(f"Full response JSON:\n{json.dumps(result, indent=2)}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response (first 1000 chars): {response.text[:1000]}")
        except Exception as e:
            logger.exception(f"Unexpected error processing response: {e}")
            logger.error(f"Raw response (first 1000 chars): {response.text[:1000]}")

    except requests.exceptions.RequestException as e:
        logger.exception(f"Request failed: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

    return None


def test_analyze_url(url):
    """Test the /casestrainer/api/analyze endpoint with a URL input."""
    print(f"Testing /casestrainer/api/analyze endpoint with URL: {url}")
    api_url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}
    try:
        # Send as JSON with the correct Content-Type header
        response = requests.post(api_url, json={"url": url}, headers=headers)
        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    return None


def test_analyze_file(file_path):
    """Test the /casestrainer/api/analyze endpoint with a file upload."""
    print(f"Testing /casestrainer/api/analyze endpoint with file: {file_path}")
    api_url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    try:
        with open(file_path, "rb") as f:
            # Read the file content and send it as text in the JSON payload
            file_content = f.read().decode("utf-8")

        # Send as JSON with the file content
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            api_url,
            json={"text": file_content, "filename": os.path.basename(file_path)},
            headers=headers,
        )

        print(f"Response status code: {response.status_code}")
        try:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"File operation or request failed: {e}")
    return None


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
                        print("Analysis completed!")

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

    # Test with a known good text file first
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test_files",
        "test.txt",
    )
    if os.path.exists(test_file):
        print("\n==== Testing /casestrainer/api/analyze (file upload) ====")
        test_analyze_file(test_file)
    else:
        print("\n==== Skipping file upload test - test file not found ====")
        print(f"Expected test file at: {test_file}")

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
