#!/usr/bin/env python3
"""
Comprehensive test script for CaseStrainer that tests all input methods and output tabs
with proper error logging and validation.
"""

import requests
import json
import time
import os
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f'test_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
PROCESSING_TIMEOUT = 30  # seconds
EXPECTED_CITATION_COUNT = 5  # Based on TEST_TEXT

# Test data
TEST_TEXT = """This is a test document with various citations:
Brown v. Board of Education, 347 U.S. 483 (1954)
Roe v. Wade, 410 U.S. 113 (1973)
Marbury v. Madison, 5 U.S. 137 (1803)
Some unverified citation: Smith v. Jones, 123 F.3d 456 (9th Cir. 1999)
Future citation: Future v. Case, 123 F.4th 456 (9th Cir. 2030)"""

TEST_URL = "https://supreme.justia.com/cases/federal/us/347/483/"


@dataclass
class TestResult:
    """Class to store test results."""

    success: bool
    message: str
    details: Dict = None
    error: Optional[Exception] = None


def retry_on_failure(func):
    """Decorator to retry a function on failure."""

    def wrapper(*args, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                time.sleep(RETRY_DELAY)

    return wrapper


def validate_response(
    response: requests.Response, expected_status: int = 200
) -> TestResult:
    """Validate API response."""
    try:
        if response.status_code != expected_status:
            return TestResult(
                success=False,
                message=f"Unexpected status code: {response.status_code}",
                details={
                    "status_code": response.status_code,
                    "response": response.text,
                },
            )

        try:
            data = response.json()
        except json.JSONDecodeError:
            return TestResult(
                success=False,
                message="Invalid JSON response",
                details={"response": response.text},
            )

        return TestResult(success=True, message="Response validated", details=data)
    except Exception as e:
        return TestResult(success=False, message="Error validating response", error=e)


def wait_for_processing(
    analysis_id: str, timeout: int = PROCESSING_TIMEOUT
) -> TestResult:
    """Wait for processing to complete."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/api/status/{analysis_id}", timeout=30)
            result = validate_response(response)
            if result.success:
                status = result.details.get("status")
                if status == "completed":
                    return TestResult(success=True, message="Processing completed")
                elif status == "failed":
                    return TestResult(
                        success=False,
                        message="Processing failed",
                        details=result.details,
                    )
            time.sleep(1)
        except Exception as e:
            return TestResult(
                success=False, message="Error checking processing status", error=e
            )
    return TestResult(
        success=False, message=f"Processing timed out after {timeout} seconds"
    )


def create_test_file() -> Tuple[Optional[str], TestResult]:
    """Create a test file with citations."""
    test_file_path = "test_citations.txt"
    try:
        with open(test_file_path, "w") as f:
            f.write(TEST_TEXT)
        logger.info(f"Created test file: {test_file_path}")
        return test_file_path, TestResult(success=True, message="Test file created")
    except Exception as e:
        logger.error(f"Error creating test file: {str(e)}")
        return None, TestResult(
            success=False, message="Failed to create test file", error=e
        )


@retry_on_failure
def test_file_upload() -> TestResult:
    """Test uploading a file and checking all output tabs."""
    logger.info("\n=== TESTING FILE UPLOAD ===")

    # Create test file
    test_file_path, file_result = create_test_file()
    if not file_result.success:
        return file_result

    try:
        # Upload the file
        logger.info("Uploading test file...")
        with open(test_file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/api/analyze", files=files, timeout=30)

        result = validate_response(response)
        if not result.success:
            return result

        analysis_id = result.details.get("analysis_id")
        citations_count = result.details.get("citations_count")

        if citations_count != EXPECTED_CITATION_COUNT:
            return TestResult(
                success=False,
                message=f"Unexpected citation count: {citations_count} (expected {EXPECTED_CITATION_COUNT})",
                details=result.details,
            )

        logger.info(f"File upload successful: {response.status_code}")
        logger.info(f"Analysis ID: {analysis_id}")
        logger.info(f"Citations found: {citations_count}")

        # Wait for processing
        processing_result = wait_for_processing(analysis_id)
        if not processing_result.success:
            return processing_result

        # Test all output tabs
        tabs_result = check_all_tabs(analysis_id, "file upload")
        return TestResult(
            success=tabs_result.success,
            message="File upload test completed",
            details={"tabs_result": tabs_result},
        )

    except Exception as e:
        return TestResult(success=False, message="Error in file upload test", error=e)
    finally:
        # Clean up
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            logger.info(f"Removed test file: {test_file_path}")


@retry_on_failure
def test_text_paste() -> TestResult:
    """Test pasting text and checking all output tabs."""
    logger.info("\n=== TESTING TEXT PASTE ===")

    try:
        # Submit the text
        logger.info("Submitting test text...")
        response = requests.post(f"{BASE_URL}/api/analyze", data={"text": TEST_TEXT}, timeout=30)

        result = validate_response(response)
        if not result.success:
            return result

        analysis_id = result.details.get("analysis_id")
        citations_count = result.details.get("citations_count")

        if citations_count != EXPECTED_CITATION_COUNT:
            return TestResult(
                success=False,
                message=f"Unexpected citation count: {citations_count} (expected {EXPECTED_CITATION_COUNT})",
                details=result.details,
            )

        logger.info(f"Text submission successful: {response.status_code}")
        logger.info(f"Analysis ID: {analysis_id}")
        logger.info(f"Citations found: {citations_count}")

        # Wait for processing
        processing_result = wait_for_processing(analysis_id)
        if not processing_result.success:
            return processing_result

        # Test all output tabs
        tabs_result = check_all_tabs(analysis_id, "text paste")
        return TestResult(
            success=tabs_result.success,
            message="Text paste test completed",
            details={"tabs_result": tabs_result},
        )

    except Exception as e:
        return TestResult(success=False, message="Error in text paste test", error=e)


@retry_on_failure
def test_url_input() -> TestResult:
    """Test URL input and checking all output tabs."""
    logger.info("\n=== TESTING URL INPUT ===")

    try:
        # Submit the URL
        logger.info(f"Submitting URL: {TEST_URL}")
        data = json.dumps({"url": TEST_URL})
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            f"{BASE_URL}/api/direct_url_analyze", data=data, headers=headers
        , timeout=30)

        result = validate_response(response)
        if not result.success:
            return result

        analysis_id = result.details.get("analysis_id")
        citations_count = result.details.get("citations_count")

        logger.info(f"URL submission successful: {response.status_code}")
        logger.info(f"Analysis ID: {analysis_id}")
        logger.info(f"Citations found: {citations_count}")

        # Wait for processing
        processing_result = wait_for_processing(analysis_id)
        if not processing_result.success:
            return processing_result

        # Test all output tabs
        tabs_result = check_all_tabs(analysis_id, "URL input")
        return TestResult(
            success=tabs_result.success,
            message="URL input test completed",
            details={"tabs_result": tabs_result},
        )

    except Exception as e:
        return TestResult(success=False, message="Error in URL input test", error=e)


# Rename helper functions to avoid pytest collection
@retry_on_failure
def check_verified_tab(analysis_id: str) -> TestResult:
    """Test the Verified Citations tab."""
    logger.info("Testing Verified Citations tab...")
    try:
        response = requests.get(f"{BASE_URL}/api/verified_citations/{analysis_id}", timeout=30)
        result = validate_response(response)
        if not result.success:
            return result

        citations = result.details.get("citations", [])
        logger.info(f"Found {len(citations)} verified citations")

        # Validate citation format
        for citation in citations:
            if not all(key in citation for key in ["citation", "case_name", "year"]):
                return TestResult(
                    success=False,
                    message="Invalid citation format in verified citations",
                    details={"citation": citation},
                )

        return TestResult(
            success=True,
            message=f"Found {len(citations)} verified citations",
            details={"citations": citations},
        )
    except Exception as e:
        return TestResult(
            success=False, message="Error testing verified citations tab", error=e
        )


@retry_on_failure
def check_unconfirmed_tab(analysis_id: str) -> TestResult:
    """Test the Unconfirmed Citations tab."""
    logger.info("Testing Unconfirmed Citations tab...")
    try:
        response = requests.get(f"{BASE_URL}/api/unconfirmed_citations/{analysis_id}", timeout=30)
        result = validate_response(response)
        if not result.success:
            return result

        citations = result.details.get("citations", [])
        logger.info(f"Found {len(citations)} unconfirmed citations")

        # Validate citation format
        for citation in citations:
            if not all(key in citation for key in ["citation", "confidence"]):
                return TestResult(
                    success=False,
                    message="Invalid citation format in unconfirmed citations",
                    details={"citation": citation},
                )

        return TestResult(
            success=True,
            message=f"Found {len(citations)} unconfirmed citations",
            details={"citations": citations},
        )
    except Exception as e:
        return TestResult(
            success=False, message="Error testing unconfirmed citations tab", error=e
        )


@retry_on_failure
def check_courtlistener_tab(analysis_id: str) -> TestResult:
    """Test the CourtListener Cases tab."""
    logger.info("Testing CourtListener Cases tab...")
    try:
        response = requests.get(f"{BASE_URL}/api/courtlistener_cases/{analysis_id}", timeout=30)
        result = validate_response(response)
        if not result.success:
            return result

        cases = result.details.get("cases", [])
        logger.info(f"Found {len(cases)} CourtListener cases")

        # Validate case format
        for case in cases:
            if not all(key in case for key in ["case_name", "citation", "court"]):
                return TestResult(
                    success=False,
                    message="Invalid case format in CourtListener cases",
                    details={"case": case},
                )

        return TestResult(
            success=True,
            message=f"Found {len(cases)} CourtListener cases",
            details={"cases": cases},
        )
    except Exception as e:
        return TestResult(
            success=False, message="Error testing CourtListener cases tab", error=e
        )


@retry_on_failure
def check_courtlistener_gaps_tab(analysis_id: str) -> TestResult:
    """Test the CourtListener Gaps tab."""
    logger.info("Testing CourtListener Gaps tab...")
    try:
        response = requests.get(f"{BASE_URL}/api/courtlistener_gaps/{analysis_id}", timeout=30)
        result = validate_response(response)
        if not result.success:
            return result

        gaps = result.details.get("gaps", [])
        logger.info(f"Found {len(gaps)} CourtListener gaps")

        # Validate gap format
        for gap in gaps:
            if not all(key in gap for key in ["citation", "reason"]):
                return TestResult(
                    success=False,
                    message="Invalid gap format in CourtListener gaps",
                    details={"gap": gap},
                )

        return TestResult(
            success=True,
            message=f"Found {len(gaps)} CourtListener gaps",
            details={"gaps": gaps},
        )
    except Exception as e:
        return TestResult(
            success=False, message="Error testing CourtListener gaps tab", error=e
        )


@retry_on_failure
def check_google_scholar_tab(analysis_id: str) -> TestResult:
    """Test the Google Scholar Cases tab."""
    logger.info("Testing Google Scholar Cases tab...")
    try:
        response = requests.get(f"{BASE_URL}/api/google_scholar_cases/{analysis_id}", timeout=30)
        result = validate_response(response)
        if not result.success:
            return result

        cases = result.details.get("cases", [])
        logger.info(f"Found {len(cases)} Google Scholar cases")

        # Validate case format
        for case in cases:
            if not all(key in case for key in ["title", "citation", "url"]):
                return TestResult(
                    success=False,
                    message="Invalid case format in Google Scholar cases",
                    details={"case": case},
                )

        return TestResult(
            success=True,
            message=f"Found {len(cases)} Google Scholar cases",
            details={"cases": cases},
        )
    except Exception as e:
        return TestResult(
            success=False, message="Error testing Google Scholar cases tab", error=e
        )


def check_all_tabs(analysis_id: str, input_method: str) -> TestResult:
    """Test all output tabs for a given analysis ID."""
    logger.info(f"\nTesting all output tabs for {input_method}...")

    success = True
    tab_results = {}
    tabs = {
        "Verified Citations": check_verified_tab,
        "Unconfirmed Citations": check_unconfirmed_tab,
        "CourtListener Cases": check_courtlistener_tab,
        "CourtListener Gaps": check_courtlistener_gaps_tab,
        "Google Scholar Cases": check_google_scholar_tab,
    }

    for tab_name, test_func in tabs.items():
        logger.info(f"\nTesting {tab_name} tab...")
        try:
            result = test_func(analysis_id)
            tab_results[tab_name] = result
            if not result.success:
                logger.error(f"{tab_name} tab test failed: {result.message}")
                success = False
        except Exception as e:
            logger.error(f"Error testing {tab_name} tab: {str(e)}")
            tab_results[tab_name] = TestResult(
                success=False, message=f"Error testing {tab_name} tab", error=e
            )
            success = False

    return TestResult(
        success=success,
        message=f"Tab testing completed for {input_method}",
        details={"tab_results": tab_results},
    )


def run_all_tests() -> None:
    """Run all tests for all input methods and output tabs."""
    logger.info("=== STARTING COMPREHENSIVE TESTING ===")
    logger.info("Testing all 3 input methods with all 5 output tabs")

    start_time = time.time()
    results = {
        "file_upload": test_file_upload(),
        "text_paste": test_text_paste(),
        "url_input": test_url_input(),
    }
    end_time = time.time()

    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Total test time: {end_time - start_time:.2f} seconds")

    all_success = True
    for test_name, result in results.items():
        status = "SUCCESS" if result.success else "FAILED"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        if not result.success:
            all_success = False
            logger.error(f"Error: {result.message}")
            if result.error:
                logger.error(f"Exception: {str(result.error)}")
                logger.error(traceback.format_exc())
            if result.details:
                logger.error(f"Details: {json.dumps(result.details, indent=2)}")

    if all_success:
        logger.info("\nAll tests PASSED!")
    else:
        logger.error("\nSome tests FAILED!")


if __name__ == "__main__":
    run_all_tests()
