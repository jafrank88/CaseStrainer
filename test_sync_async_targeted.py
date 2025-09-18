"""
Targeted Sync/Async Test
Tests both processing modes with your exact problematic text.
"""

import requests
import json
import time

def test_sync_processing():
    """Test sync processing with short text."""
    
    print("🔄 TESTING SYNC PROCESSING")
    print("=" * 30)
    
    # Short text to force sync processing
    short_text = """Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)
Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007)"""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': short_text}
    
    print(f"📝 Text length: {len(short_text)} characters (should force sync)")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            processing_strategy = result.get('result', {}).get('metadata', {}).get('processing_strategy', 'unknown')
            
            print(f"✅ Sync test completed")
            print(f"   Processing mode: {processing_mode}")
            print(f"   Processing strategy: {processing_strategy}")
            print(f"   Citations found: {len(citations)}")
            
            # Check for duplicates
            citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
            unique_citations = set(citation_texts)
            duplicates = len(citation_texts) - len(unique_citations)
            
            print(f"   Duplicate citations: {duplicates}")
            
            if duplicates > 0:
                print(f"   ❌ SYNC DEDUPLICATION NOT WORKING")
                from collections import Counter
                counts = Counter(citation_texts)
                for citation, count in counts.items():
                    if count > 1:
                        print(f"      '{citation}' appears {count} times")
            else:
                print(f"   ✅ SYNC DEDUPLICATION WORKING")
            
            # Check case name extraction
            print(f"\n📋 Case name extraction results:")
            for citation in citations:
                citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                extracted_name = citation.get('extracted_case_name', '')
                canonical_name = citation.get('canonical_name', '')
                
                print(f"   {citation_text}:")
                print(f"      Extracted: {extracted_name}")
                print(f"      Canonical: {canonical_name}")
                
                # Check if extraction improved
                if len(extracted_name) > 15 and 'Inc. v.' not in extracted_name[:10]:
                    print(f"      ✅ GOOD EXTRACTION")
                elif extracted_name.startswith('Inc. v.') and len(extracted_name) > 15:
                    print(f"      ⚠️  PARTIAL IMPROVEMENT")
                else:
                    print(f"      ❌ STILL TRUNCATED")
            
            return result
        else:
            print(f"❌ Sync request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        return None

def test_async_processing():
    """Test async processing with longer text."""
    
    print(f"\n🔄 TESTING ASYNC PROCESSING")
    print("=" * 30)
    
    # Longer text to potentially force async processing
    long_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)

If the statute is susceptible to more than one reasonable interpretation after this inquiry, 
it is ambiguous, and we may consider extratextual materials to help determine legislative 
intent, including legislative history and agency interpretation. Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases).

Additional text to make this longer and potentially force async processing. 
This should help us test whether the async deduplication is working properly.
More text here to ensure we exceed the sync threshold and trigger async processing.
Even more text to be absolutely sure we're testing the async pipeline."""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': long_text}
    
    print(f"📝 Text length: {len(long_text)} characters (should force async)")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if it's async (has task_id) or sync
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
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
                            citations = status_data.get('citations', [])
                            
                            print(f"✅ Async processing completed after {(attempt + 1) * 2}s")
                            print(f"   Citations found: {len(citations)}")
                            
                            # Check for duplicates
                            citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                            unique_citations = set(citation_texts)
                            duplicates = len(citation_texts) - len(unique_citations)
                            
                            print(f"   Duplicate citations: {duplicates}")
                            
                            if duplicates > 0:
                                print(f"   ❌ ASYNC DEDUPLICATION NOT WORKING")
                                from collections import Counter
                                counts = Counter(citation_texts)
                                for citation, count in counts.items():
                                    if count > 1:
                                        print(f"      '{citation}' appears {count} times")
                            else:
                                print(f"   ✅ ASYNC DEDUPLICATION WORKING")
                            
                            return {
                                'citations': citations,
                                'processing_mode': 'async'
                            }
                        elif status_data.get('status') == 'failed':
                            print(f"❌ Async processing failed: {status_data.get('error', 'Unknown error')}")
                            return None
                    
                    print(f"   ⏳ Waiting for async completion... ({attempt + 1}/{max_attempts})")
                else:
                    print(f"❌ Async processing timed out after {max_attempts * 2}s")
                    return None
            else:
                # It was processed sync despite the text length
                citations = result.get('result', {}).get('citations', [])
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                
                print(f"✅ Processed as sync (despite text length)")
                print(f"   Processing mode: {processing_mode}")
                print(f"   Citations found: {len(citations)}")
                
                return {
                    'citations': citations,
                    'processing_mode': processing_mode
                }
                
        else:
            print(f"❌ Async request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return None

def main():
    """Run both sync and async tests."""
    
    print("🔍 TARGETED SYNC/ASYNC DEDUPLICATION TEST")
    print("=" * 60)
    
    sync_result = test_sync_processing()
    async_result = test_async_processing()
    
    print(f"\n📊 SUMMARY")
    print("=" * 20)
    
    if sync_result and async_result:
        sync_citations = len(sync_result.get('result', {}).get('citations', []))
        async_citations = len(async_result.get('citations', []))
        
        print(f"✅ Both tests completed")
        print(f"   Sync citations: {sync_citations}")
        print(f"   Async citations: {async_citations}")
        
        if sync_citations > 0 and async_citations > 0:
            print(f"   📈 Both processing modes are working")
        else:
            print(f"   ⚠️  One or both modes returned no citations")
    else:
        print(f"❌ One or both tests failed")
        if not sync_result:
            print(f"   Sync test failed")
        if not async_result:
            print(f"   Async test failed")

if __name__ == "__main__":
    main()
