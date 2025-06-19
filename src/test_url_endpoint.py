import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fetch_url(url):
    """Test the fetch_url endpoint with a given URL."""
    logger.info(f"Testing fetch_url endpoint with URL: {url}")
    
    # Use the correct endpoint URL with the /casestrainer/api prefix
    endpoint = "http://localhost:5000/casestrainer/api/fetch_url"
    
    try:
        # Send POST request to the endpoint
        response = requests.post(
            endpoint,
            json={"url": url},
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        try:
            data = response.json()
            logger.info("Response JSON:")
            logger.info(json.dumps(data, indent=2))
            
            if response.status_code == 200:
                logger.info(f"Successfully extracted {len(data.get('text', ''))} characters")
                logger.info(f"Sample text: {data.get('text', '')[:500]}...")
                logger.info(f"Found {len(data.get('citations', []))} citations")
            else:
                logger.error(f"Error: {data.get('error', 'Unknown error')}")
                logger.error(f"Details: {data.get('details', 'No details provided')}")
                
        except json.JSONDecodeError as e:
            # Safely log the response error to avoid Unicode encoding errors
            try:
                logger.error(f"Response is not JSON: {response.text}")
            except UnicodeEncodeError:
                # If Unicode fails, log a safe version
                safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                logger.error(f"Response is not JSON (safe): {safe_text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

if __name__ == "__main__":
    # Test with the Washington Supreme Court opinion URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1028814.pdf"
    test_fetch_url(test_url) 