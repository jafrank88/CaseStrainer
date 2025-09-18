"""
Test Async Processing Fix
Tests the fixed async endpoint and investigates remaining deduplication issues.
"""

import requests
import json
import time

def test_async_fix():
    """Test the fixed async processing endpoint."""
    
    print("🔧 TESTING ASYNC PROCESSING FIX")
    print("=" * 40)
    
    # Create large text to force async processing
    base_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)"""
    
    large_text = base_text * 15  # Make it large enough for async
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': large_text}
    
    print(f"📝 Text length: {len(large_text)} characters")
    
    try:
        # Submit the task
        print(f"\n📤 Submitting async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Submission failed: HTTP {response.status_code}")
            return False
        
        result = response.json()
        
        if 'task_id' in result.get('result', {}):
            task_id = result['result']['task_id']
            print(f"✅ Async task created: {task_id}")
            
            # Test the fixed endpoint
            status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
            
            print(f"\n⏳ Monitoring task with fixed endpoint...")
            
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Check if it's a status update or final result
                        if 'status' in status_data:
                            status = status_data['status']
                            print(f"Attempt {attempt + 1}: Status = {status}")
                            
                            if status == 'completed':
                                citations = status_data.get('citations', [])
                                
                                print(f"\n✅ ASYNC TASK COMPLETED!")
                                print(f"   Citations found: {len(citations)}")
                                
                                # Check deduplication
                                citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                unique_citations = set(citation_texts)
                                duplicates = len(citation_texts) - len(unique_citations)
                                
                                print(f"   Total citations: {len(citation_texts)}")
                                print(f"   Unique citations: {len(unique_citations)}")
                                print(f"   Duplicates: {duplicates}")
                                
                                if duplicates == 0:
                                    print(f"   ✅ ASYNC DEDUPLICATION WORKING!")
                                else:
                                    print(f"   ❌ ASYNC DEDUPLICATION FAILED!")
                                    from collections import Counter
                                    counts = Counter(citation_texts)
                                    for citation, count in counts.items():
                                        if count > 1:
                                            print(f"      '{citation}' appears {count} times")
                                
                                return True
                                
                            elif status == 'failed':
                                error = status_data.get('error', 'Unknown error')
                                print(f"\n❌ TASK FAILED: {error}")
                                return False
                                
                            elif status in ['running', 'queued', 'started']:
                                time.sleep(3)
                                continue
                        else:
                            # It might be the final result directly
                            if 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                print(f"\n✅ ASYNC TASK COMPLETED (direct result)!")
                                print(f"   Citations found: {len(citations)}")
                                return True
                    
                    elif status_response.status_code == 404:
                        print(f"Attempt {attempt + 1}: Still 404 - task not found or not ready")
                        time.sleep(3)
                    else:
                        print(f"Attempt {attempt + 1}: HTTP {status_response.status_code}")
                        time.sleep(3)
                        
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Error - {e}")
                    time.sleep(3)
            
            print(f"\n⏰ Task monitoring timed out")
            return False
            
        else:
            # Processed as sync
            processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            print(f"⚠️  Processed as sync: {processing_mode}")
            return test_sync_deduplication(result)
            
    except Exception as e:
        print(f"❌ Error in async test: {e}")
        return False

def test_sync_deduplication(result=None):
    """Test sync deduplication with the original problematic text."""
    
    print(f"\n🔍 TESTING SYNC DEDUPLICATION")
    print("-" * 30)
    
    if result is None:
        # Test with original problematic text
        test_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)

If the statute is susceptible to more than one 
reasonable interpretation after this inquiry, it is ambiguous, and we may consider 
extratextual materials to help determine legislative intent, including legislative 
history and agency interpretation. Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases)."""
        
        url = "http://localhost:8080/casestrainer/api/analyze"
        headers = {'Content-Type': 'application/json'}
        data = {'type': 'text', 'text': test_text}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
            else:
                print(f"❌ Request failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Request error: {e}")
            return False
    
    citations = result.get('result', {}).get('citations', [])
    processing_strategy = result.get('result', {}).get('metadata', {}).get('processing_strategy', 'unknown')
    
    print(f"Processing strategy: {processing_strategy}")
    print(f"Citations found: {len(citations)}")
    
    # Detailed deduplication analysis
    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
    unique_citations = set(citation_texts)
    duplicates = len(citation_texts) - len(unique_citations)
    
    print(f"Total citations: {len(citation_texts)}")
    print(f"Unique citations: {len(unique_citations)}")
    print(f"Duplicates: {duplicates}")
    
    if duplicates > 0:
        print(f"\n❌ DUPLICATES FOUND:")
        from collections import Counter
        counts = Counter(citation_texts)
        for citation, count in counts.items():
            if count > 1:
                print(f"   '{citation}' appears {count} times")
                
                # Find the duplicate citations and analyze them
                duplicate_citations = [c for c in citations if c.get('citation', '').replace('\n', ' ').strip() == citation]
                print(f"   Duplicate citation details:")
                for i, dup_cit in enumerate(duplicate_citations):
                    print(f"      {i+1}. Case name: {dup_cit.get('extracted_case_name', 'N/A')}")
                    print(f"         Verified: {dup_cit.get('verified', 'N/A')}")
                    print(f"         Canonical: {dup_cit.get('canonical_name', 'N/A')}")
        
        return False
    else:
        print(f"✅ NO DUPLICATES - DEDUPLICATION WORKING!")
        return True

def main():
    """Run comprehensive async and sync tests."""
    
    print("🎯 COMPREHENSIVE ASYNC/SYNC FIX TEST")
    print("=" * 50)
    
    # Test sync deduplication first
    sync_success = test_sync_deduplication()
    
    # Test async processing fix
    async_success = test_async_fix()
    
    print(f"\n📊 FINAL RESULTS")
    print("=" * 20)
    print(f"✅ Sync deduplication: {'WORKING' if sync_success else 'FAILED'}")
    print(f"✅ Async processing: {'WORKING' if async_success else 'FAILED'}")
    
    if sync_success and async_success:
        print(f"\n🎉 ALL FIXES SUCCESSFUL!")
    elif sync_success:
        print(f"\n⚠️  SYNC WORKING, ASYNC NEEDS MORE WORK")
    elif async_success:
        print(f"\n⚠️  ASYNC WORKING, SYNC NEEDS MORE WORK")
    else:
        print(f"\n❌ BOTH NEED MORE WORK")

if __name__ == "__main__":
    main()
