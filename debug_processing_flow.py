#!/usr/bin/env python3
"""
Debug the actual processing flow to see what's happening with large documents.
"""

import requests
import json

def debug_processing_flow():
    """Debug the processing flow with detailed logging."""
    
    # Create a document that should definitely trigger async (10KB+)
    base_text = """
    Legal Document Analysis Test
    
    This document contains several important legal citations that should be extracted:
    
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Important precedent case
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Municipal law case  
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014) - Criminal procedure case
    4. Davis v. County, 190 Wn.2d 400, 400 P.3d 900 (2017) - Administrative law case
    5. Miller v. Corporation, 200 Wn.2d 500, 450 P.3d 1000 (2020) - Corporate law case
    
    Additional legal analysis and commentary follows...
    """
    
    # Pad to make it definitely large (15KB+)
    large_text = base_text + "\n\nLegal analysis paragraph. " * 500
    
    print("🔍 Debugging Large Document Processing Flow")
    print("=" * 60)
    print(f"📄 Document size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
    print(f"📝 Expected citations: State v. Johnson, City of Seattle v. Williams, Brown v. State, Davis v. County, Miller v. Corporation")
    print()
    
    try:
        print("📤 Submitting document to API...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=60
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n🔍 Response Analysis:")
            print(f"  Success: {data.get('success')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Has task_id: {'task_id' in data}")
            
            if 'task_id' in data:
                print(f"  Task ID: {data['task_id']}")
                print("  🔄 ASYNC PROCESSING TRIGGERED")
                
                # Check progress data
                if 'progress_data' in data:
                    progress = data['progress_data']
                    print(f"  Progress: {progress.get('overall_progress', 0)}%")
                    print(f"  Status: {progress.get('status')}")
                    print(f"  Current step: {progress.get('current_step')}")
                
                return monitor_async_task(data['task_id'])
            else:
                print("  ⚡ SYNC PROCESSING USED")
                
                # Analyze sync results
                citations = data.get('citations', [])
                clusters = data.get('clusters', [])
                metadata = data.get('metadata', {})
                
                print(f"  Citations found: {len(citations)}")
                print(f"  Clusters found: {len(clusters)}")
                print(f"  Processing mode: {metadata.get('processing_mode', 'unknown')}")
                
                if len(citations) == 0:
                    print("\n❌ PROBLEM: Sync processing found 0 citations")
                    print("🔍 Investigating sync processing issue...")
                    return investigate_sync_issue(large_text)
                else:
                    print(f"\n✅ Sync processing working: {len(citations)} citations found")
                    return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Debug failed: {e}")
        return False

def monitor_async_task(task_id):
    """Monitor async task completion."""
    print(f"\n🔄 Monitoring async task: {task_id}")
    
    import time
    max_attempts = 60  # 1 minute
    
    for attempt in range(max_attempts):
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
                    
                    print(f"\n✅ Async task completed!")
                    print(f"  Citations: {len(citations)}")
                    print(f"  Clusters: {len(clusters)}")
                    
                    if len(citations) > 0:
                        print("  📋 Sample citations:")
                        for i, citation in enumerate(citations[:3]):
                            print(f"    {i+1}. {citation.get('citation', 'N/A')}")
                        return True
                    else:
                        print("  ❌ Async processing found 0 citations")
                        return False
                        
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    print(f"\n❌ Async task failed: {error}")
                    return False
                    
            time.sleep(1)
            
        except Exception as e:
            print(f"    ⚠️ Status check failed: {e}")
            time.sleep(1)
    
    print(f"\n⏰ Async task timed out after {max_attempts} seconds")
    return False

def investigate_sync_issue(text):
    """Investigate why sync processing isn't finding citations."""
    print("\n🔬 Investigating Sync Processing Issue")
    print("=" * 50)
    
    # Test with just the citation-rich part
    citation_part = """
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)  
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    """
    
    print(f"📝 Testing citation-rich excerpt ({len(citation_part)} chars)...")
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": citation_part},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            
            print(f"  📊 Citations found in excerpt: {len(citations)}")
            
            if len(citations) > 0:
                print("  ✅ Citations ARE being found in small excerpts")
                print("  🔍 Issue: Large document size is breaking citation extraction")
                return False
            else:
                print("  ❌ Citations NOT found even in small excerpt")
                print("  🔍 Issue: Core citation extraction problem")
                return False
        else:
            print(f"  ❌ Excerpt test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  💥 Excerpt test error: {e}")
        return False

if __name__ == "__main__":
    success = debug_processing_flow()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Large document processing debug")
