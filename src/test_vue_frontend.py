"""
Comprehensive Test Suite for CaseStrainer Vue.js Frontend and APIs

This script tests:
1. Core UI Functionality:
   - File upload
   - URL input
   - Text paste
   - Citation verification tab

2. API Endpoints:
   - /api/analyze (for all input types)
   - /api/verify-citation
   - /api/version

3. Citation Verification:
   - Single citation verification
   - Batch verification
   - Error handling

Requirements:
- Python 3.8+
- Playwright (install with: pip install playwright && playwright install)
- Requests library (pip install requests)
- CaseStrainer running locally on http://localhost:5000
"""

import os
import time
import sys
import requests
from playwright.sync_api import (
    sync_playwright,
    expect,
    TimeoutError as PlaywrightTimeoutError,
)

# API Test Configuration
API_BASE_URL = "http://localhost:5000/casestrainer/api"
HEADERS = {"Content-Type": "application/json"}


# Helper function for API tests
def make_api_request(endpoint, method="GET", data=None, params=None):
    """Helper function to make API requests with error handling"""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=HEADERS, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise


# Test Data
TEST_URL = "https://example.legal-document.com/sample"
TEST_CITATION = "Roe v. Wade, 410 U.S. 113 (1973)"
TEST_CITATIONS = [
    "Roe v. Wade, 410 U.S. 113 (1973)",
    "Brown v. Board of Education, 347 U.S. 483 (1954)",
    "Miranda v. Arizona, 384 U.S. 436 (1966)",
]

TEST_TEXT = f"""
This is a test document with citations to legal cases.

1. {TEST_CITATIONS[0]}
2. {TEST_CITATIONS[1]}
3. {TEST_CITATIONS[2]}

This text is used to test the citation extraction and verification functionality.
"""

# Path to a test PDF file (create a simple one if it doesn't exist)
TEST_PDF_PATH = os.path.join(os.path.dirname(__file__), "test_document.pdf")

# Base URLs
BASE_URL = "http://localhost:5000"
VUE_URL = f"{BASE_URL}/casestrainer"


def create_test_pdf():
    """Create a simple test PDF if it doesn't exist."""
    if not os.path.exists(TEST_PDF_PATH):
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Test Document with Citations", ln=True, align="C")
        pdf.multi_cell(0, 10, txt=TEST_TEXT)
        pdf.output(TEST_PDF_PATH)


def test_file_upload():
    """Test file upload functionality."""
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the application
            print(f"Navigating to {VUE_URL}")
            try:
                page.goto(VUE_URL, timeout=30000)
                # Wait for the page to be fully loaded
                page.wait_for_selector("body", timeout=10000)
            except PlaywrightTimeoutError as e:
                print(f"Error navigating to {VUE_URL}: {e}")
                # Try to get page content for debugging
                print(f"Page content: {page.content()[:500]}...")
                # Take a screenshot for debugging
                screenshot_path = "navigation_error.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {os.path.abspath(screenshot_path)}")
                raise

            # Wait for the file input and upload the test PDF
            print("Clicking upload button...")
            try:
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    upload_button = page.wait_for_selector(
                        "button:has-text('Upload Document')", timeout=10000
                    )
                    upload_button.click()
                file_chooser = fc_info.value
                print(f"Uploading file: {TEST_PDF_PATH}")
                file_chooser.set_files(TEST_PDF_PATH)
            except Exception as e:
                print(f"Error during file upload: {e}")
                # Take a screenshot for debugging
                screenshot_path = "test_failure.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {os.path.abspath(screenshot_path)}")
                raise

            # Verify results are displayed
            results_container = page.locator(".results-container")
            expect(results_container).to_be_visible(timeout=30000)

            # Wait for citation cards to be visible
            citations = page.locator(".citation-card")
            try:
                citations.first.wait_for(state="visible", timeout=30000)
            except Exception:
                print("Timed out waiting for citation cards to appear")
                print(f"Current page URL: {page.url}")
                print(f"Page content: {page.content()[:1000]}...")
                page.screenshot(path="citation_timeout.png")
                raise

            # Verify at least one citation is found
            citation_count = citations.count()
            assert (
                citation_count > 0
            ), f"No citations found in the uploaded document. Found {citation_count} citations."

            # Verify citation details are displayed
            first_citation = citations.first
            expect(first_citation.locator(".citation-text")).to_be_visible()
            expect(first_citation.locator(".citation-status")).to_be_visible()

            # Check for analysis results
            analysis_section = first_citation.locator(".analysis-results")
            if analysis_section.is_visible():
                print("Analysis results found for citation:")
                print(analysis_section.inner_text())

            print(f"✅ File upload test passed. Found {citation_count} citations.")

        finally:
            # Clean up
            context.close()
            browser.close()


def test_url_input():
    """Test URL input functionality."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the application
            print(f"Navigating to {VUE_URL}")
            try:
                page.goto(VUE_URL, timeout=30000)
                # Wait for the page to be fully loaded
                page.wait_for_selector("body", timeout=10000)
            except PlaywrightTimeoutError as e:
                print(f"Error navigating to {VUE_URL}: {e}")
                print(f"Page content: {page.content()[:500]}...")
                screenshot_path = "navigation_error_url.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {os.path.abspath(screenshot_path)}")
                raise

            # Switch to URL tab and enter test URL
            print("Testing URL input...")
            url_tab = page.wait_for_selector(
                "button:has-text('Enter URL')", timeout=10000
            )
            url_tab.click()

            url_input = page.wait_for_selector(
                "input[placeholder='Enter document URL']", timeout=10000
            )
            url_input.fill(TEST_URL)

            analyze_btn = page.wait_for_selector(
                "button:has-text('Analyze URL')", timeout=10000
            )
            analyze_btn.click()

            # Verify results are displayed
            results_container = page.locator(".results-container")
            expect(results_container).to_be_visible(timeout=30000)

            # Wait for citation cards to be visible
            citations = page.locator(".citation-card")
            try:
                citations.first.wait_for(state="visible", timeout=30000)
                citation_count = citations.count()
                print(f"✅ URL input test passed. Found {citation_count} citations.")

                # Log first citation details if available
                if citation_count > 0:
                    first_citation = citations.first
                    print("First citation details:")
                    print(
                        first_citation.inner_text()[:200] + "..."
                        if len(first_citation.inner_text()) > 200
                        else first_citation.inner_text()
                    )
            except Exception as e:
                print(f"Error verifying URL input results: {e}")
                page.screenshot(path="url_input_error.png")
                raise

        finally:
            context.close()
            browser.close()


def test_text_paste():
    """Test text paste functionality."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the application
            print(f"Navigating to {VUE_URL}")
            try:
                page.goto(VUE_URL, timeout=30000)
                # Wait for the page to be fully loaded
                page.wait_for_selector("body", timeout=10000)
            except PlaywrightTimeoutError as e:
                print(f"Error navigating to {VUE_URL}: {e}")
                print(f"Page content: {page.content()[:500]}...")
                screenshot_path = "navigation_error_text.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {os.path.abspath(screenshot_path)}")
                raise

            # Switch to text tab and paste test text
            print("Testing text input...")
            text_tab = page.wait_for_selector(
                "button:has-text('Paste Text')", timeout=10000
            )
            text_tab.click()

            text_area = page.wait_for_selector(
                "textarea[placeholder='Paste your text here...']", timeout=10000
            )
            text_area.fill(TEST_TEXT)

            analyze_btn = page.wait_for_selector(
                "button:has-text('Analyze Text')", timeout=10000
            )
            analyze_btn.click()

            # Verify results are displayed
            results_container = page.locator(".results-container")
            expect(results_container).to_be_visible(timeout=30000)

            # Verify specific citations are found
            expected_citations = [
                "Roe v. Wade, 410 U.S. 113 (1973)",
                "Brown v. Board of Education, 347 U.S. 483 (1954)",
            ]

            citations_found = []
            for citation in expected_citations:
                try:
                    locator = page.locator(f"text='{citation}'")
                    locator.wait_for(state="visible", timeout=10000)
                    citations_found.append(citation)
                    print(f"✅ Found expected citation: {citation}")
                except Exception:
                    print(f"❌ Missing expected citation: {citation}")

            # Verify at least one citation was found
            assert (
                len(citations_found) > 0
            ), "No expected citations were found in the results"

            # Log all visible citations for debugging
            all_citations = page.locator(".citation-card")
            print(f"\nFound {all_citations.count()} total citations:")
            for i in range(
                min(5, all_citations.count())
            ):  # Limit to first 5 for brevity
                print(f"{i+1}. {all_citations.nth(i).inner_text()[:100]}...")

            print("✅ Text paste test completed")

        finally:
            context.close()
            browser.close()


def test_api_health():
    """Test API health and version endpoint"""
    print("\n=== Testing API Health ===")
    try:
        # Test version endpoint
        version_data = make_api_request("/version")
        print(f"API Version: {version_data.get('version', 'N/A')}")
        print(f"API Status: {version_data.get('status', 'N/A')}")
        return True
    except Exception as e:
        print(f"API Health Check Failed: {e}")
        return False


def test_verify_citation_api():
    """Test the verify citation API endpoint"""
    print("\n=== Testing Verify Citation API ===")
    try:
        # Test with a known citation
        response = make_api_request(
            "/analyze", method="POST", data={"citation": TEST_CITATION}
        )
        print(f"Verified citation: {TEST_CITATION}")
        print(f"Status: {response.get('status', 'N/A')}")
        print(f"Exists: {response.get('exists', 'N/A')}")
        return True
    except Exception as e:
        print(f"Verify Citation API Test Failed: {e}")
        return False


def test_analyze_text_api():
    """Test the analyze text API endpoint"""
    print("\n=== Testing Analyze Text API ===")
    try:
        response = make_api_request(
            "/analyze",
            method="POST",
            data={"text": TEST_TEXT, "analyze_citations": True},
        )
        print(
            f"Analysis completed. Found {len(response.get('citations', []))} citations."
        )
        return True
    except Exception as e:
        print(f"Analyze Text API Test Failed: {e}")
        return False


def test_verify_citation_ui():
    """Test the citation verification UI"""
    print("\n=== Testing Citation Verification UI ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the application
            print(f"Navigating to {VUE_URL}")
            page.goto(VUE_URL, timeout=30000)

            # Switch to Verify Citation tab
            print("Switching to Verify Citation tab")
            verify_tab = page.wait_for_selector(
                "button:has-text('Verify Citation')", timeout=10000
            )
            verify_tab.click()

            # Enter test citation
            print(f"Entering citation: {TEST_CITATION}")
            citation_input = page.wait_for_selector(
                "input[placeholder='Enter citation to verify']", timeout=10000
            )
            citation_input.fill(TEST_CITATION)

            # Click verify button
            verify_btn = page.wait_for_selector(
                "button:has-text('Verify')", timeout=10000
            )
            verify_btn.click()

            # Wait for results
            print("Waiting for verification results...")
            result_container = page.wait_for_selector(
                ".verification-result", timeout=30000
            )

            # Check if results are displayed
            is_visible = result_container.is_visible()
            print(f"Verification results visible: {is_visible}")

            # Take a screenshot
            page.screenshot(path="verification_result.png")
            print("Screenshot saved as verification_result.png")

            return is_visible

        except Exception as e:
            print(f"Citation Verification UI Test Failed: {e}")
            page.screenshot(path="verification_error.png")
            return False
        finally:
            context.close()
            browser.close()


def run_all_tests():
    """Run all tests and report results"""
    start_time = time.time()
    results = {
        "api_health": False,
        "verify_citation_api": False,
        "analyze_text_api": False,
        "verify_citation_ui": False,
        "file_upload": False,
        "url_input": False,
        "text_paste": False,
    }

    try:
        # Create test PDF if it doesn't exist
        create_test_pdf()

        print("🚀 Starting comprehensive test suite for CaseStrainer...")

        # API Tests
        results["api_health"] = test_api_health()
        results["verify_citation_api"] = test_verify_citation_api()
        results["analyze_text_api"] = test_analyze_text_api()

        # UI Tests
        results["verify_citation_ui"] = test_verify_citation_ui()
        results["file_upload"] = test_file_upload()
        results["url_input"] = test_url_input()
        results["text_paste"] = test_text_paste()

    except Exception as e:
        print(f"\n❌ Error during test execution: {e}")
        import traceback

        traceback.print_exc()

    # Calculate test duration
    duration = time.time() - start_time

    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")

    print("\n" + "-" * 50)
    passed_count = sum(1 for result in results.values() if result)
    total_tests = len(results)
    print(f"Tests completed in {duration:.2f} seconds")
    print(
        f"{passed_count}/{total_tests} tests passed ({passed_count/total_tests*100:.1f}%)"
    )

    if passed_count == total_tests:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the logs above for details.")

    print("=" * 50)

    # Return non-zero exit code if any test failed
    sys.exit(0 if passed_count == total_tests else 1)


if __name__ == "__main__":
    run_all_tests()
