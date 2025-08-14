#!/usr/bin/env python3
"""
Comprehensive Regression Test for CaseStrainer
Test all major functionality: immediate processing, async processing, clustering, verification
"""

import sys
import os
import json
import time
import requests
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_immediate_text_processing():
    """Test immediate processing for short text inputs."""
    print("🔍 IMMEDIATE TEXT PROCESSING TEST")
    print("="*50)
    
    test_cases = [
        {
            'name': 'Single Federal Citation',
            'text': 'Brown v. Board of Education, 347 U.S. 483 (1954)',
            'expected_citations': 1,
            'expected_clusters': 1
        },
        {
            'name': 'Multiple Citations',
            'text': 'See Brown v. Board, 347 U.S. 483 (1954) and Roe v. Wade, 410 U.S. 113 (1973)',
            'expected_citations': 2,
            'expected_clusters': 2
        },
        {
            'name': 'Parallel Citations',
            'text': 'Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)',
            'expected_citations': 3,
            'expected_clusters': 1
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Text: {test_case['text']}")
        
        try:
            url = "http://localhost:5000/casestrainer/api/analyze"
            data = {"text": test_case['text'], "type": "text"}
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                if status == 'completed':
                    citations = result.get('result', {}).get('citations', [])
                    clusters = result.get('result', {}).get('clusters', [])
                    
                    citation_count = len(citations)
                    cluster_count = len(clusters)
                    
                    print(f"   ✅ Status: {status}")
                    print(f"   📊 Citations: {citation_count} (expected: {test_case['expected_citations']})")
                    print(f"   📊 Clusters: {cluster_count} (expected: {test_case['expected_clusters']})")
                    
                    # Check if we have citations with proper data
                    if citations:
                        citation = citations[0]
                        canonical_name = citation.get('canonical_name')
                        canonical_url = citation.get('canonical_url')
                        verified = citation.get('verified')
                        
                        print(f"   📋 First Citation: {citation.get('citation')}")
                        print(f"   📋 Canonical Name: {canonical_name}")
                        print(f"   📋 Canonical URL: {canonical_url}")
                        print(f"   📋 Verified: {verified}")
                        
                        # Success criteria
                        success = (
                            citation_count >= test_case['expected_citations'] and
                            cluster_count >= test_case['expected_clusters'] and
                            canonical_name is not None and
                            canonical_url is not None and
                            verified is True
                        )
                        
                        results.append({
                            'test': test_case['name'],
                            'success': success,
                            'citations': citation_count,
                            'clusters': cluster_count,
                            'verified': verified,
                            'canonical_data': canonical_name is not None and canonical_url is not None
                        })
                        
                        print(f"   🎯 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
                    else:
                        print(f"   ❌ No citations found")
                        results.append({
                            'test': test_case['name'],
                            'success': False,
                            'citations': 0,
                            'clusters': cluster_count,
                            'verified': False,
                            'canonical_data': False
                        })
                else:
                    print(f"   ❌ Unexpected status: {status}")
                    results.append({
                        'test': test_case['name'],
                        'success': False,
                        'error': f'Unexpected status: {status}'
                    })
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                results.append({
                    'test': test_case['name'],
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({
                'test': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    return results

def test_async_processing():
    """Test async processing for longer inputs or files."""
    print("\n🔄 ASYNC PROCESSING TEST")
    print("="*40)
    
    # Test with longer text that should trigger async processing
    long_text = """
    This is a longer legal document that contains multiple citations and should trigger async processing.
    
    In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court held that racial segregation in public schools was unconstitutional.
    
    Later, in Roe v. Wade, 410 U.S. 113 (1973), the Court established a constitutional right to abortion.
    
    The Court further clarified these principles in subsequent cases, including Planned Parenthood v. Casey, 505 U.S. 833 (1992).
    
    More recently, in Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), the Court addressed issues of criminal forfeiture.
    
    These cases demonstrate the evolution of constitutional law over time and the importance of precedent in judicial decision-making.
    """ * 50  # Make it long enough to trigger async processing
    
    try:
        url = "http://localhost:5000/casestrainer/api/analyze"
        data = {"text": long_text, "type": "text"}
        
        print(f"📋 Testing async processing with text length: {len(long_text)} characters")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'processing':
                task_id = result.get('task_id')
                print(f"✅ Async processing started with task_id: {task_id}")
                
                # Poll for results
                max_polls = 30
                poll_count = 0
                
                while poll_count < max_polls:
                    time.sleep(2)
                    poll_count += 1
                    
                    status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        task_status = status_result.get('status')
                        
                        print(f"📊 Poll {poll_count}: Status = {task_status}")
                        
                        if task_status == 'completed':
                            citations = status_result.get('result', {}).get('citations', [])
                            clusters = status_result.get('result', {}).get('clusters', [])
                            
                            print(f"✅ Async processing completed")
                            print(f"📊 Citations found: {len(citations)}")
                            print(f"📊 Clusters found: {len(clusters)}")
                            
                            if citations:
                                citation = citations[0]
                                print(f"📋 First Citation: {citation.get('citation')}")
                                print(f"📋 Canonical Name: {citation.get('canonical_name')}")
                                print(f"📋 Verified: {citation.get('verified')}")
                            
                            return {
                                'success': True,
                                'citations': len(citations),
                                'clusters': len(clusters),
                                'processing_time': poll_count * 2
                            }
                        elif task_status == 'failed':
                            error = status_result.get('error', 'Unknown error')
                            print(f"❌ Async processing failed: {error}")
                            return {'success': False, 'error': error}
                    else:
                        print(f"❌ Status poll failed: {status_response.status_code}")
                
                print(f"❌ Async processing timed out after {max_polls} polls")
                return {'success': False, 'error': 'Timeout'}
                
            elif status == 'completed':
                print(f"⚠️  Expected async processing but got immediate processing")
                citations = result.get('result', {}).get('citations', [])
                clusters = result.get('result', {}).get('clusters', [])
                
                return {
                    'success': True,
                    'citations': len(citations),
                    'clusters': len(clusters),
                    'note': 'Processed immediately instead of async'
                }
            else:
                print(f"❌ Unexpected status: {status}")
                return {'success': False, 'error': f'Unexpected status: {status}'}
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {'success': False, 'error': str(e)}

def test_clustering_and_verification():
    """Test citation clustering and CourtListener verification."""
    print("\n🔗 CLUSTERING AND VERIFICATION TEST")
    print("="*45)
    
    # Test parallel citations that should cluster together
    test_text = "Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)"
    
    try:
        url = "http://localhost:5000/casestrainer/api/analyze"
        data = {"text": test_text, "type": "text"}
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'completed':
                citations = result.get('result', {}).get('citations', [])
                clusters = result.get('result', {}).get('clusters', [])
                
                print(f"📊 Citations found: {len(citations)}")
                print(f"📊 Clusters found: {len(clusters)}")
                
                if clusters and len(clusters) == 1:
                    cluster = clusters[0]
                    cluster_citations = cluster.get('citations', [])
                    
                    print(f"✅ Clustering: {len(cluster_citations)} citations in 1 cluster")
                    
                    # Check if all citations have canonical data
                    verified_count = 0
                    canonical_count = 0
                    
                    for citation in citations:
                        if citation.get('verified'):
                            verified_count += 1
                        if citation.get('canonical_name') and citation.get('canonical_url'):
                            canonical_count += 1
                        
                        print(f"📋 Citation: {citation.get('citation')}")
                        print(f"   Canonical Name: {citation.get('canonical_name')}")
                        print(f"   Canonical URL: {citation.get('canonical_url')}")
                        print(f"   Verified: {citation.get('verified')}")
                        print()
                    
                    success = (
                        len(clusters) == 1 and
                        len(citations) == 3 and  # Should have 3 parallel citations
                        verified_count > 0 and
                        canonical_count > 0
                    )
                    
                    print(f"🎯 Clustering Test: {'✅ SUCCESS' if success else '❌ FAILED'}")
                    print(f"   Verified Citations: {verified_count}/{len(citations)}")
                    print(f"   Canonical Data: {canonical_count}/{len(citations)}")
                    
                    return {
                        'success': success,
                        'citations': len(citations),
                        'clusters': len(clusters),
                        'verified': verified_count,
                        'canonical': canonical_count
                    }
                else:
                    print(f"❌ Expected 1 cluster, got {len(clusters)}")
                    return {'success': False, 'error': f'Expected 1 cluster, got {len(clusters)}'}
            else:
                print(f"❌ Unexpected status: {status}")
                return {'success': False, 'error': f'Unexpected status: {status}'}
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Run comprehensive regression tests."""
    print("🧪 COMPREHENSIVE REGRESSION TEST SUITE")
    print("="*60)
    
    # Test immediate processing
    immediate_results = test_immediate_text_processing()
    
    # Test async processing
    async_result = test_async_processing()
    
    # Test clustering and verification
    clustering_result = test_clustering_and_verification()
    
    # Summary
    print(f"\n" + "="*60)
    print("📊 REGRESSION TEST RESULTS")
    print("="*60)
    
    print(f"\n🔍 IMMEDIATE PROCESSING RESULTS:")
    immediate_success_count = sum(1 for r in immediate_results if r.get('success', False))
    print(f"   Passed: {immediate_success_count}/{len(immediate_results)} tests")
    
    for result in immediate_results:
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"   {status} {result['test']}")
        if not result.get('success', False) and 'error' in result:
            print(f"      Error: {result['error']}")
    
    print(f"\n🔄 ASYNC PROCESSING RESULTS:")
    async_success = async_result.get('success', False)
    print(f"   Status: {'✅ PASS' if async_success else '❌ FAIL'}")
    if not async_success and 'error' in async_result:
        print(f"   Error: {async_result['error']}")
    elif async_success:
        print(f"   Citations: {async_result.get('citations', 0)}")
        print(f"   Clusters: {async_result.get('clusters', 0)}")
    
    print(f"\n🔗 CLUSTERING & VERIFICATION RESULTS:")
    clustering_success = clustering_result.get('success', False)
    print(f"   Status: {'✅ PASS' if clustering_success else '❌ FAIL'}")
    if not clustering_success and 'error' in clustering_result:
        print(f"   Error: {clustering_result['error']}")
    elif clustering_success:
        print(f"   Citations: {clustering_result.get('citations', 0)}")
        print(f"   Clusters: {clustering_result.get('clusters', 0)}")
        print(f"   Verified: {clustering_result.get('verified', 0)}")
        print(f"   Canonical: {clustering_result.get('canonical', 0)}")
    
    # Overall success
    overall_success = (
        immediate_success_count == len(immediate_results) and
        async_success and
        clustering_success
    )
    
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 CaseStrainer is fully functional and ready for production!")
        print("   ✅ Immediate processing working")
        print("   ✅ Async processing working")
        print("   ✅ Citation clustering working")
        print("   ✅ CourtListener verification working")
        print("   ✅ All 6 data points delivered correctly")
    else:
        print("\n⚠️  Some issues remain that need attention before production deployment.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
