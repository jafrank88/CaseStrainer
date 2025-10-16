import requests
import json
import time
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('task_polling.log')
    ]
)
logger = logging.getLogger(__name__)

def poll_task_status(task_id, max_attempts=60, interval=5):
    """
    Poll the task status endpoint until completion or max attempts.
    
    Args:
        task_id: The task ID to poll
        max_attempts: Maximum number of polling attempts (default: 60)
        interval: Seconds between polling attempts (default: 5)
    """
    
    # Try different possible endpoints for task status
    possible_endpoints = [
        f"https://wolf.law.uw.edu/casestrainer/api/tasks/{task_id}",
        f"https://wolf.law.uw.edu/casestrainer/api/task/{task_id}",
        f"https://wolf.law.uw.edu/casestrainer/api/status/{task_id}",
        f"https://wolf.law.uw.edu/casestrainer/api/results/{task_id}"
    ]
    
    headers = {
        'User-Agent': 'CaseStrainer-Test/1.0',
        'Accept': 'application/json'
    }
    
    for attempt in range(max_attempts):
        logger.info(f"Polling attempt {attempt + 1}/{max_attempts} for task {task_id}")
        
        for endpoint in possible_endpoints:
            try:
                logger.debug(f"Trying endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        status_data = response.json()
                        logger.info(f"Successfully got response from {endpoint}")
                        
                        # Save the response
                        filename = f"task_status_{task_id}_{attempt}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(status_data, f, indent=2, ensure_ascii=False)
                        
                        # Check if task is completed
                        status = status_data.get('status', '').lower()
                        if status in ['completed', 'finished', 'done']:
                            logger.info("Task completed successfully!")
                            
                            # Check for citations
                            citations = (status_data.get('citations') or 
                                       status_data.get('result', {}).get('citations', []))
                            
                            if citations:
                                logger.info(f"Found {len(citations)} citations in completed task")
                                for i, citation in enumerate(citations[:5], 1):
                                    logger.info(f"Citation {i}: {citation.get('text', citation.get('citation', 'N/A'))}")
                            else:
                                logger.warning("No citations found in completed task")
                            
                            return status_data
                            
                        elif status in ['failed', 'error']:
                            logger.error(f"Task failed: {status_data.get('error', 'Unknown error')}")
                            return status_data
                            
                        elif status in ['processing', 'running', 'pending']:
                            logger.info(f"Task still {status}, continuing to poll...")
                            break  # Break from endpoint loop, continue with next attempt
                            
                        else:
                            logger.info(f"Unknown status: {status}, continuing to poll...")
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON response from {endpoint}: {response.text[:200]}")
                        
                elif response.status_code == 404:
                    logger.debug(f"Endpoint {endpoint} not found (404)")
                    continue  # Try next endpoint
                    
                else:
                    logger.warning(f"HTTP {response.status_code} from {endpoint}: {response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for {endpoint}: {e}")
                continue
        
        # Wait before next attempt
        if attempt < max_attempts - 1:
            logger.info(f"Waiting {interval} seconds before next attempt...")
            time.sleep(interval)
    
    logger.error(f"Max polling attempts ({max_attempts}) reached without completion")
    return None

def submit_and_poll_url(url_to_analyze):
    """Submit a URL for analysis and poll for results."""
    
    # Submit the URL for processing
    api_endpoint = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Test/1.0'
    }
    
    data = {
        'url': url_to_analyze,
        'type': 'url'
    }
    
    try:
        logger.info(f"Submitting URL for analysis: {url_to_analyze}")
        response = requests.post(api_endpoint, headers=headers, data=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract task ID
            task_id = (response_data.get('task_id') or 
                      response_data.get('result', {}).get('task_id'))
            
            if task_id:
                logger.info(f"Got task ID: {task_id}")
                logger.info("Starting to poll for results...")
                
                # Poll for results
                result = poll_task_status(task_id)
                return result
            else:
                logger.error("No task ID found in response")
                logger.error(f"Response: {json.dumps(response_data, indent=2)}")
                
        else:
            logger.error(f"Failed to submit URL: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error submitting URL: {e}")
    
    return None

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("CaseStrainer Task Polling Test")
    logger.info("=" * 80)
    
    # Test with the provided URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    # Option 1: Submit new URL and poll
    logger.info("Option 1: Submit new URL and poll for results")
    result = submit_and_poll_url(test_url)
    
    if result:
        logger.info("Successfully got final results!")
    else:
        logger.warning("Failed to get final results")
        
        # Option 2: Poll existing task ID if we have one
        logger.info("\nOption 2: Poll existing task ID")
        existing_task_id = "97209d87-e479-4d3f-9544-440adc1dd443"  # From our previous test
        logger.info(f"Polling existing task: {existing_task_id}")
        result = poll_task_status(existing_task_id, max_attempts=10)
    
    logger.info("=" * 80)
    logger.info("Polling test completed")
