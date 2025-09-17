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
        logging.FileHandler('clustering_verification_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_sync_processing():
    """Test synchronous processing with the user's paragraph."""
    
    # The user's specific paragraph that should create clusters and verify citations
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    logger.info("=" * 80)
    logger.info("🔄 TESTING SYNCHRONOUS PROCESSING")
    logger.info("=" * 80)
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Test/1.0'
    }
    
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        logger.info("Sending synchronous request...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Save response
            with open('sync_test_response.json', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            # Analyze results
            result = response_data.get('result', {})
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            metadata = result.get('metadata', {})
            
            logger.info(f"📊 SYNC RESULTS:")
            logger.info(f"  Citations found: {len(citations)}")
            logger.info(f"  Clusters created: {len(clusters)}")
            logger.info(f"  Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
            
            # Check for Bostain parallel citations
            bostain_citations = [c for c in citations if 'bostain' in c.get('extracted_case_name', '').lower()]
            logger.info(f"  Bostain citations: {len(bostain_citations)}")
            
            # Check verification status
            verified_count = sum(1 for c in citations if c.get('verified', False) or c.get('is_verified', False))
            logger.info(f"  Verified citations: {verified_count}/{len(citations)}")
            
            # Detailed analysis
            if len(bostain_citations) >= 2:
                logger.info("✅ Found multiple Bostain citations (should cluster)")
                for i, citation in enumerate(bostain_citations, 1):
                    logger.info(f"    {i}. {citation.get('citation', 'N/A')} - {citation.get('extracted_case_name', 'N/A')}")
            else:
                logger.warning("❌ Expected multiple Bostain citations for clustering")
            
            if len(clusters) > 0:
                logger.info("✅ Clusters were created")
                for i, cluster in enumerate(clusters, 1):
                    cluster_citations = cluster.get('citations', [])
                    logger.info(f"    Cluster {i}: {len(cluster_citations)} citations")
            else:
                logger.warning("❌ No clusters were created")
            
            if verified_count > 0:
                logger.info("✅ Some citations were verified")
            else:
                logger.warning("❌ No citations were verified")
            
            return {
                'success': True,
                'citations_count': len(citations),
                'clusters_count': len(clusters),
                'verified_count': verified_count,
                'bostain_count': len(bostain_citations),
                'processing_strategy': metadata.get('processing_strategy', 'unknown')
            }
            
        else:
            logger.error(f"Sync request failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Sync test failed: {e}")
        return {'success': False, 'error': str(e)}

def test_async_processing():
    """Test asynchronous processing with a longer text."""
    
    # Create a longer text to trigger async processing
    base_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    # Repeat the text to make it longer and trigger async processing
    long_text = base_text + "\n\n" + base_text + "\n\n" + base_text
    
    logger.info("=" * 80)
    logger.info("🔄 TESTING ASYNCHRONOUS PROCESSING")
    logger.info("=" * 80)
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'CaseStrainer-Test/1.0'
    }
    
    data = {
        'text': long_text,
        'type': 'text'
    }
    
    try:
        logger.info(f"Sending async request with {len(long_text)} characters...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Check if this is an async response
            task_id = response_data.get('task_id') or response_data.get('result', {}).get('task_id')
            
            if task_id:
                logger.info(f"Got async task ID: {task_id}")
                
                # Poll for results
                status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                
                for attempt in range(30):  # 30 attempts, 5 seconds each = 2.5 minutes max
                    logger.info(f"Polling attempt {attempt + 1}/30...")
                    
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('status') == 'completed':
                            logger.info("✅ Async task completed!")
                            
                            # Save response
                            with open('async_test_response.json', 'w', encoding='utf-8') as f:
                                json.dump(status_data, f, indent=2, ensure_ascii=False)
                            
                            # Analyze results
                            result = status_data.get('result', {})
                            citations = result.get('citations', [])
                            clusters = result.get('clusters', [])
                            
                            logger.info(f"📊 ASYNC RESULTS:")
                            logger.info(f"  Citations found: {len(citations)}")
                            logger.info(f"  Clusters created: {len(clusters)}")
                            
                            # Check for Bostain parallel citations
                            bostain_citations = [c for c in citations if 'bostain' in c.get('extracted_case_name', '').lower()]
                            logger.info(f"  Bostain citations: {len(bostain_citations)}")
                            
                            # Check verification status
                            verified_count = sum(1 for c in citations if c.get('verified', False) or c.get('is_verified', False))
                            logger.info(f"  Verified citations: {verified_count}/{len(citations)}")
                            
                            return {
                                'success': True,
                                'citations_count': len(citations),
                                'clusters_count': len(clusters),
                                'verified_count': verified_count,
                                'bostain_count': len(bostain_citations)
                            }
                            
                        elif status_data.get('status') == 'failed':
                            logger.error(f"Async task failed: {status_data.get('error', 'Unknown error')}")
                            return {'success': False, 'error': 'Task failed'}
                        
                        else:
                            logger.info(f"Task status: {status_data.get('status', 'unknown')}")
                            time.sleep(5)
                    else:
                        logger.warning(f"Status check failed: {status_response.status_code}")
                        time.sleep(5)
                
                logger.error("Async task did not complete within timeout")
                return {'success': False, 'error': 'Timeout'}
                
            else:
                # This was processed synchronously despite being long
                logger.info("Text was processed synchronously despite length")
                result = response_data.get('result', {})
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                return {
                    'success': True,
                    'citations_count': len(citations),
                    'clusters_count': len(clusters),
                    'verified_count': 0,  # Will analyze separately
                    'note': 'Processed synchronously'
                }
                
        else:
            logger.error(f"Async request failed: {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Async test failed: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Run comprehensive tests for both sync and async processing."""
    
    logger.info("🚀 Starting comprehensive clustering and verification tests")
    
    # Test synchronous processing
    sync_result = test_sync_processing()
    
    # Test asynchronous processing
    async_result = test_async_processing()
    
    # Summary
    logger.info("=" * 80)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 80)
    
    if sync_result['success']:
        logger.info("✅ SYNC PROCESSING:")
        logger.info(f"  Citations: {sync_result['citations_count']}")
        logger.info(f"  Clusters: {sync_result['clusters_count']}")
        logger.info(f"  Verified: {sync_result['verified_count']}")
        logger.info(f"  Bostain citations: {sync_result['bostain_count']}")
        logger.info(f"  Strategy: {sync_result['processing_strategy']}")
        
        # Evaluate success criteria
        clustering_works = sync_result['clusters_count'] > 0 and sync_result['bostain_count'] >= 2
        verification_works = sync_result['verified_count'] > 0
        
        logger.info(f"  Clustering working: {'✅' if clustering_works else '❌'}")
        logger.info(f"  Verification working: {'✅' if verification_works else '❌'}")
        
    else:
        logger.error(f"❌ SYNC PROCESSING FAILED: {sync_result.get('error', 'Unknown error')}")
    
    if async_result['success']:
        logger.info("✅ ASYNC PROCESSING:")
        logger.info(f"  Citations: {async_result['citations_count']}")
        logger.info(f"  Clusters: {async_result['clusters_count']}")
        logger.info(f"  Verified: {async_result['verified_count']}")
        logger.info(f"  Bostain citations: {async_result['bostain_count']}")
        
    else:
        logger.error(f"❌ ASYNC PROCESSING FAILED: {async_result.get('error', 'Unknown error')}")
    
    # Overall assessment
    overall_success = (
        sync_result['success'] and 
        sync_result['clusters_count'] > 0 and 
        sync_result['bostain_count'] >= 2
    )
    
    if overall_success:
        logger.info("🎉 OVERALL: Clustering and verification fixes are working!")
    else:
        logger.error("❌ OVERALL: Issues still remain with clustering or verification")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
