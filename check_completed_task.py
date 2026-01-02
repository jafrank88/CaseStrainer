#!/usr/bin/env python3
"""
Check the status of the completed async task
"""

import requests
import json

def check_task_status():
    """Check the status of the completed task"""
    
    task_id = "f1431e81-06cd-461e-a772-04ea3a6b9ed8"
    
    print(f"🔍 Checking task status for: {task_id}")
    
    try:
        response = requests.get(f"http://localhost:5000/casestrainer/api/task/{task_id}")
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Task Status: {result.get('status', 'unknown')}")
            print(f"📋 Result keys: {list(result.keys())}")
            
            if 'result' in result:
                citations = result['result'].get('citations', [])
                print(f"📋 Citations found: {len(citations)}")
                
                if citations:
                    print(f"\n📋 First 5 citations:")
                    for i, citation in enumerate(citations[:5]):
                        print(f"  Citation {i+1}: {citation.get('citation', 'N/A')}")
                        print(f"    Verified: {citation.get('verified', 'N/A')}")
                        print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
                        print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
                        
                        # Check verification paradox
                        has_canonical = bool(
                            citation.get('canonical_name') and 
                            citation.get('canonical_date') and 
                            citation.get('canonical_url')
                        )
                        verified = citation.get('verified', False)
                        
                        if has_canonical and not verified:
                            print(f"    ⚠️  VERIFICATION PARADOX!")
                        elif verified and has_canonical:
                            print(f"    ✅ VERIFICATION WORKING!")
                        print()
                
                # Check metadata
                metadata = result['result'].get('metadata', {})
                print(f"📋 Processing Metadata:")
                print(f"   Processing mode: {metadata.get('processing_mode', 'N/A')}")
                print(f"   Verification count: {metadata.get('verification_count', 'N/A')}")
                print(f"   Stages completed: {metadata.get('stages_completed', 'N/A')}")
                print(f"   Status: {metadata.get('status', 'N/A')}")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    check_task_status()
