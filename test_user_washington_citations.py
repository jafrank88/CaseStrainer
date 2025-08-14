#!/usr/bin/env python3
"""
Test User's Washington State Citations
Test the exact paragraph the user entered to diagnose clustering issues
"""

import sys
import os
import json
import requests
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set console encoding to UTF-8
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Configure logging with UTF-8 encoding
class UTF8ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        UTF8ConsoleHandler(),
        logging.FileHandler('test_user_washington_citations.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Set environment variable to allow test data in production (temporarily for testing)
os.environ['ALLOW_TEST_DATA'] = 'true'

def test_user_citations():
    """Test the user's exact Washington state citations."""
    logger.info("🔍 TESTING USER'S WASHINGTON STATE CITATIONS")
    logger.info("="*60)
    
    # User's exact text
    user_text = """We review a trial court's parenting plan for abuse of discretion. In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014). A court abuses its discretion if its decision is manifestly unreasonable or based on untenable grounds or reasons. In re Marriage of Littlefield, 133 Wn.2d 39, 46-47, 940 P.2d 1362 (1997). This includes a court's failure to apply the correct legal standard."""
    
    logger.info(f"📋 Text length: {len(user_text)} characters")
    logger.info(f"📋 Expected: 2 clusters of 2 citations each")
    logger.info(f"   - Cluster 1: Marriage of Chandola (180 Wn.2d 632, 327 P.3d 644)")
    logger.info(f"   - Cluster 2: Marriage of Littlefield (133 Wn.2d 39, 940 P.2d 1362)")
    
    try:
        # Test API endpoint
        url = "http://localhost:5000/casestrainer/api/analyze"
        data = {
            "text": user_text, 
            "type": "text",
            "test_mode": True  # Explicitly mark as test
        }
        
        # Get CourtListener API key from environment
        cl_api_key = os.getenv('COURTLISTENER_API_KEY', '***REDACTED_COURTLISTENER_KEY***')
        if not cl_api_key:
            logger.warning("⚠️ No CourtListener API key found in environment")
        
        # Add headers with API key and bypass test environment check
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Forwarded-For': '127.0.0.1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://localhost:5000/casestrainer/',
            'X-Test-Mode': 'true',  # Explicit test mode header
            'X-Allow-Test-Data': 'true',  # Bypass test data protection
            'Authorization': f'Token {cl_api_key}' if cl_api_key else ''
        }
        
        print(f"\n🌐 Testing API endpoint: {url}")
        print(f"📤 Request headers: {json.dumps(headers, indent=2)}")
        print(f"📝 Request data: {json.dumps(data, indent=2)}")
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Try to get JSON response if possible
            try:
                response_json = response.json()
                print(f"📥 Response JSON: {json.dumps(response_json, indent=2)}")
            except ValueError:
                print(f"📥 Response text (not JSON): {response.text[:1000]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"❌ Response status: {e.response.status_code}")
                print(f"❌ Response text: {e.response.text}")
            raise
        
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            print(f"📊 Response status: {status}")
            
            if status == 'completed':
                print("✅ Immediate processing completed")
                
                # Get results
                result_data = result.get('result', {})
                citations = result_data.get('citations', [])
                clusters = result_data.get('clusters', [])
                
                print(f"\n📊 RESULTS:")
                print(f"   Citations found: {len(citations)}")
                print(f"   Clusters found: {len(clusters)}")
                
                # Analyze citations
                if citations:
                    print(f"\n📋 CITATIONS:")
                    for i, citation in enumerate(citations, 1):
                        print(f"   {i}. Citation: {citation.get('citation')}")
                        print(f"      Case Name: {citation.get('extracted_case_name')}")
                        print(f"      Canonical Name: {citation.get('canonical_name')}")
                        print(f"      Canonical URL: {citation.get('canonical_url')}")
                        print(f"      Verified: {citation.get('verified')}")
                        print()
                
                # Analyze clusters
                if clusters:
                    print(f"📋 CLUSTERS:")
                    for i, cluster in enumerate(clusters, 1):
                        cluster_citations = cluster.get('citations', [])
                        print(f"   Cluster {i}: {len(cluster_citations)} citations")
                        for j, cit in enumerate(cluster_citations, 1):
                            print(f"      {j}. {cit}")
                        print()
                
                # Check success criteria
                expected_citations = 4  # 2 Wn.2d + 2 P.3d
                expected_clusters = 2   # 2 cases
                
                success = (
                    len(citations) == expected_citations and
                    len(clusters) == expected_clusters
                )
                
                print(f"🎯 SUCCESS CRITERIA:")
                print(f"   Expected citations: {expected_citations}, Got: {len(citations)} {'✅' if len(citations) == expected_citations else '❌'}")
                print(f"   Expected clusters: {expected_clusters}, Got: {len(clusters)} {'✅' if len(clusters) == expected_clusters else '❌'}")
                print(f"   Overall: {'✅ SUCCESS' if success else '❌ FAILED'}")
                
                if not success:
                    print(f"\n🔍 DIAGNOSIS:")
                    if len(citations) == 0:
                        print("   ❌ No citations extracted - extraction pipeline broken")
                    elif len(citations) < expected_citations:
                        print("   ❌ Missing citations - extraction not finding all citations")
                    elif len(clusters) != expected_clusters:
                        print("   ❌ Clustering issue - not grouping parallel citations correctly")
                
                return success
                
            elif status == 'processing':
                task_id = result.get('task_id')
                print(f"⚠️  Unexpected async processing with task_id: {task_id}")
                print("   This should be immediate processing for short text")
                return False
            else:
                print(f"❌ Unexpected status: {status}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_processing():
    """Test direct processing to isolate the issue."""
    logger.info("\n🔬 DIRECT PROCESSING TEST")
    logger.info("="*60)
    
    user_text = """We review a trial court's parenting plan for abuse of discretion. In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014). A court abuses its discretion if its decision is manifestly unreasonable or based on untenable grounds or reasons. In re Marriage of Littlefield, 133 Wn.2d 39, 46-47, 940 P.2d 1362 (1997). This includes a court's failure to apply the correct legal standard."""
    
    try:
        logger.info("Importing CitationService...")
        from src.api.services.citation_service import CitationService
        
        logger.info("Initializing CitationService...")
        service = CitationService()
        input_data = {'text': user_text, 'type': 'text'}
        
        # Test should_process_immediately
        logger.info("Testing should_process_immediately...")
        should_immediate = service.should_process_immediately(input_data)
        logger.info(f"should_process_immediately: {should_immediate}")
        
        if should_immediate:
            logger.info("✅ Text should be processed immediately")
            
            # Test process_immediately
            logger.info("Processing text immediately...")
            start_time = time.time()
            result = service.process_immediately(input_data)
            processing_time = time.time() - start_time
            
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            logger.info(f"Result status: {result.get('status')}")
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            logger.info(f"Citations found: {len(citations)}")
            logger.info(f"Clusters found: {len(clusters)}")
            
            if citations:
                logger.info("\n📋 CITATIONS:")
                for i, citation in enumerate(citations, 1):
                    logger.info(f"   {i}. {citation.get('citation')}")
                    logger.info(f"      Case Name: {citation.get('case_name')}")
                    logger.info(f"      Extracted Name: {citation.get('extracted_case_name')}")
                    logger.info(f"      Canonical Name: {citation.get('canonical_name')}")
                    logger.info(f"      Verified: {citation.get('verified')}")
            
            if clusters:
                logger.info("\n🔗 CLUSTERS:")
                for i, cluster in enumerate(clusters, 1):
                    cluster_citations = cluster.get('citations', [])
                    logger.info(f"   Cluster {i}: {len(cluster_citations)} citations")
                    for j, citation in enumerate(cluster_citations, 1):
                        logger.info(f"      {j}. {citation.get('citation')}")
            
            # Check if we got the expected number of citations and clusters
            expected_citations = 4
            expected_clusters = 2
            
            success = (len(citations) == expected_citations and 
                      len(clusters) == expected_clusters)
            
            if success:
                logger.info("✅ Test passed: Found expected number of citations and clusters")
            else:
                logger.warning(f"❌ Test failed: Expected {expected_citations} citations and {expected_clusters} clusters, "
                             f"but found {len(citations)} citations and {len(clusters)} clusters")
            
            return success
        else:
            logger.error("❌ Text should be processed immediately (unexpected)")
            return False
        
    except ImportError as ie:
        logger.error(f"❌ Import error: {ie}")
        logger.error("Make sure all dependencies are installed and PYTHONPATH is set correctly")
        import traceback
        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"❌ Direct processing test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        return False

def main():
    """Run user citation tests."""
    print("🧪 USER WASHINGTON STATE CITATIONS TEST")
    print("="*70)
    
    api_success = test_user_citations()
    direct_success = test_direct_processing()
    
    print(f"\n" + "="*70)
    print("📊 DIAGNOSIS RESULTS")
    print("="*70)
    
    print(f"API endpoint test: {'✅ WORKING' if api_success else '❌ FAILED'}")
    print(f"Direct processing test: {'✅ WORKING' if direct_success else '❌ FAILED'}")
    
    if not api_success and not direct_success:
        print("\n🔍 DIAGNOSIS: Core extraction/clustering pipeline broken")
        print("   Both API and direct processing are failing")
        print("   Check citation extraction and clustering logic")
    elif direct_success and not api_success:
        print("\n🔍 DIAGNOSIS: API routing or response formatting issue")
        print("   Direct processing works but API doesn't")
        print("   Check API endpoint routing and response handling")
    elif api_success and direct_success:
        print("\n✅ DIAGNOSIS: Everything working correctly")
        print("   Both API and direct processing are functional")
    
    return api_success and direct_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
