import requests
import json
import time
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('url_upload_async_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def poll_task_status(task_id, max_attempts=30, interval=2):
    """Poll the task status endpoint until completion or max attempts."""
    status_url = f"http://localhost:5000/casestrainer/api/tasks/{task_id}"
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Polling task status (attempt {attempt + 1}/{max_attempts})")
            response = requests.get(status_url, timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            logger.debug(f"Status response: {json.dumps(status_data, indent=2)}")
            
            if status_data.get('status') == 'completed':
                logger.info("Task completed successfully")
                return status_data
            elif status_data.get('status') == 'failed':
                logger.error(f"Task failed: {status_data.get('error', 'Unknown error')}")
                return status_data
                
            logger.info(f"Task still processing, waiting {interval} seconds...")
            time.sleep(interval)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error polling task status: {e}")
            time.sleep(interval)
    
    logger.error(f"Max polling attempts ({max_attempts}) reached without completion")
    return None

def test_url_upload():
    # The API endpoint for URL analysis
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # The test URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    logger.info(f"Starting URL upload test for: {test_url}")
    
    # Request headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    # Form data
    data = {
        'url': test_url,
        'type': 'url'
    }
    
    try:
        # Step 1: Submit the URL for processing
        logger.info("Sending POST request to API endpoint")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        response.raise_for_status()
        
        # Parse the initial response
        try:
            response_data = response.json()
            logger.info("Initial response received")
            
            # Save the full response to a file
            with open('url_analysis_initial_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            # Check if we got a task ID
            task_id = None
            if 'task_id' in response_data:
                task_id = response_data['task_id']
            elif 'result' in response_data and 'task_id' in response_data['result']:
                task_id = response_data['result']['task_id']
            
            if not task_id:
                logger.error("No task ID found in response")
                logger.error(f"Response: {json.dumps(response_data, indent=2)}")
                return
                
            logger.info(f"Task ID: {task_id}")
            
            # Step 2: Poll for task completion
            logger.info("Polling for task completion...")
            result = poll_task_status(task_id)
            
            if result and 'result' in result and 'citations' in result['result']:
                citations = result['result']['citations']
                logger.info(f"Found {len(citations)} citations in result")
                
                # Save the full result to a file
                with open('url_analysis_final_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                # Print some citation examples
                for i, citation in enumerate(citations[:5], 1):
                    logger.info(f"Citation {i}: {citation.get('text', 'N/A')}")
                    logger.info(f"  - Case: {citation.get('extracted_case_name', 'N/A')}")
                    logger.info(f"  - Year: {citation.get('extracted_date', 'N/A')}")
                    logger.info(f"  - Verified: {citation.get('is_verified', False)}")
            else:
                logger.error("No citations found in result")
                logger.error(f"Result: {json.dumps(result, indent=2) if result else 'No result'}")
                
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response: {je}")
            logger.error(f"Response content: {response.text[:1000]}...")
            
    except requests.exceptions.RequestException as re:
        logger.error(f"Request failed: {re}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    test_url_upload()
