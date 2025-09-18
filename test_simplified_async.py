"""
Test Simplified Async Processing
Tests if disabling verification and clustering resolves the container hanging issue.
"""

import requests
import time

def test_simplified_async():
    """Test the simplified async processing without verification and clustering."""
    
    print("🚀 TESTING SIMPLIFIED ASYNC PROCESSING")
    print("=" * 45)
    
    # Create text that should trigger async processing
    test_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003). " * 50  # ~3KB
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    print(f"🔧 Async config: verification=OFF, clustering=OFF, ultra_fast=ON")
    
    try:
        print(f"\n📤 Submitting simplified async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Async task created: {task_id}")
                
                # Monitor with hope for faster completion
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                start_time = time.time()
                
                for attempt in range(20):  # 60 seconds total
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = time.time() - start_time
                                
                                # Print status every 6 seconds or on change
                                if attempt % 2 == 0:
                                    print(f"   [{elapsed:5.1f}s] Status: {status}")
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    
                                    print(f"\n🎉 SIMPLIFIED ASYNC SUCCESS!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   📋 Citations: {len(citations)}")
                                    
                                    # Check deduplication (should still work)
                                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                    unique_citations = set(citation_texts)
                                    duplicates = len(citation_texts) - len(unique_citations)
                                    
                                    print(f"   🔄 Total citations: {len(citation_texts)}")
                                    print(f"   ✨ Unique citations: {len(unique_citations)}")
                                    print(f"   🔁 Duplicates: {duplicates}")
                                    
                                    if duplicates == 0:
                                        print(f"   ✅ Deduplication: WORKING!")
                                    else:
                                        print(f"   ⚠️  Deduplication: {duplicates} duplicates found")
                                    
                                    # Show sample citations
                                    print(f"\n📋 Sample citations:")
                                    for i, citation in enumerate(citations[:3], 1):
                                        citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                                        case_name = citation.get('extracted_case_name', 'N/A')
                                        verified = citation.get('verified', False)
                                        print(f"   {i}. {citation_text}")
                                        print(f"      Case: {case_name}")
                                        print(f"      Verified: {verified} (expected: False)")
                                    
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown error')
                                    print(f"\n❌ SIMPLIFIED ASYNC FAILED!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   💥 Error: {error}")
                                    
                                    if "ultra-fast" in error.lower():
                                        print(f"   🔍 Ultra-fast processing issue detected")
                                    elif "verification" in error.lower():
                                        print(f"   🔍 Verification still causing issues")
                                    
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                elapsed = time.time() - start_time
                                print(f"\n🎉 SIMPLIFIED ASYNC SUCCESS (direct result)!")
                                print(f"   ⏱️  Time: {elapsed:.1f}s")
                                print(f"   📋 Citations: {len(citations)}")
                                return True
                        
                        elif status_response.status_code == 404:
                            if attempt < 3:
                                elapsed = time.time() - start_time
                                print(f"   [{elapsed:5.1f}s] Task not ready (404)")
                        
                    except Exception as e:
                        if attempt % 5 == 0:
                            elapsed = time.time() - start_time
                            print(f"   [{elapsed:5.1f}s] Connection error: {e}")
                    
                    time.sleep(3)
                
                elapsed = time.time() - start_time
                print(f"\n⏰ SIMPLIFIED ASYNC STILL HANGING")
                print(f"   ⏱️  Monitored for: {elapsed:.1f}s")
                print(f"   🔍 Even simplified processing hangs - deeper container issue")
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                print(f"⚠️  PROCESSED AS SYNC!")
                print(f"   Mode: {processing_mode}")
                print(f"   Citations: {len(citations)}")
                print(f"   Text may not be large enough to trigger async")
                return "sync"
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def compare_sync_vs_simplified_async():
    """Compare sync processing vs simplified async processing."""
    
    print(f"\n📊 SYNC VS SIMPLIFIED ASYNC COMPARISON")
    print("-" * 45)
    
    # Test sync processing
    print(f"🏠 Testing sync processing...")
    sync_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003)"  # Small for sync
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': sync_text}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' not in result.get('result', {}):
                citations = result.get('result', {}).get('citations', [])
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                
                print(f"   ✅ Sync: {processing_mode}, {len(citations)} citations")
                
                # Check deduplication in sync
                citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                unique_citations = set(citation_texts)
                duplicates = len(citation_texts) - len(unique_citations)
                
                print(f"   🔄 Sync deduplication: {len(citation_texts)} → {len(unique_citations)} ({duplicates} duplicates)")
                
                sync_success = True
            else:
                print(f"   ⚠️  Small text triggered async")
                sync_success = False
        else:
            print(f"   ❌ Sync failed: {response.status_code}")
            sync_success = False
            
    except Exception as e:
        print(f"   ❌ Sync error: {e}")
        sync_success = False
    
    # Test simplified async
    print(f"\n🚀 Testing simplified async processing...")
    async_success = test_simplified_async()
    
    return sync_success, async_success

def main():
    """Run comprehensive simplified async test."""
    
    print("🎯 SIMPLIFIED ASYNC PROCESSING TEST")
    print("=" * 35)
    
    print("🔧 CHANGES MADE:")
    print("   - Disabled verification (likely cause of hanging)")
    print("   - Disabled clustering (simplify processing)")
    print("   - Enabled ultra-fast processing")
    print("   - Removed complex timeout mechanism")
    
    sync_success, async_success = compare_sync_vs_simplified_async()
    
    print(f"\n📊 FINAL RESULTS")
    print("=" * 15)
    print(f"✅ Sync processing: {'WORKING' if sync_success else 'FAILED'}")
    
    if async_success == True:
        print(f"✅ Simplified async: WORKING!")
        print(f"\n🎉 CONTAINER ISSUE RESOLVED!")
        print(f"   The problem was verification/clustering in container environment")
    elif async_success == "sync":
        print(f"⚠️  Simplified async: Processed as sync")
        print(f"\n🔍 THRESHOLD ISSUE")
        print(f"   Text not large enough to trigger async processing")
    else:
        print(f"❌ Simplified async: STILL HANGING")
        print(f"\n🔍 DEEPER CONTAINER ISSUE")
        print(f"   Even ultra-fast processing hangs - fundamental problem")
        print(f"   May need container resource investigation or different approach")

if __name__ == "__main__":
    main()
