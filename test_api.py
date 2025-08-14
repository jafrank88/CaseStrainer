import requests
import json
import os
import sys
import datetime
from urllib.parse import urljoin
from contextlib import redirect_stdout, redirect_stderr

# Configuration
BASE_URL = "http://localhost:5000"  # Update this if your API is hosted elsewhere
ANALYZE_ENDPOINT = urljoin(BASE_URL, "/casestrainer/api/analyze")
TEST_TEXT = "The case of Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) is relevant. Also see Roe v. Wade, 410 U.S. 113 (1973)."

def print_request_debug_info(method, url, headers, data=None, files=None):
    """Print debug information about the request being made."""
    print("\n" + "="*80)
    print(f"TESTING {method} {url}")
    print("-"*80)
    print("HEADERS:", json.dumps(dict(headers), indent=2))
    if data:
        print("BODY (JSON):", json.dumps(data, indent=2))
    if files:
        print("FILES:", {k: v[1] if isinstance(v, tuple) else v for k, v in files.items()})
    print("="*80 + "\n")

def test_text_analysis():
    """Test the /api/analyze endpoint with text input using different content types."""
    # Test 1: JSON content-type with JSON body
    headers = {"Content-Type": "application/json"}
    data = {"text": TEST_TEXT, "type": "text"}
    
    try:
        print("\nTEST 1: JSON content-type with JSON body")
        print_request_debug_info("POST", ANALYZE_ENDPOINT, headers, data=data)
        
        response = requests.post(ANALYZE_ENDPOINT, json=data, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text[:500] + ("..." if len(response.text) > 500 else ""))
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Found {len(result.get('citations', []))} citations.")
            print(f"Processing time: {result.get('processing_time', 'N/A')}s")
            if result.get('citations'):
                print("Sample citation:", json.dumps(result['citations'][0], indent=2))
    
    except Exception as e:
        print(f"Error in test 1: {str(e)}")
    
    # Test 2: Form data with text/plain content-type
    headers = {"Content-Type": "text/plain"}
    
    try:
        print("\nTEST 2: text/plain content-type with raw text")
        print_request_debug_info("POST", ANALYZE_ENDPOINT, headers, data=TEST_TEXT)
        
        response = requests.post(ANALYZE_ENDPOINT, data=TEST_TEXT, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text[:500] + ("..." if len(response.text) > 500 else ""))
        
    except Exception as e:
        print(f"Error in test 2: {str(e)}")
    
    # Test 3: Form data with multipart/form-data content-type
    headers = {}
    files = {
        'file': ('test.txt', TEST_TEXT, 'text/plain'),
        'type': (None, 'text')
    }
    
    try:
        print("\nTEST 3: multipart/form-data with file upload")
        print_request_debug_info("POST", ANALYZE_ENDPOINT, headers, files=files)
        
        response = requests.post(ANALYZE_ENDPOINT, files=files, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text[:500] + ("..." if len(response.text) > 500 else ""))
        
    except Exception as e:
        print(f"Error in test 3: {str(e)}")

def main():
    # Redirect output to a file for better analysis
    output_file = "api_test_output.log"
    print(f"Testing API endpoint: {ANALYZE_ENDPOINT}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Saving output to: {os.path.abspath(output_file)}")
    
    # Run all tests and capture output
    with open(output_file, 'w', encoding='utf-8') as f:
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        # Redirect both stdout and stderr to the file
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            sys.stdout = f
            sys.stderr = f
            
            print(f"Test started at: {datetime.datetime.now()}")
            print(f"Testing API endpoint: {ANALYZE_ENDPOINT}")
            print("-" * 80)
            
            # Run the test
            test_text_analysis()
            
            print("\n" + "=" * 80)
            print(f"Test completed at: {datetime.datetime.now()}")
            
        except Exception as e:
            print(f"\nERROR: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
        finally:
            # Restore original stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    # Print a summary to console
    print("\nTesting complete!")
    print(f"Detailed output saved to: {os.path.abspath(output_file)}")
    
    # Show a preview of the output file
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            print("\n=== BEGIN OUTPUT PREVIEW ===")
            for i, line in enumerate(f):
                if i < 50:  # Show first 50 lines
                    print(line, end='')
                else:
                    print("\n... (output truncated - see file for full details)")
                    break
            print("=== END OUTPUT PREVIEW ===\n")
    except Exception as e:
        print(f"Error showing output preview: {str(e)}")

def run_tests():
    """Run all tests and handle any exceptions."""
    try:
        main()
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())
