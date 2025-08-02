"""Test direct API access to the backend service with detailed error reporting."""
import requests
import json
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_test.log')
    ]
)
logger = logging.getLogger(__name__)

def make_api_request(url, method='get', data=None, headers=None):
    """Make an API request with detailed error handling."""
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        logger.info(f"{method.upper()} {url} - Status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        try:
            logger.debug(f"Response content: {response.text}")
            if response.text:
                return response.json()
            return {}
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON response: {response.text}")
            return {"error": "Invalid JSON response", "content": response.text}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}

def test_direct_api():
    """Test direct access to the backend API with detailed logging."""
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    base_url = "http://localhost:5000"
    
    # Test health endpoint first
    logger.info("Testing health endpoint...")
    health_url = f"{base_url}/casestrainer/api/health"
    health_response = make_api_request(health_url, 'get')
    logger.info(f"Health check: {health_response}")
    
    # Test API endpoint
    logger.info("Testing API endpoint...")
    api_url = f"{base_url}/casestrainer/api/analyze"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "text": test_text,
        "document_type": "test"
    }
    
    # Make the API request
    logger.info(f"Sending request to {api_url}")
    response = make_api_request(api_url, 'post', payload, headers)
    
    if isinstance(response, dict) and 'error' in response:
        logger.error(f"API request failed: {response}")
        return
        
    # If we got a task ID, try to get results
    task_id = response.get('task_id')
    if task_id:
        logger.info(f"Got task ID: {task_id}")
        
        # Try to get results with retries
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            logger.info(f"Checking results (attempt {attempt}/{max_retries})...")
            results_url = f"{base_url}/casestrainer/api/analyze/results/{task_id}"
            result = make_api_request(results_url, 'get', headers=headers)
            
            if result and 'status' in result:
                status = result.get('status')
                logger.info(f"Task status: {status}")
                
                if status == 'completed':
                    logger.info("Task completed successfully!")
                    logger.info(f"Results: {json.dumps(result, indent=2)}")
                    break
                elif status == 'error':
                    logger.error(f"Task failed: {result.get('message', 'Unknown error')}")
                    break
                else:
                    logger.info(f"Task in progress: {status}")
            
            if attempt < max_retries:
                import time
                time.sleep(2)  # Wait before next attempt
    
    logger.info("Test completed.")

if __name__ == "__main__":
    logger.info("Starting API test...")
    test_direct_api()
    logger.info("Test finished. Check api_test.log for details.")
