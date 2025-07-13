#!/usr/bin/env python3
"""
Script to clear all caches and test both sync and async processing.
"""

import os
import sys
import json
import time
import requests
import redis
import sqlite3
from pathlib import Path

def clear_all_caches():
    """Clear all caches that might be causing issues."""
    print("CLEARING ALL CACHES")
    print("=" * 60)
    
    # 1. Clear Redis cache
    print("1. Clearing Redis cache...")
    try:
        redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        redis_conn.flushdb()
        print("   ✅ Redis cache cleared")
    except Exception as e:
        print(f"   ⚠ Redis not available: {e}")
    
    # 2. Clear SQLite cache
    print("2. Clearing SQLite cache...")
    cache_files = [
        "src/citations.db",
        "citation_cache/citations.db", 
        "data/citations.db",
        "cache/citations.db"
    ]
    
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"   ✅ Removed: {cache_file}")
            except Exception as e:
                print(f"   ⚠ Could not remove {cache_file}: {e}")
    
    # 3. Clear file caches
    print("3. Clearing file caches...")
    cache_dirs = [
        "citation_cache",
        "cache",
        "temp",
        "temp_uploads"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                import shutil
                shutil.rmtree(cache_dir)
                print(f"   ✅ Cleared directory: {cache_dir}")
            except Exception as e:
                print(f"   ⚠ Could not clear {cache_dir}: {e}")
    
    # 4. Clear memory caches in Python modules
    print("4. Clearing Python memory caches...")
    try:
        # Clear any LRU caches
        import functools
        functools._lru_cache_wrapper.cache_clear()
        print("   ✅ Python LRU caches cleared")
    except Exception as e:
        print(f"   ⚠ Could not clear Python caches: {e}")
    
    print("✅ All caches cleared!")

def test_sync_processing():
    """Test synchronous processing (immediate response)."""
    print("\nTESTING SYNC PROCESSING")
    print("=" * 60)
    
    url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    
    # Short text that should trigger immediate processing
    test_text = "Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."
    
    print(f"Test text: {test_text}")
    print()
    
    try:
        response = requests.post(url, json={"text": test_text}, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's immediate response or async
            if "task_id" in data:
                print("⚠ Async response received (should be sync for short text)")
                print(f"Task ID: {data['task_id']}")
                return False
            else:
                print("✅ Sync response received")
                citations = data.get('citations', [])
                print(f"Found {len(citations)} citations")
                
                for i, citation in enumerate(citations):
                    print(f"\nCitation {i+1}:")
                    print(f"  Citation: {citation.get('citation', 'N/A')}")
                    print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
                    print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
                    print(f"  URL: {citation.get('url', 'N/A')}")
                    print(f"  Verified: {citation.get('verified', 'N/A')}")
                    
                    # Check for the problematic citation
                    if "146 Wn.2d 1" in citation.get('citation', ''):
                        print(f"  *** THIS IS THE PROBLEMATIC CITATION ***")
                        if citation.get('canonical_name') == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                            print(f"  ✅ CORRECT CASE NAME FOUND!")
                            return True
                        else:
                            print(f"  ❌ WRONG CASE NAME: {citation.get('canonical_name')}")
                            return False
                
                return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_async_processing():
    """Test asynchronous processing."""
    print("\nTESTING ASYNC PROCESSING")
    print("=" * 60)
    
    url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    
    # Longer text that should trigger async processing
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    
    This is additional text to make the document longer and trigger async processing. The system should process this asynchronously and return a task ID that can be used to poll for results.
    """ * 10  # Repeat to make it longer
    
    print(f"Test text length: {len(test_text)} characters")
    print()
    
    try:
        response = requests.post(url, json={"text": test_text}, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's async response
            if "task_id" in data:
                print("✅ Async response received")
                task_id = data['task_id']
                print(f"Task ID: {task_id}")
                
                # Poll for results
                return poll_async_results(task_id)
            else:
                print("⚠ Sync response received (should be async for long text)")
                return False
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def poll_async_results(task_id):
    """Poll for async task results."""
    print(f"\nPolling for task {task_id} results...")
    
    url = f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}"
    max_wait = 120  # 2 minutes
    poll_interval = 2  # seconds
    
    for attempt in range(max_wait // poll_interval):
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                print(f"Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print("✅ Task completed!")
                    citations = data.get('citations', [])
                    print(f"Found {len(citations)} citations")
                    
                    for i, citation in enumerate(citations):
                        print(f"\nCitation {i+1}:")
                        print(f"  Citation: {citation.get('citation', 'N/A')}")
                        print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
                        print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
                        print(f"  URL: {citation.get('url', 'N/A')}")
                        print(f"  Verified: {citation.get('verified', 'N/A')}")
                        
                        # Check for the problematic citation
                        if "146 Wn.2d 1" in citation.get('citation', ''):
                            print(f"  *** THIS IS THE PROBLEMATIC CITATION ***")
                            if citation.get('canonical_name') == "Department of Ecology v. Campbell & Gwinn, L.L.C.":
                                print(f"  ✅ CORRECT CASE NAME FOUND!")
                                return True
                            else:
                                print(f"  ❌ WRONG CASE NAME: {citation.get('canonical_name')}")
                                return False
                    
                    return True
                    
                elif status == 'failed':
                    print(f"❌ Task failed: {data.get('error', 'Unknown error')}")
                    return False
                    
                elif status == 'processing':
                    progress = data.get('progress', 0)
                    current_step = data.get('current_step', 'Unknown')
                    print(f"  Progress: {progress}% - {current_step}")
                
            else:
                print(f"Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Error polling: {e}")
        
        time.sleep(poll_interval)
    
    print("❌ Timeout waiting for task completion")
    return False

def main():
    """Main test function."""
    print("CACHE CLEARING AND PROCESSING TEST")
    print("=" * 60)
    
    # Clear all caches
    clear_all_caches()
    
    # Test sync processing
    sync_success = test_sync_processing()
    
    # Test async processing
    async_success = test_async_processing()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Sync Processing: {'✅ PASSED' if sync_success else '❌ FAILED'}")
    print(f"Async Processing: {'✅ PASSED' if async_success else '❌ FAILED'}")
    
    if sync_success and async_success:
        print("\n🎉 All tests passed! The issue was likely cached data.")
    else:
        print("\n⚠ Some tests failed. The issue may be deeper than caching.")

if __name__ == "__main__":
    main() 