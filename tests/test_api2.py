import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

url = "http://localhost:5000/casestrainer/api/verify-citation"
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json"
}

# Create the JSON string manually
json_data = '{"text": "Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)"}'

logger.debug(f"Sending request to: {url}")
logger.debug(f"Headers: {headers}")
logger.debug(f"Data: {json_data}")

try:
    # Use data parameter instead of json to send raw JSON
    response = requests.post(url, headers=headers, data=json_data)
    
    logger.debug(f"Response status code: {response.status_code}")
    logger.debug(f"Response headers: {response.headers}")
    logger.debug(f"Response content: {response.text}")
    
    # Pretty print JSON response if possible
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2))
    except:
        print("Response text:", response.text)
        
except Exception as e:
    logger.error(f"Request failed: {str(e)}", exc_info=True)