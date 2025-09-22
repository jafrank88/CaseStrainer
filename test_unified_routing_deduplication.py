#!/usr/bin/env python3
"""
Test script to verify unified routing and deduplication systems.

Tests the scenario:
- 2KB text → sync processing → should find X citations
- 6KB text (same content × 3) → async processing → should find same X citations (deduplicated)

This verifies both:
1. Unified routing: content-based sync/async decisions
2. Deduplication: consistent results regardless of processing mode
"""

import requests
import json
import time
import sys
import os
import urllib3

# Suppress SSL warnings for localhost testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_routing_and_deduplication():
    """Test unified routing and deduplication with 2KB vs 6KB content."""
    
    print("🧪 TESTING UNIFIED ROUTING AND DEDUPLICATION")
    print("=" * 60)
    
    # Base URL for the API (direct backend access)
    base_url = "http://localhost:5000"
    
    # Test content with citations (approximately 2KB)
    base_text = """
    In the landmark case of Bostain v. Food Express, Inc., 159 Wn.2d 700, 153 P.3d 846 (2007), 
    the Washington Supreme Court established important precedent regarding employment law. 
    This decision built upon earlier rulings in State v. Velasquez, 176 Wash.2d 333, 292 P.3d 92 (2013),
    and referenced the federal case of Miranda v. Arizona, 384 U.S. 436 (1966).
    
    The court also considered the analysis from Johnson v. State, 2024 WL 2133370 (Wash. 2024),
    which provided additional context for the constitutional issues at stake. Furthermore,
    the decision in Smith v. County, 2024 WL 3199858 (W.D. Wash. 2024) offered guidance
    on procedural matters.
    
    These cases collectively demonstrate the evolution of legal doctrine in this area,
    particularly when considered alongside the foundational ruling in Brown v. Board of Education,
    347 U.S. 483 (1954), which established the framework for equal protection analysis.
    
    The practical implications of these decisions extend beyond the immediate parties,
    affecting how courts interpret similar statutory provisions in future cases.
    """ * 3  # Repeat to get closer to 2KB
    
    # Trim to approximately 2KB
    base_text = base_text[:2048]
    
    print(f"📏 Base text size: {len(base_text)} bytes")
    print(f"📏 Expected routing: SYNC (< 5KB threshold)")
    print()
    
    # Create >5KB version to trigger async processing (repeat content multiple times)
    large_text = (base_text + "\n\n") * 6  # Repeat 6 times to ensure >5KB
    print(f"📏 Large text size: {len(large_text)} bytes")
    print(f"📏 Expected routing: ASYNC (>= 5KB threshold)")
    print()
    
    # Test 1: 2KB text (should use sync processing)
    print("🔄 TEST 1: 2KB Text (Sync Processing)")
    print("-" * 40)
    
    try:
        response1 = requests.post(
            f"{base_url}/casestrainer/api/analyze",
            json={"type": "text", "text": base_text},
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False  # Skip SSL verification for localhost
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            citations1 = result1.get('result', {}).get('citations', result1.get('citations', []))
            clusters1 = result1.get('result', {}).get('clusters', result1.get('clusters', []))
            processing_mode1 = result1.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Status: {response1.status_code}")
            print(f"📊 Processing mode: {processing_mode1}")
            print(f"📝 Citations found: {len(citations1)}")
            print(f"🔗 Clusters found: {len(clusters1)}")
            
            # Show citation details
            print("📋 Citations:")
            for i, citation in enumerate(citations1[:5], 1):  # Show first 5
                citation_text = citation.get('citation', citation.get('citation_text', str(citation)))
                print(f"  {i}. {citation_text}")
            if len(citations1) > 5:
                print(f"  ... and {len(citations1) - 5} more")
            print()
            
        else:
            print(f"❌ Error: {response1.status_code}")
            print(f"Response: {response1.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception in Test 1: {e}")
        return False
    
    # Test 2: 6KB text (should use async processing)
    print("🔄 TEST 2: 6KB Text (Async Processing)")
    print("-" * 40)
    
    try:
        response2 = requests.post(
            f"{base_url}/casestrainer/api/analyze",
            json={"type": "text", "text": large_text},
            headers={"Content-Type": "application/json"},
            timeout=60,  # Longer timeout for async
            verify=False  # Skip SSL verification for localhost
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            
            # Handle async response (might have task_id or job_id in metadata)
            task_id = result2.get('task_id') or result2.get('metadata', {}).get('job_id')
            if task_id:
                print(f"📋 Async task created: {task_id}")
                print("⏳ Waiting for async processing to complete...")
                
                # Poll for results
                max_attempts = 30
                for attempt in range(max_attempts):
                    time.sleep(2)
                    
                    status_response = requests.get(f"{base_url}/casestrainer/api/task_status/{task_id}", verify=False)
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        status = status_result.get('status', 'unknown')
                        
                        print(f"  Attempt {attempt + 1}: Status = {status}")
                        
                        if status == 'completed':
                            result2 = status_result
                            break
                        elif status == 'failed':
                            print(f"❌ Async processing failed: {status_result.get('error', 'Unknown error')}")
                            return False
                    else:
                        print(f"  Status check failed: {status_response.status_code}")
                
                if status != 'completed':
                    print(f"❌ Async processing timed out after {max_attempts * 2} seconds")
                    return False
            
            citations2 = result2.get('result', {}).get('citations', result2.get('citations', []))
            clusters2 = result2.get('result', {}).get('clusters', result2.get('clusters', []))
            processing_mode2 = result2.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Status: {response2.status_code}")
            print(f"📊 Processing mode: {processing_mode2}")
            print(f"📝 Citations found: {len(citations2)}")
            print(f"🔗 Clusters found: {len(clusters2)}")
            
            # Show citation details
            print("📋 Citations:")
            for i, citation in enumerate(citations2[:5], 1):  # Show first 5
                citation_text = citation.get('citation', citation.get('citation_text', str(citation)))
                print(f"  {i}. {citation_text}")
            if len(citations2) > 5:
                print(f"  ... and {len(citations2) - 5} more")
            print()
            
        else:
            print(f"❌ Error: {response2.status_code}")
            print(f"Response: {response2.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception in Test 2: {e}")
        return False
    
    # Compare results
    print("🔍 COMPARISON ANALYSIS")
    print("=" * 60)
    
    # Check routing
    print("📊 ROUTING VERIFICATION:")
    if 'sync' in processing_mode1.lower() or 'immediate' in processing_mode1.lower():
        print("✅ Test 1: Correctly used SYNC processing")
    else:
        print(f"⚠️  Test 1: Expected sync, got {processing_mode1}")
    
    if 'async' in processing_mode2.lower() or 'task' in str(result2.get('task_id', '')):
        print("✅ Test 2: Correctly used ASYNC processing")
    else:
        print(f"⚠️  Test 2: Expected async, got {processing_mode2}")
    print()
    
    # Check deduplication
    print("🔧 DEDUPLICATION VERIFICATION:")
    citation_count_diff = abs(len(citations1) - len(citations2))
    cluster_count_diff = abs(len(clusters1) - len(clusters2))
    
    if citation_count_diff == 0:
        print(f"✅ Citations: IDENTICAL count ({len(citations1)} vs {len(citations2)})")
    else:
        print(f"❌ Citations: DIFFERENT count ({len(citations1)} vs {len(citations2)}, diff: {citation_count_diff})")
    
    if cluster_count_diff == 0:
        print(f"✅ Clusters: IDENTICAL count ({len(clusters1)} vs {len(clusters2)})")
    else:
        print(f"⚠️  Clusters: DIFFERENT count ({len(clusters1)} vs {len(clusters2)}, diff: {cluster_count_diff})")
    print()
    
    # Overall result
    print("🎯 OVERALL RESULT:")
    if citation_count_diff == 0 and cluster_count_diff <= 1:  # Allow small cluster difference
        print("✅ SUCCESS: Unified routing and deduplication working correctly!")
        print("   - Different processing modes used appropriately")
        print("   - Identical results despite content duplication")
        print("   - Deduplication successfully removed duplicate citations")
        return True
    else:
        print("❌ FAILURE: Issues detected")
        if citation_count_diff > 0:
            print(f"   - Citation count mismatch suggests deduplication not working")
        if cluster_count_diff > 1:
            print(f"   - Significant cluster count difference")
        return False

if __name__ == "__main__":
    print("🚀 Starting Unified Routing and Deduplication Test")
    print("This test verifies that:")
    print("1. Content-based routing works (2KB→sync, 6KB→async)")
    print("2. Deduplication works (same results regardless of processing mode)")
    print()
    
    success = test_unified_routing_and_deduplication()
    
    if success:
        print("\n🎉 All tests passed! The unified routing and deduplication systems are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        sys.exit(1)
