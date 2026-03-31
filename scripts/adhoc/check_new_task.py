#!/usr/bin/env python3
"""
Check the status of the newly completed async task
"""

import requests
import json

def check_task_status():
    """Check the status of the completed task"""
    
    task_id = "05820a53-aebf-4bff-b180-62ba21edc155"
    
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
                    print(f"\n📋 First 10 citations:")
                    verified_count = 0
                    canonical_count = 0
                    paradox_count = 0
                    
                    for i, citation in enumerate(citations[:10]):
                        print(f"\n  Citation {i+1}: {citation.get('citation', 'N/A')}")
                        print(f"    Verified: {citation.get('verified', 'N/A')}")
                        print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
                        print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
                        print(f"    Canonical URL: {citation.get('canonical_url', 'N/A')}")
                        
                        # Check verification paradox
                        has_canonical = bool(
                            citation.get('canonical_name') and 
                            citation.get('canonical_date') and 
                            citation.get('canonical_url')
                        )
                        verified = citation.get('verified', False)
                        
                        if has_canonical and not verified:
                            print(f"    ⚠️  VERIFICATION PARADOX!")
                            paradox_count += 1
                        elif verified and has_canonical:
                            print(f"    ✅ VERIFICATION WORKING!")
                            verified_count += 1
                            canonical_count += 1
                        elif verified:
                            verified_count += 1
                        elif has_canonical:
                            canonical_count += 1
                    
                    # Check all citations for summary
                    total_paradox = 0
                    total_verified = 0
                    total_canonical = 0
                    
                    for citation in citations:
                        has_canonical = bool(
                            citation.get('canonical_name') and 
                            citation.get('canonical_date') and 
                            citation.get('canonical_url')
                        )
                        verified = citation.get('verified', False)
                        
                        if has_canonical and not verified:
                            total_paradox += 1
                        if verified:
                            total_verified += 1
                        if has_canonical:
                            total_canonical += 1
                    
                    print(f"\n📈 SUMMARY:")
                    print(f"   Total citations: {len(citations)}")
                    print(f"   Verified citations: {total_verified}")
                    print(f"   Citations with canonical data: {total_canonical}")
                    print(f"   Citations with verification paradox: {total_paradox}")
                    
                    if total_paradox == 0 and total_canonical > 0:
                        print(f"   ✅ VERIFICATION PARADOX FIXED!")
                    elif total_paradox > 0:
                        print(f"   ⚠️  VERIFICATION PARADOX STILL EXISTS: {total_paradox} citations")
                    else:
                        print(f"   ℹ️  No citations with canonical data found")
                
                # Check metadata
                metadata = result['result'].get('metadata', {})
                print(f"\n📋 PROCESSING METADATA:")
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
