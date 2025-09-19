#!/usr/bin/env python3
"""
Test if async processing is working after the fix.
"""

import requests
import time
import json

def test_async_processing_fixed():
    """Test async processing with the fixed code."""
    
    # Create a large document that should trigger async processing
    base_text = """
    Legal Document with Multiple Citations
    
    This document contains several important legal citations:
    
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Criminal law case
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Municipal law
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014) - State constitutional law
    4. Davis v. County, 190 Wn.2d 400, 400 P.3d 900 (2017) - Administrative law
    5. Miller v. Corporation, 200 Wn.2d 500, 450 P.3d 1000 (2020) - Corporate law
    
    These cases establish important precedents in Washington State law.
    """
    
    # Make it large enough to definitely trigger async (20KB+)
    large_text = base_text + "\n\nLegal analysis paragraph with additional content. " * 600
    
    print("🧪 Testing Async Processing After Fix")
    print("=" * 50)
    print(f"📄 Document size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
    print(f"📝 Expected: 5+ citations from the base text")
    print()
    
    try:
        print("📤 Submitting large document...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success: {data.get('success')}")
            print(f"📝 Message: {data.get('message')}")
            
            # Check if we got async task
            if data.get('task_id'):
                print(f"🔄 Async task created: {data['task_id']}")
                print("📊 Monitoring task progress...")
                
                return monitor_task_completion(data['task_id'])
                
            else:
                # Sync processing or sync fallback
                citations = data.get('citations', [])
                clusters = data.get('clusters', [])
                processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
                
                print(f"⚡ Processed synchronously (mode: {processing_mode})")
                print(f"📊 Citations found: {len(citations)}")
                print(f"🔗 Clusters found: {len(clusters)}")
                
                if len(citations) > 0:
                    print("✅ Sync processing working!")
                    print("📋 Sample citations:")
                    for i, citation in enumerate(citations[:3]):
                        citation_text = citation.get('citation', 'N/A')
                        print(f"  {i+1}. {citation_text}")
                    return True
                else:
                    print("❌ Sync processing found 0 citations")
                    
                    # Check for error details
                    if 'error' in data:
                        print(f"🚨 Error: {data['error']}")
                    
                    metadata = data.get('metadata', {})
                    if 'error_details' in metadata:
                        print(f"🔍 Error details: {metadata['error_details']}")
                    
                    return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return False

def monitor_task_completion(task_id, max_wait=60):
    """Monitor async task until completion."""
    print(f"🔄 Monitoring task: {task_id}")
    
    for attempt in range(max_wait):
        try:
            response = requests.get(
                f"http://localhost:8080/casestrainer/api/task_status/{task_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                print(f"  📈 Attempt {attempt + 1}: {status}")
                
                if status == 'completed':
                    citations = data.get('citations', [])
                    clusters = data.get('clusters', [])
                    
                    print(f"✅ Async task completed!")
                    print(f"📊 Citations: {len(citations)}")
                    print(f"🔗 Clusters: {len(clusters)}")
                    
                    if len(citations) > 0:
                        print("📋 Sample citations:")
                        for i, citation in enumerate(citations[:3]):
                            citation_text = citation.get('citation', 'N/A')
                            case_name = citation.get('extracted_case_name', 'N/A')
                            print(f"  {i+1}. {citation_text} - {case_name}")
                        return True
                    else:
                        print("❌ Async task found 0 citations")
                        return False
                        
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    print(f"❌ Async task failed: {error}")
                    return False
                    
            elif response.status_code == 404:
                print(f"❌ Task not found: {task_id}")
                return False
                
            time.sleep(1)
            
        except Exception as e:
            print(f"  ⚠️ Status check failed: {e}")
            time.sleep(1)
    
    print(f"⏰ Task timed out after {max_wait} seconds")
    return False

if __name__ == "__main__":
    success = test_async_processing_fixed()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Async processing test")
