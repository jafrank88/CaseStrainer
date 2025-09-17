import requests
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_url_analysis():
    # The API endpoint for analysis
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # The test URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    logger.info(f"Starting URL analysis test for: {test_url}")
    
    # Request headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    # Form data
    data = {
        'url': test_url,
        'type': 'url',
        'sync': 'true'  # Explicitly request synchronous processing
    }
    
    try:
        logger.info("Sending POST request to API endpoint")
        response = requests.post(url, headers=headers, data=data, timeout=300)  # 5 minute timeout
        
        logger.info(f"Response status code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            
            # Save the full response to a file
            with open('sync_url_analysis_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
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
            else:
                logger.warning("No 'citations' key found in response")
                logger.debug(f"Response keys: {list(response_data.keys())}")
                
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
    test_url_analysis()
