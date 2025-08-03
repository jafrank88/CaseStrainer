"""
Test script for the /casestrainer/api/analyze endpoint

This script tests various input types and edge cases for the analyze endpoint.
"""

import os
import sys
import json
import requests
from pathlib import Path
from urllib.parse import urljoin

# Configuration
# Use the production URL by default, but allow override with environment variable
import os
BASE_URL = os.environ.get('CASE_STRAINER_URL', 'http://localhost:5000/casestrainer/api')

# Add proper SSL verification handling
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure session to handle cookies and headers
session = requests.Session()
session.verify = False  # Disable SSL verification for testing
session.headers.update({
    'User-Agent': 'CaseStrainer-Test-Script/1.0',
    'Accept': 'application/json',
})
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
TEST_PDF = os.path.join(TEST_FILES_DIR, "test_case.pdf")  # Using existing test PDF
TEST_TEXT = """
The Supreme Court held in Brown v. Board of Education, 347 U.S. 483 (1954),
that racial segregation in public schools was unconstitutional. This decision
overruled the "separate but equal" principle established in Plessy v. Ferguson,
163 U.S. 537 (1896).
"""

def print_section(title):
    """Print a section header for test output"""
    print(f"\n{'='*80}")
    print(f"{title.upper()}")
    print(f"{'='*80}")

def test_health_check():
    """Test the health check endpoint"""
    print_section("Testing Health Check")
    try:
        # Try the standard health endpoint first
        response = session.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health Check (Standard): {response.status_code}")
        
        # If that fails, try the root endpoint
        if response.status_code != 200:
            root_url = BASE_URL.rsplit('/api', 1)[0]  # Remove /api if present
            response = session.get(f"{root_url}/health", timeout=5)
            print(f"Health Check (Root): {response.status_code}")
        
        print(f"Response: {response.text}")
        
        # Try to parse JSON if possible
        try:
            print(f"JSON: {response.json()}")
        except:
            pass
            
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_file_upload():
    """Test file upload functionality with different file types"""
    test_cases = [
        ("PDF File", "test_case.pdf", "application/pdf"),
        ("Text File", "test.txt", "text/plain"),
        ("HTML File", "test.html", "text/html"),
        ("RTF File", "test.rtf", "application/rtf")
    ]
    
    all_passed = True
    
    for file_desc, filename, content_type in test_cases:
        print_section(f"Testing {file_desc} Upload")
        file_path = os.path.join(TEST_FILES_DIR, filename)
        
        if not os.path.exists(file_path):
            print(f"Test file not found: {file_path}")
            all_passed = False
            continue
            
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, content_type)}
                response = requests.post(
                    f"{BASE_URL}/analyze",
                    files=files,
                    timeout=30  # Increase timeout for file processing
                )
                
            print(f"File: {filename}")
            print(f"Status Code: {response.status_code}")
            
            try:
                result = response.json()
                print(f"Success: {result.get('success')}")
                
                if 'error' in result:
                    print(f"Error: {result.get('error')}")
                    print(f"Details: {result.get('details')}")
                    all_passed = False
                else:
                    print(f"Citations found: {len(result.get('citations', []))}")
                    print(f"Clusters found: {len(result.get('clusters', []))}")
                    print(f"Request ID: {result.get('request_id')}")
                    
                    # If this is a background task, check its status
                    if 'task_id' in result and result.get('status') == 'processing':
                        task_success = check_task_status(result['task_id'])
                        all_passed = all_passed and task_success
                    else:
                        all_passed = all_passed and result.get('success', False)
                        
            except ValueError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Response content: {response.text[:500]}...")
                all_passed = False
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            all_passed = False
    
    return all_passed

def test_text_analysis():
    """Test text analysis functionality"""
    print_section("Testing Text Analysis")
    
    test_cases = [
        ("Simple Text", TEST_TEXT, {}),
        ("Text with Options", TEST_TEXT, {
            'extract_case_names': True,
            'verify_citations': True,
            'include_metadata': True
        }),
        ("Empty Text", "", {}),
        ("Text with Invalid Citations", "This is a test with invalid citations like 123 F.3d 4567 and 999 U.S. 999", {})
    ]
    
    all_passed = True
    
    for name, text, options in test_cases:
        print(f"\n--- {name} ---")
        print(f"Text length: {len(text)} characters")
        
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {'text': text}
            if options:
                payload['options'] = options
            
            response = requests.post(
                f"{BASE_URL}/analyze",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            try:
                result = response.json()
                print(f"Success: {result.get('success')}")
                
                if 'error' in result:
                    print(f"Error: {result.get('error')}")
                    print(f"Details: {result.get('details')}")
                    all_passed = all_passed and (response.status_code >= 400)  # Expected error for some cases
                else:
                    print(f"Citations found: {len(result.get('citations', []))}")
                    print(f"Clusters found: {len(result.get('clusters', []))}")
                    print(f"Request ID: {result.get('request_id')}")
                    
                    # Print the first citation details if available
                    if result.get('citations'):
                        first_citation = result['citations'][0]
                        print("\nFirst citation:")
                        print(f"  Text: {first_citation.get('text', 'N/A')}")
                        print(f"  Type: {first_citation.get('type', 'N/A')}")
                        print(f"  Case Name: {first_citation.get('case_name', 'N/A')}")
                        if 'canonical' in first_citation:
                            print(f"  Canonical: {first_citation['canonical'].get('citation', 'N/A')} - {first_citation['canonical'].get('name', 'N/A')}")
                    
                    all_passed = all_passed and result.get('success', False)
                    
            except ValueError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Response content: {response.text[:500]}...")
                all_passed = False
                
        except Exception as e:
            print(f"Error: {e}")
            all_passed = False
    
    return all_passed

def test_url_analysis():
    """Test URL analysis functionality"""
    print_section("Testing URL Analysis")
    
    test_url = "https://www.oyez.org/cases/1952/1"  # Brown v. Board of Education
    
    try:
        # Test with URL in form data
        print("Testing with form data...")
        response = requests.post(
            f"{BASE_URL}/analyze",
            data={'url': test_url}
        )
        
        print(f"Status Code (form): {response.status_code}")
        result = response.json()
        
        print(f"Success: {result.get('success')}")
        if 'error' in result:
            print(f"Error: {result.get('error')}")
            print(f"Details: {result.get('details')}")
        else:
            print(f"Request ID: {result.get('request_id')}")
            if 'task_id' in result:
                print(f"Background task ID: {result.get('task_id')}")
                print(f"Status: {result.get('status')}")
                print(f"Message: {result.get('message')}")
                
                # If this is a background task, we can check its status
                if 'task_id' in result and result.get('status') == 'processing':
                    return check_task_status(result['task_id'])
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_task_status(task_id):
    """Check the status of a background task"""
    print(f"\nChecking task status for task_id: {task_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/task/{task_id}")
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Task Status: {result.get('status')}")
        print(f"Success: {result.get('success')}")
        
        if 'error' in result:
            print(f"Error: {result.get('error')}")
            print(f"Details: {result.get('details')}")
        
        if result.get('status') == 'completed':
            print(f"Citations found: {len(result.get('citations', []))}")
            print(f"Clusters found: {len(result.get('clusters', []))}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"Error checking task status: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("Starting API Endpoint Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Python: {sys.version}")
    print(f"Requests: {requests.__version__}")
    
    # Check if we can access the server
    try:
        response = session.get(BASE_URL.rsplit('/api', 1)[0], timeout=5)
        print(f"Server is accessible. Status code: {response.status_code}")
    except Exception as e:
        print(f"\nERROR: Could not connect to server at {BASE_URL}")
        print(f"Make sure the server is running and accessible.")
        print(f"Error details: {e}")
        print("\nYou can set a different URL using the CASE_STRAINER_URL environment variable.")
        print("Example: set CASE_STRAINER_URL=https://wolf.law.uw.edu/casestrainer/api")
        return 1
    
    # Create test files directory if it doesn't exist
    os.makedirs(TEST_FILES_DIR, exist_ok=True)
    
    # Run tests - start with just health check first
    tests = [
        ("Health Check", test_health_check),
        # Comment out other tests until health check passes
        # ("File Upload", test_file_upload),
        # ("Text Analysis", test_text_analysis),
        # ("URL Analysis", test_url_analysis)
    ]
    
    # If health check passes, run the other tests
    if tests[0][1]():
        tests.extend([
            ("File Upload", test_file_upload),
            ("Text Analysis", test_text_analysis),
            ("URL Analysis", test_url_analysis)
        ])
    
    results = {}
    for name, test_func in tests[1:]:  # Skip health check as we already ran it
        print(f"\n{'='*80}")
        print(f"RUNNING TEST: {name}")
        print(f"{'='*80}")
        results[name] = test_func()
    
    # Print summary
    print_section("Test Summary")
    all_passed = True
    
    # Include health check in results
    health_check_passed = tests[0][1]()
    print(f"Health Check: {'PASSED' if health_check_passed else 'FAILED'}")
    all_passed = all_passed and health_check_passed
    
    # Print other test results
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_tests())
