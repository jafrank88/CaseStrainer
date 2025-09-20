#!/usr/bin/env python3
"""
Test async result polling to see if the fix is working.
"""

import requests
import time
import json

def test_async_with_polling():
    """Test async processing with proper result polling."""
    
    # Medium document that should trigger async
    base_text = """
    Legal Document for Async Testing
    
    Important cases:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Landmark case
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Important ruling
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014) - Recent decision
    """
    
    # Make it large enough to trigger async
    large_text = base_text + "\n\nLegal content padding. " * 500
    
    print("🔄 Testing Async Processing with Result Polling")
    print("=" * 60)
    print(f"Document size: {len(large_text)} characters ({len(large_text)/1024:.1f} KB)")
    print()
    
    # Step 1: Submit for processing
    print("📤 Step 1: Submitting for async processing...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": large_text},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Submission failed: {response.status_code}")
            return False
            
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        task_id = data.get('task_id')
        job_id = data.get('metadata', {}).get('job_id')
        immediate_citations = data.get('citations', [])
        
        print(f"  Processing mode: {processing_mode}")
        print(f"  Task ID: {task_id}")
        print(f"  Job ID: {job_id}")
        print(f"  Immediate citations: {len(immediate_citations)}")
        
        # Check if it's sync fallback (immediate results)
        if processing_mode == 'sync_fallback':
            print("  ✅ Sync fallback - checking results...")
            
            citations_with_names = []
            for citation in immediate_citations:
                extracted_name = citation.get('extracted_case_name', '')
                if extracted_name and extracted_name != 'N/A':
                    citations_with_names.append(citation)
                    print(f"    Citation: {citation.get('citation', 'N/A')}")
                    print(f"    Name: '{extracted_name}'")
                    print(f"    Date: '{citation.get('extracted_date', 'N/A')}'")
            
            print(f"  Citations with names: {len(citations_with_names)}/{len(immediate_citations)}")
            return len(citations_with_names) > 0
        
        # If not sync fallback, poll for async results
        if not (task_id or job_id):
            print("  ❌ No task ID or job ID for async processing")
            return False
        
        tracking_id = task_id or job_id
        print(f"  ✅ Async processing started, tracking ID: {tracking_id}")
        
        # Step 2: Poll for completion
        print("\n⏳ Step 2: Polling for completion...")
        for attempt in range(15):
            print(f"  Attempt {attempt + 1}/15")
            
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
                        print(f"    ✅ Job completed!")
                        
                        # Check for extracted names
                        citations_with_names = []
                        for citation in citations:
                            extracted_name = citation.get('extracted_case_name', '')
                            if extracted_name and extracted_name != 'N/A':
                                citations_with_names.append(citation)
                                print(f"      Citation: {citation.get('citation', 'N/A')}")
                                print(f"      Name: '{extracted_name}'")
                                print(f"      Date: '{citation.get('extracted_date', 'N/A')}'")
                        
                        print(f"    Citations with names: {len(citations_with_names)}/{len(citations)}")
                        return len(citations_with_names) > 0
                    
                    elif status == 'failed':
                        print(f"    ❌ Job failed: {status_data}")
                        return False
                    
                    elif status == 'processing':
                        print(f"    🔄 Still processing...")
                else:
                    print(f"    Status check failed: {status_response.status_code}")
                    
            except Exception as e:
                print(f"    Exception: {e}")
            
            time.sleep(2)
        
        print("  ❌ Timeout waiting for completion")
        return False
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return False

def main():
    """Run async result polling test."""
    success = test_async_with_polling()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Async result polling test")
    
    if success:
        print("✅ Name extraction is working correctly in async processing")
    else:
        print("❌ Name extraction is not working in async processing")

if __name__ == "__main__":
    main()
