import requests
import json
import time
import sys
from urllib.parse import urljoin

class TestRunner:
    def __init__(self):
        self.base_urls = {
            'flask_direct': 'http://localhost:5000',
            'nginx_http': 'http://localhost',
            'nginx_https': 'https://localhost/casestrainer'
        }
        self.results = {}
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for testing
        
        # Suppress only the InsecureRequestWarning from urllib3
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def test_endpoint(self, name, url, method="GET", data=None, headers=None, timeout=10):
        """Test an endpoint and return the status and response."""
        result = {
            'name': name,
            'url': url,
            'method': method,
            'status': None,
            'response': None,
            'time_ms': 0,
            'error': None
        }
        
        try:
            headers = headers or {}
            if 'Content-Type' not in headers and method.upper() in ["POST", "PUT", "PATCH"]:
                headers['Content-Type'] = 'application/json'

            print(f"\nTesting {name}...")
            print(f"  {method} {url}")
            if data:
                print(f"  Data: {json.dumps(data, indent=2) if isinstance(data, dict) else data}")

            start_time = time.time()
            
            response = self.session.request(
                method.upper(),
                url,
                json=data if isinstance(data, dict) else None,
                data=str(data) if not isinstance(data, dict) else None,
                headers=headers,
                timeout=timeout,
                allow_redirects=False
            )
            
            result['time_ms'] = (time.time() - start_time) * 1000
            result['status'] = response.status_code
            
            try:
                result['response'] = response.json()
            except ValueError:
                result['response'] = response.text
                
            print(f"  Status: {response.status_code}")
            print(f"  Time: {result['time_ms']:.2f}ms")
            
            if response.status_code >= 400:
                print(f"  Error: {result['response']}")
                
        except requests.exceptions.SSLError as e:
            result['error'] = f"SSL Error: {str(e)}"
            print(f"  {result['error']}")
        except requests.exceptions.RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
            print(f"  {result['error']}")
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            print(f"  {result['error']}")
        
        return result

    def run_tests(self):
        print("🚀 Starting comprehensive API endpoint tests...\n")
        
        # Test direct Flask endpoints
        print("\n🔍 Testing direct Flask endpoints (port 5000)")
        print("=" * 50)
        
        # Test root endpoint
        root_test = self.test_endpoint(
            "Root endpoint",
            f"{self.base_urls['flask_direct']}/"
        )
        
        # Test API endpoints
        api_tests = [
            ("Verify citation (POST)", 
             f"{self.base_urls['flask_direct']}/verify-citation", 
             "POST", 
             {"citation": "410 U.S. 113 (1973)"}),
            ("Analyze text (POST)", 
             f"{self.base_urls['flask_direct']}/api/analyze", 
             "POST", 
             {"text": "This is a test citation: 410 U.S. 113 (1973)"}),
        ]
        
        for name, url, method, data in api_tests:
            self.test_endpoint(name, url, method, data)
        
        # Test Nginx endpoints (HTTP)
        print("\n🔍 Testing Nginx HTTP endpoints (port 80)")
        print("=" * 50)
        
        nginx_http_tests = [
            ("Root endpoint (should redirect to HTTPS)", 
             f"{self.base_urls['nginx_http']}/", 
             "GET"),
            ("CaseStrainer endpoint (should redirect to HTTPS)", 
             f"{self.base_urls['nginx_http']}/casestrainer/", 
             "GET"),
        ]
        
        for name, url, method in nginx_http_tests:
            self.test_endpoint(name, url, method)
        
        # Test Nginx endpoints (HTTPS)
        print("\n🔍 Testing Nginx HTTPS endpoints (port 443)")
        print("=" * 50)
        
        nginx_https_tests = [
            ("Root endpoint (HTTPS)", 
             f"{self.base_urls['nginx_https']}/", 
             "GET"),
            ("CaseStrainer API endpoint (HTTPS)", 
             f"{self.base_urls['nginx_https']}/api/analyze", 
             "POST",
             {"text": "This is a test citation: 410 U.S. 113 (1973)"}),
        ]
        
        for test in nginx_https_tests:
            if len(test) == 3:
                name, url, method = test
                self.test_endpoint(name, url, method)
            else:
                name, url, method, data = test
                self.test_endpoint(name, url, method, data)
        
        print("\n✅ All tests completed!")

if __name__ == "__main__":
    tester = TestRunner()
    tester.run_tests()
