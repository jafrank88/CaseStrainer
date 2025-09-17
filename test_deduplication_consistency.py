"""
Test Deduplication Consistency Between Sync and Async Processing
Verifies that both processing paths produce identical results after deduplication.
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

def test_deduplication_consistency():
    """Test that sync and async processing produce consistent deduplicated results."""
    
    print("🔍 TESTING DEDUPLICATION CONSISTENCY")
    print("=" * 60)
    
    # Test text with known duplicate citations
    test_text = """
    In Restaurant Development, Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003), the court held...
    As established in Restaurant Development, Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003)...
    See also Restaurant Development, Inc. v. Cananwill, Inc., 4 Wn.3d 1021 (2003)...
    The case Restaurant Development, Inc. v. Cananwill, Inc., 80 P.3d 598 (2003) demonstrates...
    
    This builds on Bostain v. Food Express, Inc., 159 Wn.2d 700 (2007) and 
    Bostain v. Food Express, Inc., 153 P.3d 846 (2007).
    
    Additional cases include State v. Jackson, 137 Wn.2d 712 (1999) and
    State v. Jackson, 137 Wn.2d 712 (1999) [duplicate].
    """
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    
    print(f"📝 Test text contains known duplicates:")
    print(f"   - 150 Wn.2d 674 appears 2 times")
    print(f"   - Restaurant Development citations appear 4 times")
    print(f"   - Bostain citations appear 2 times")
    print(f"   - State v. Jackson appears 2 times")
    print(f"📏 Text length: {len(test_text)} characters")
    print()
    
    # Test 1: Force sync processing (short text)
    print("🔄 TEST 1: Sync Processing")
    print("-" * 30)
    
    try:
        sync_data = {'type': 'text', 'text': test_text[:500]}  # Truncate to force sync
        sync_response = requests.post(url, headers=headers, json=sync_data, timeout=30)
        
        if sync_response.status_code == 200:
            sync_result = sync_response.json()
            sync_citations = sync_result.get('result', {}).get('citations', [])
            sync_clusters = sync_result.get('result', {}).get('clusters', [])
            sync_mode = sync_result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Sync processing completed")
            print(f"   Processing mode: {sync_mode}")
            print(f"   Citations found: {len(sync_citations)}")
            print(f"   Clusters found: {len(sync_clusters)}")
            
            # Check for duplicates
            sync_citation_texts = [c.get('citation', '') for c in sync_citations]
            sync_duplicates = len(sync_citation_texts) - len(set(sync_citation_texts))
            print(f"   Duplicate citations: {sync_duplicates}")
            
            if sync_duplicates > 0:
                print(f"   ❌ SYNC STILL HAS DUPLICATES!")
                print(f"   Citation texts: {sync_citation_texts}")
            else:
                print(f"   ✅ No duplicates in sync results")
                
        else:
            print(f"❌ Sync request failed: {sync_response.status_code}")
            sync_result = None
            
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        sync_result = None
    
    print()
    
    # Test 2: Force async processing (long text)
    print("🔄 TEST 2: Async Processing")
    print("-" * 30)
    
    try:
        # Use full text to force async processing
        async_data = {'type': 'text', 'text': test_text}
        async_response = requests.post(url, headers=headers, json=async_data, timeout=30)
        
        if async_response.status_code == 200:
            async_result = async_response.json()
            
            # Check if it's async (has task_id) or sync
            if 'task_id' in async_result.get('result', {}):
                task_id = async_result['result']['task_id']
                print(f"📋 Async processing started with task_id: {task_id}")
                
                # Poll for results
                max_attempts = 30
                for attempt in range(max_attempts):
                    time.sleep(2)
                    status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                    status_response = requests.get(status_url)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            async_citations = status_data.get('citations', [])
                            async_clusters = status_data.get('clusters', [])
                            
                            print(f"✅ Async processing completed after {(attempt + 1) * 2}s")
                            print(f"   Citations found: {len(async_citations)}")
                            print(f"   Clusters found: {len(async_clusters)}")
                            
                            # Check for duplicates
                            async_citation_texts = [c.get('citation', '') for c in async_citations]
                            async_duplicates = len(async_citation_texts) - len(set(async_citation_texts))
                            print(f"   Duplicate citations: {async_duplicates}")
                            
                            if async_duplicates > 0:
                                print(f"   ❌ ASYNC STILL HAS DUPLICATES!")
                                print(f"   Citation texts: {async_citation_texts}")
                            else:
                                print(f"   ✅ No duplicates in async results")
                            
                            async_final_result = {
                                'citations': async_citations,
                                'clusters': async_clusters,
                                'processing_mode': 'async'
                            }
                            break
                        elif status_data.get('status') == 'failed':
                            print(f"❌ Async processing failed: {status_data.get('error', 'Unknown error')}")
                            async_final_result = None
                            break
                    
                    print(f"   ⏳ Waiting for async completion... ({attempt + 1}/{max_attempts})")
                else:
                    print(f"❌ Async processing timed out after {max_attempts * 2}s")
                    async_final_result = None
            else:
                # It was processed sync despite the text length
                async_citations = async_result.get('result', {}).get('citations', [])
                async_clusters = async_result.get('result', {}).get('clusters', [])
                processing_mode = async_result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                
                print(f"✅ Processed as sync (despite text length)")
                print(f"   Processing mode: {processing_mode}")
                print(f"   Citations found: {len(async_citations)}")
                print(f"   Clusters found: {len(async_clusters)}")
                
                async_final_result = {
                    'citations': async_citations,
                    'clusters': async_clusters,
                    'processing_mode': processing_mode
                }
                
        else:
            print(f"❌ Async request failed: {sync_response.status_code}")
            async_final_result = None
            
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        async_final_result = None
    
    print()
    
    # Test 3: Compare results
    print("🔍 TEST 3: Consistency Analysis")
    print("-" * 30)
    
    if sync_result and async_final_result:
        sync_citations = sync_result.get('result', {}).get('citations', [])
        async_citations = async_final_result.get('citations', [])
        
        print(f"📊 Results comparison:")
        print(f"   Sync citations: {len(sync_citations)}")
        print(f"   Async citations: {len(async_citations)}")
        
        # Compare citation texts
        sync_texts = sorted([c.get('citation', '') for c in sync_citations])
        async_texts = sorted([c.get('citation', '') for c in async_citations])
        
        if sync_texts == async_texts:
            print(f"   ✅ Citation texts are identical!")
        else:
            print(f"   ❌ Citation texts differ!")
            print(f"   Sync only: {set(sync_texts) - set(async_texts)}")
            print(f"   Async only: {set(async_texts) - set(sync_texts)}")
        
        # Check for any remaining duplicates
        sync_duplicates = len(sync_texts) - len(set(sync_texts))
        async_duplicates = len(async_texts) - len(set(async_texts))
        
        print(f"   Sync duplicates: {sync_duplicates}")
        print(f"   Async duplicates: {async_duplicates}")
        
        if sync_duplicates == 0 and async_duplicates == 0:
            print(f"   ✅ DEDUPLICATION SUCCESSFUL IN BOTH PATHS!")
        else:
            print(f"   ❌ DEDUPLICATION FAILED!")
            
    else:
        print(f"❌ Cannot compare - one or both tests failed")
    
    print()
    print("=" * 60)
    print("🏁 DEDUPLICATION CONSISTENCY TEST COMPLETE")

if __name__ == "__main__":
    test_deduplication_consistency()
