import requests
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('url_upload_debug.log')
    ]
)
logger = logging.getLogger(__name__)

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
        logger.info("Sending POST request to API endpoint")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            logger.info("Successfully parsed JSON response")
            
            # Save the full response to a file
            with open('url_analysis_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info("Full response saved to url_analysis_response.json")
            
            # Print summary of citations if present
            if 'citations' in response_data:
                logger.info(f"Found {len(response_data['citations'])} citations in response")
                for i, citation in enumerate(response_data['citations'][:5], 1):
                    logger.info(f"Citation {i}: {citation.get('text', 'N/A')}")
            else:
                logger.warning("No 'citations' key found in response")
                
            # Print any error messages if present
            if 'error' in response_data:
                logger.error(f"Error in response: {response_data['error']}")
                
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response: {je}")
            logger.error(f"Response content: {response.text[:1000]}...")
            
    except requests.exceptions.RequestException as re:
        logger.error(f"Request failed: {re}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    test_url_upload()
