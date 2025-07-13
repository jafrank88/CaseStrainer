#!/usr/bin/env python3
"""
Test script to verify Wolf frontend/async processing returns clusters correctly.
"""

import requests
import json
import time
import sys

def test_wolf_async_processing():
    """Test the Wolf async processing endpoint to see if clusters are returned."""
    
    # Wolf production URL
    base_url = "https://wolf.law.uw.edu"
    analyze_url = f"{base_url}/casestrainer/api/analyze"
    status_url = f"{base_url}/casestrainer/api/task_status"
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
    
    print("🧪 Testing Wolf async processing...")
    print(f"🌐 URL: {analyze_url}")
    print(f"📝 Test text: {test_text[:100]}...")
    
    try:
        # Step 1: Submit the analysis request
        print("\n📤 Submitting analysis request...")
        payload = {
            'text': test_text,
            'type': 'text'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(analyze_url, json=payload, headers=headers, timeout=30)
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code != 200 and response.status_code != 202:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse response
        try:
            result = response.json()
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
        
        print(f"📋 Response: {json.dumps(result, indent=2)}")
        
        # Check if it's immediate or async
        if result.get('status') == 'completed':
            print("⚡ Got immediate response")
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"📊 Citations: {len(citations)}")
            print(f"🔗 Clusters: {len(clusters)}")
            
            if clusters:
                print("🎉 SUCCESS: Clusters present in immediate response!")
                for i, cluster in enumerate(clusters):
                    print(f"   Cluster {i+1}: {cluster.get('canonical_name', 'N/A')} ({len(cluster.get('citations', []))} citations)")
            else:
                print("❌ FAILURE: No clusters in immediate response")
                return False
                
        else:
            # Async processing
            task_id = result.get('task_id')
            if not task_id:
                print("❌ No task_id in response")
                return False
                
            print(f"🔄 Async processing - Task ID: {task_id}")
            
            # Step 2: Poll for results
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                print(f"⏳ Polling attempt {attempt}/{max_attempts}...")
                
                try:
                    status_response = requests.get(f"{status_url}/{task_id}", timeout=10)
                    if status_response.status_code != 200:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        time.sleep(2)
                        continue
                    
                    status_result = status_response.json()
                    print(f"📋 Status: {status_result.get('status')}")
                    
                    if status_result.get('status') == 'completed':
                        print("✅ Task completed!")
                        
                        # Check for clusters in the result
                        citations = status_result.get('citations', [])
                        clusters = status_result.get('clusters', [])
                        
                        print(f"📊 Citations: {len(citations)}")
                        print(f"🔗 Clusters: {len(clusters)}")
                        
                        if clusters:
                            print("🎉 SUCCESS: Clusters present in async response!")
                            for i, cluster in enumerate(clusters):
                                print(f"   Cluster {i+1}: {cluster.get('canonical_name', 'N/A')} ({len(cluster.get('citations', []))} citations)")
                            return True
                        else:
                            print("❌ FAILURE: No clusters in async response")
                            print(f"Full response: {json.dumps(status_result, indent=2)}")
                            return False
                            
                    elif status_result.get('status') == 'failed':
                        print(f"❌ Task failed: {status_result.get('error', 'Unknown error')}")
                        return False
                        
                    else:
                        # Still processing
                        progress = status_result.get('progress', 0)
                        current_step = status_result.get('current_step', 'Unknown')
                        print(f"🔄 Progress: {progress}% - {current_step}")
                        time.sleep(2)
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Request error: {e}")
                    time.sleep(2)
                    continue
            
            print("⏰ Timeout waiting for task completion")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_local_async_processing():
    """Test local async processing for comparison."""
    
    print("\n" + "="*50)
    print("🧪 Testing local async processing for comparison...")
    
    try:
        # Import local service
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from api.services.citation_service import CitationService
        
        # Test text
        test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
        
        service = CitationService()
        
        # Test async processing
        result = service.process_citation_task('test-local', 'text', {'text': test_text})
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"📊 Local citations: {len(citations)}")
        print(f"🔗 Local clusters: {len(clusters)}")
        
        if clusters:
            print("✅ Local processing has clusters")
            for i, cluster in enumerate(clusters):
                print(f"   Cluster {i+1}: {cluster.get('canonical_name', 'N/A')} ({len(cluster.get('citations', []))} citations)")
        else:
            print("❌ Local processing missing clusters")
            
        return len(clusters) > 0
        
    except Exception as e:
        print(f"💥 Local test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Wolf async processing test...")
    
    # Test local first
    local_success = test_local_async_processing()
    
    # Test Wolf
    wolf_success = test_wolf_async_processing()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS:")
    print(f"   Local processing: {'✅ SUCCESS' if local_success else '❌ FAILURE'}")
    print(f"   Wolf processing: {'✅ SUCCESS' if wolf_success else '❌ FAILURE'}")
    
    if local_success and wolf_success:
        print("🎉 Both local and Wolf are working correctly!")
        sys.exit(0)
    elif local_success and not wolf_success:
        print("⚠️ Local works but Wolf doesn't - deployment issue")
        sys.exit(1)
    elif not local_success and wolf_success:
        print("⚠️ Wolf works but local doesn't - strange!")
        sys.exit(1)
    else:
        print("❌ Both local and Wolf are failing")
        sys.exit(1) 