import requests
import json
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_endpoint(url, method="GET", data=None, headers=None, verify_ssl=False):
    """Test an API endpoint and return the response with detailed information."""
    try:
        # Set default headers if not provided
        if headers is None:
            headers = {}
        
        # Ensure Content-Type is set for POST requests with data
        if method.upper() == "POST" and data is not None and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        
        logger.info(f"Testing {method} {url}")
        logger.debug(f"Headers: {headers}")
        if data:
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")
        
        # Make the request
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, verify=verify_ssl)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, verify=verify_ssl)
        else:
            error_msg = f"Unsupported HTTP method: {method}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            content = response_data
            content_type = "json"
        except ValueError:
            content = response.text[:1000]  # First 1000 chars for non-JSON
            content_type = "text"
        
        # Prepare result
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": content_type,
            "content": content,
        }
        
        logger.info(f"Status: {response.status_code}")
        if response.status_code >= 400:
            logger.error(f"Error response: {content}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}

def test_health_check(base_url):
    """Test the health check endpoint."""
    url = urljoin(base_url, "/health")
    print(f"\n{'='*50}")
    print(f"Testing health check: GET {url}")
    result = test_api_endpoint(url, method="GET")
    print(json.dumps(result, indent=2))
    return result

def test_verify_citation(base_url):
    """Test the verify-citation endpoint."""
    url = urljoin(base_url, "/verify-citation")
    print(f"\n{'='*50}")
    print(f"Testing verify-citation: POST {url}")
    
    # Test data
    test_data = {"citation": "410 U.S. 113 (1973)"}
    
    # Make the request
    result = test_api_endpoint(
        url=url,
        method="POST",
        data=test_data,
        headers={"Content-Type": "application/json"},
    )
    
    print(json.dumps(result, indent=2))
    return result

def test_analyze_endpoint(base_url):
    """Test the analyze endpoint with sample text."""
    url = urljoin(base_url, "/analyze")
    print(f"\n{'='*50}")
    print(f"Testing analyze endpoint: POST {url}")
    
    # Test data
    test_data = {"text": "This is a test with citation 534 F.3d 1290"}
    
    # Make the request
    result = test_api_endpoint(
        url=url,
        method="POST",
        data=test_data,
        headers={"Content-Type": "application/json"},
    )
    
    print(json.dumps(result, indent=2))
    return result

def list_available_endpoints(base_url):
    """List all available API endpoints."""
    print("\n" + "="*50)
    print("AVAILABLE API ENDPOINTS:")
    print("="*50)
    print(f"  GET     {urljoin(base_url, '/version')}")
    print(f"  GET     {urljoin(base_url, '/health')}")
    print(f"  POST    {urljoin(base_url, '/analyze')}")
    print(f"  POST    {urljoin(base_url, '/verify-citation')}")
    print(f"  GET     {urljoin(base_url, '/confirmed_with_multitool_data')}")
    print(f"  GET     {urljoin(base_url, '/processing_progress')}")
    print(f"  POST    {urljoin(base_url, '/validate_citations')}")
    print("="*50 + "\n")

def main():
    # Base URL for the API
    base_url = "http://localhost:5000/casestrainer/api"
    
    # List available endpoints
    list_available_endpoints(base_url)
    
    # Run tests
    test_health_check(base_url)
    test_verify_citation(base_url)
    test_analyze_endpoint(base_url)


if __name__ == "__main__":
    main()
