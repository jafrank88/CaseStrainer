import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_api_directly():
    """Test the CourtListener API directly with a sample citation."""
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if not api_key:
        logger.error("ERROR: COURTLISTENER_API_KEY environment variable is not set")
        return False
    
    citation = "410 U.S. 113"  # Roe v. Wade
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer/1.0 (test script)'
    }
    
    # Prepare the JSON payload for the POST request
    payload = {
        'text': citation,
        'type': 'citation',  # 'citation' for citation lookup
        'return_models': True  # Return full case details
    }
    
    logger.info(f"Testing API with citation: {citation}")
    logger.info(f"API Key: {'*' * 10}{api_key[-4:] if api_key else 'NONE'}")
    
    try:
        # Log request details
        logger.info("\nRequest Details:")
        logger.info(f"URL: {url}")
        logger.info(f"Method: POST")
        logger.info(f"Headers: {json.dumps(headers, indent=2)}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Make the POST request with JSON payload
        logger.info("\nSending POST request to CourtListener API...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,  # Send as JSON in the request body
            timeout=(10, 30),  # 10s connect, 30s read
            verify=True  # Ensure SSL verification is on
        )
        
        # Log response details
        logger.info("\nResponse Received:")
        logger.info(f"Status Code: {response.status_code}")
        logger.info("Response Headers:")
        for header, value in response.headers.items():
            logger.info(f"  {header}: {value}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info("\nAPI Response (JSON):")
                logger.info(json.dumps(data, indent=2))
                return True
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.info(f"Raw response (first 500 chars): {response.text[:500]}")
                return False
        else:
            logger.error(f"\nAPI Error ({response.status_code}):")
            try:
                error_data = response.json()
                logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
            except ValueError:
                logger.error(f"Non-JSON response: {response.text[:1000]}...")
            
            # Check for rate limiting
            if response.status_code == 429:
                logger.error("\n⚠️ Rate limited! Check your API key usage and limits.")
            
            return False
            
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL Error: {str(e)}")
        logger.error("This might be due to SSL verification issues. Try running with verify=False (not recommended for production).")
        return False
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out: {str(e)}")
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text[:500]}...")
        return False

if __name__ == "__main__":
    logger.info("Starting direct API test...")
    success = test_api_directly()
    if success:
        logger.info("\n✅ API test completed successfully!")
    else:
        logger.error("\n❌ API test failed. Check logs for details.")
