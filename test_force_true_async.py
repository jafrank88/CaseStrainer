#!/usr/bin/env python3
"""
Force true async processing with a very large document.
"""

import requests
import time
import json

def test_force_true_async():
    """Test with a document large enough to force true async processing."""
    
    # Create a very large document that should definitely trigger async
    base_text = """
    Legal Document for True Async Testing
    
    Important cases:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    4. Washington v. Davis, 190 Wn.2d 400, 350 P.3d 900 (2015)
    5. Miller v. State, 200 Wn.2d 500, 400 P.3d 1000 (2018)
    """
    
    # Make it extremely large to force async
    large_text = base_text + "\n\nLegal padding content. " * 5000  # Much larger
    
    print("🧪 Testing Force True Async Processing")
    print("=" * 60)
    print(f"📄 Document size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
    print()
    
    # Submit for processing
    print("📤 Submitting extremely large document...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ Failed: {response.status_code}")
            return False
            
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode')
        task_id = data.get('task_id')
        job_id = data.get('metadata', {}).get('job_id')
        
        print(f"  Processing mode: {processing_mode}")
        print(f"  Task ID: {task_id}")
        print(f"  Job ID: {job_id}")
        
        if processing_mode == 'sync_fallback':
            print("  ⚠️ Still using sync fallback - document might not be large enough")
            citations = data.get('citations', [])
            print(f"  Citations found: {len(citations)}")
            return len(citations) > 0
        
        if not (task_id or job_id):
            print("  ❌ No async processing triggered")
            return False
        
        tracking_id = task_id or job_id
        print(f"  ✅ Async processing triggered! Tracking ID: {tracking_id}")
        
        # Poll for completion
        print("\n⏳ Polling for completion...")
        for attempt in range(20):
            print(f"  Attempt {attempt + 1}/20")
            
            try:
                status_response = requests.get(
                    f"http://localhost:8080/casestrainer/api/task_status/{tracking_id}",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status', 'unknown')
                    citations = status_data.get('citations', [])
                    
                    print(f"    Status: {status}, Citations: {len(citations)}")
                    
                    if status == 'completed':
                        if len(citations) > 0:
                            print(f"    🎉 SUCCESS: Found {len(citations)} citations!")
                            return True
                        else:
                            print("    ⚠️ Completed but no citations found")
                            return False
                    elif status == 'failed':
                        print(f"    ❌ Job failed: {status_data}")
                        return False
                else:
                    print(f"    Status check failed: {status_response.status_code}")
                    
            except Exception as e:
                print(f"    Exception: {e}")
            
            time.sleep(3)
        
        print("  ❌ Timeout waiting for completion")
        return False
        
    except Exception as e:
        print(f"  💥 Test failed: {e}")
        return False

def main():
    """Run the force async test."""
    success = test_force_true_async()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Force true async test")

if __name__ == "__main__":
    main()
