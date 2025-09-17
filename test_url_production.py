import requests
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('url_production_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_url_upload_production():
    """Test URL upload functionality using the production endpoint."""
    
    # The correct production API endpoint
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # The test URL provided by the user
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    logger.info(f"Testing URL upload with production endpoint: {url}")
    logger.info(f"Target PDF URL: {test_url}")
    
    # Request headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Test/1.0'
    }
    
    # Form data for URL analysis
    data = {
        'url': test_url,
        'type': 'url'
    }
    
    try:
        logger.info("Sending POST request to production API endpoint...")
        response = requests.post(url, headers=headers, data=data, timeout=120)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.info("Successfully parsed JSON response")
                
                # Save the full response to a file
                with open('production_url_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                logger.info("Full response saved to production_url_response.json")
                
                # Check the response structure
                logger.info(f"Response keys: {list(response_data.keys())}")
                
                # Check if we have citations in the response
                if 'citations' in response_data:
                    citations = response_data['citations']
                    logger.info(f"Found {len(citations)} citations in response")
                    
                    # Print first few citations
                    for i, citation in enumerate(citations[:5], 1):
                        logger.info(f"Citation {i}:")
                        logger.info(f"  Text: {citation.get('text', 'N/A')}")
                        logger.info(f"  Case: {citation.get('extracted_case_name', 'N/A')}")
                        logger.info(f"  Year: {citation.get('extracted_date', 'N/A')}")
                        logger.info(f"  Verified: {citation.get('is_verified', False)}")
                        logger.info("-" * 50)
                        
                elif 'result' in response_data and 'citations' in response_data['result']:
                    citations = response_data['result']['citations']
                    logger.info(f"Found {len(citations)} citations in result.citations")
                    
                    # Print first few citations
                    for i, citation in enumerate(citations[:5], 1):
                        logger.info(f"Citation {i}:")
                        logger.info(f"  Text: {citation.get('text', 'N/A')}")
                        logger.info(f"  Case: {citation.get('extracted_case_name', 'N/A')}")
                        logger.info(f"  Year: {citation.get('extracted_date', 'N/A')}")
                        logger.info(f"  Verified: {citation.get('is_verified', False)}")
                        logger.info("-" * 50)
                        
                else:
                    logger.warning("No 'citations' key found in response")
                    
                    # Check if this is an async response
                    if 'task_id' in response_data or ('result' in response_data and 'task_id' in response_data['result']):
                        task_id = response_data.get('task_id') or response_data['result'].get('task_id')
                        logger.info(f"Received async task ID: {task_id}")
                        logger.info("This appears to be an asynchronous processing response")
                        
                        # Check if there's a status endpoint we can poll
                        status_url = f"https://wolf.law.uw.edu/casestrainer/api/tasks/{task_id}"
                        logger.info(f"You may need to poll the status at: {status_url}")
                    
                # Print any error messages if present
                if 'error' in response_data:
                    logger.error(f"Error in response: {response_data['error']}")
                    
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse JSON response: {je}")
                logger.error(f"Response content (first 1000 chars): {response.text[:1000]}")
                
        else:
            logger.error(f"HTTP Error: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 120 seconds")
    except requests.exceptions.RequestException as re:
        logger.error(f"Request failed: {re}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

def test_text_analysis_production():
    """Test text analysis functionality using the production endpoint."""
    
    # The correct production API endpoint
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Sample text with legal citations
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010)."""
    
    logger.info("Testing text analysis with production endpoint")
    
    # Request headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Test/1.0'
    }
    
    # Form data for text analysis
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        logger.info("Sending text analysis request...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        logger.info(f"Text analysis response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                # Save the response
                with open('production_text_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                
                # Check for citations
                citations = response_data.get('citations') or response_data.get('result', {}).get('citations', [])
                logger.info(f"Text analysis found {len(citations)} citations")
                
            except json.JSONDecodeError:
                logger.error("Failed to parse text analysis response")
                
    except Exception as e:
        logger.error(f"Text analysis failed: {e}")

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("CaseStrainer Production API Test")
    logger.info("=" * 80)
    
    # Test text analysis first (simpler)
    test_text_analysis_production()
    
    logger.info("\n" + "=" * 80)
    
    # Test URL upload
    test_url_upload_production()
    
    logger.info("=" * 80)
    logger.info("Test completed. Check the log files for detailed results.")
