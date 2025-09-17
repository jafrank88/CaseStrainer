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
        logging.FileHandler('url_complete_test.log')
    ]
)
logger = logging.getLogger(__name__)

def poll_task_status_correct(task_id, max_attempts=30, interval=5):
    """
    Poll the correct task status endpoint until completion.
    
    Args:
        task_id: The task ID to poll
        max_attempts: Maximum number of polling attempts
        interval: Seconds between polling attempts
    """
    
    # Use the correct endpoint from the frontend code
    status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
    
    headers = {
        'User-Agent': 'CaseStrainer-Test/1.0',
        'Accept': 'application/json'
    }
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Polling attempt {attempt + 1}/{max_attempts} for task {task_id}")
            response = requests.get(status_url, headers=headers, timeout=10)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    status_data = response.json()
                    logger.info(f"Task status response: {json.dumps(status_data, indent=2)}")
                    
                    # Save the response
                    filename = f"task_status_{task_id}_{attempt}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, indent=2, ensure_ascii=False)
                    
                    # Check task status
                    status = status_data.get('status', '').lower()
                    success = status_data.get('success', False)
                    
                    if status == 'completed' and success:
                        logger.info("✅ Task completed successfully!")
                        
                        # Check for citations in the result
                        result = status_data.get('result', {})
                        citations = result.get('citations', [])
                        
                        if citations:
                            logger.info(f"🎯 Found {len(citations)} citations!")
                            
                            # Display first few citations
                            for i, citation in enumerate(citations[:5], 1):
                                text = citation.get('text', citation.get('citation', 'N/A'))
                                case_name = citation.get('extracted_case_name', citation.get('case_name', 'N/A'))
                                year = citation.get('extracted_date', citation.get('year', 'N/A'))
                                verified = citation.get('is_verified', citation.get('verified', False))
                                
                                logger.info(f"Citation {i}:")
                                logger.info(f"  📄 Text: {text}")
                                logger.info(f"  ⚖️  Case: {case_name}")
                                logger.info(f"  📅 Year: {year}")
                                logger.info(f"  ✅ Verified: {verified}")
                                logger.info("-" * 50)
                        else:
                            logger.warning("⚠️  No citations found in completed task")
                        
                        return status_data
                        
                    elif status == 'failed' or (not success and status != 'processing'):
                        error_msg = status_data.get('error', 'Unknown error')
                        logger.error(f"❌ Task failed: {error_msg}")
                        return status_data
                        
                    elif status in ['processing', 'queued']:
                        message = status_data.get('message', 'Processing...')
                        logger.info(f"🔄 Task {status}: {message}")
                        
                    else:
                        logger.warning(f"❓ Unknown status: {status}")
                        
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON: {je}")
                    logger.error(f"Response content: {response.text[:500]}")
                    
            elif response.status_code == 404:
                logger.warning(f"Task {task_id} not found (404)")
                
            else:
                logger.warning(f"HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
        
        # Wait before next attempt
        if attempt < max_attempts - 1:
            logger.info(f"⏳ Waiting {interval} seconds before next attempt...")
            time.sleep(interval)
    
    logger.error(f"❌ Max polling attempts ({max_attempts}) reached without completion")
    return None

def submit_url_and_get_results(url_to_analyze):
    """Submit a URL for analysis and poll for complete results."""
    
    logger.info("=" * 80)
    logger.info("🚀 CaseStrainer URL Analysis Test")
    logger.info("=" * 80)
    
    # Step 1: Submit the URL
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
        logger.info(f"📤 Submitting URL for analysis: {url_to_analyze}")
        response = requests.post(api_endpoint, headers=headers, data=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Save initial response
            with open('url_submission_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            # Extract task ID
            task_id = (response_data.get('task_id') or 
                      response_data.get('result', {}).get('task_id'))
            
            if task_id:
                logger.info(f"✅ Got task ID: {task_id}")
                logger.info(f"📊 Document length: {response_data.get('document_length', 'Unknown')} characters")
                
                # Step 2: Poll for results
                logger.info("\n🔍 Starting to poll for results...")
                result = poll_task_status_correct(task_id)
                
                if result:
                    logger.info("\n🎉 Successfully retrieved final results!")
                    
                    # Save final results
                    with open('url_final_results.json', 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    return result
                else:
                    logger.error("\n❌ Failed to get final results")
                    
            else:
                logger.error("❌ No task ID found in response")
                logger.error(f"Response: {json.dumps(response_data, indent=2)}")
                
        else:
            logger.error(f"❌ Failed to submit URL: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error submitting URL: {e}")
    
    return None

if __name__ == "__main__":
    # Test with the provided URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    logger.info(f"🎯 Target URL: {test_url}")
    logger.info("This PDF should contain legal citations that will be extracted and verified.")
    
    # Run the complete test
    final_result = submit_url_and_get_results(test_url)
    
    if final_result:
        # Extract summary information
        result_data = final_result.get('result', {})
        citations = result_data.get('citations', [])
        
        logger.info("\n" + "=" * 80)
        logger.info("📋 FINAL SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Task Status: {final_result.get('status', 'Unknown')}")
        logger.info(f"📄 Total Citations Found: {len(citations)}")
        
        if citations:
            verified_count = sum(1 for c in citations if c.get('is_verified', c.get('verified', False)))
            logger.info(f"✅ Verified Citations: {verified_count}")
            logger.info(f"❓ Unverified Citations: {len(citations) - verified_count}")
            
            # Show unique case names
            case_names = set()
            for citation in citations:
                case_name = citation.get('extracted_case_name', citation.get('case_name', ''))
                if case_name and case_name != 'N/A':
                    case_names.add(case_name)
            
            if case_names:
                logger.info(f"⚖️  Unique Cases Found: {len(case_names)}")
                for case_name in sorted(case_names):
                    logger.info(f"   • {case_name}")
        
        logger.info("=" * 80)
        logger.info("✅ URL Upload functionality is working correctly!")
        logger.info("Check the saved JSON files for detailed results.")
        
    else:
        logger.error("\n" + "=" * 80)
        logger.error("❌ URL Upload Test Failed")
        logger.error("The URL upload functionality may need debugging.")
        logger.error("=" * 80)
