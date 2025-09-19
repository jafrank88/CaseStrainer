#!/usr/bin/env python3
"""
Debug the exact API response flow to understand why sync fallback results aren't returned.
"""

import requests
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_api_response_flow():
    """Debug the API response flow step by step."""
    
    # Create a large document that should trigger sync fallback
    test_text = """
    Legal Document for API Testing
    
    Important cases that should be found:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
    3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
    """ + "\n\nAdditional content to make it large. " * 1000  # ~20KB
    
    print("🔍 Debugging API Response Flow")
    print("=" * 60)
    print(f"📄 Document size: {len(test_text)} characters ({len(test_text)/1024:.1f} KB)")
    print("📝 Expected: Should trigger async processing, fail to Redis, fallback to sync")
    print()
    
    try:
        print("📤 Step 1: Submitting request to API...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n🔍 Step 2: Analyzing API Response Structure...")
            print(f"  Response keys: {list(data.keys())}")
            print(f"  Success: {data.get('success')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Has task_id: {'task_id' in data}")
            print(f"  Has citations: {'citations' in data}")
            print(f"  Citations count: {len(data.get('citations', []))}")
            print(f"  Has clusters: {'clusters' in data}")
            print(f"  Clusters count: {len(data.get('clusters', []))}")
            print(f"  Has metadata: {'metadata' in data}")
            
            if 'metadata' in data:
                metadata = data['metadata']
                print(f"  Processing mode: {metadata.get('processing_mode', 'N/A')}")
                print(f"  Source: {metadata.get('source', 'N/A')}")
                print(f"  Fallback reason: {metadata.get('fallback_reason', 'N/A')}")
                print(f"  Error details: {metadata.get('error_details', 'N/A')}")
            
            print(f"  Has progress_data: {'progress_data' in data}")
            
            if 'progress_data' in data:
                progress = data['progress_data']
                print(f"  Progress status: {progress.get('status', 'N/A')}")
                print(f"  Progress message: {progress.get('current_message', 'N/A')}")
            
            print("\n🔍 Step 3: Detailed Analysis...")
            
            # Check if we got sync fallback results
            processing_mode = data.get('metadata', {}).get('processing_mode', '')
            if processing_mode == 'sync_fallback':
                print("✅ Sync fallback detected in response!")
                citations = data.get('citations', [])
                if len(citations) > 0:
                    print(f"✅ Sync fallback returned {len(citations)} citations")
                    print("📋 Sample citations:")
                    for i, citation in enumerate(citations[:3]):
                        citation_text = citation.get('citation', 'N/A')
                        case_name = citation.get('extracted_case_name', 'N/A')
                        print(f"  {i+1}. {citation_text} - {case_name}")
                    return True
                else:
                    print("❌ Sync fallback detected but no citations returned")
                    return False
            elif processing_mode == 'queued':
                print("⚠️ Response shows 'queued' mode - async processing attempted")
                if 'task_id' in data:
                    print(f"  Task ID: {data['task_id']}")
                    print("  This suggests async processing succeeded")
                else:
                    print("  No task_id - this suggests async failed but API didn't handle fallback")
                return False
            elif processing_mode == 'immediate':
                print("✅ Immediate processing detected")
                citations = data.get('citations', [])
                print(f"  Citations: {len(citations)}")
                return len(citations) > 0
            else:
                print(f"❌ Unexpected processing mode: '{processing_mode}'")
                return False
                
        else:
            print(f"❌ API request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_direct_processing():
    """Compare API result with direct processing to identify the gap."""
    
    print("\n" + "=" * 60)
    print("🔄 COMPARISON WITH DIRECT PROCESSING")
    print("=" * 60)
    
    try:
        from src.unified_input_processor import process_text_input
        import uuid
        
        # Same test text
        test_text = """
        Legal Document for Direct Testing
        
        Important cases:
        1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007)
        2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010)
        3. Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014)
        """ + "\n\nAdditional content. " * 1000
        
        print("🔧 Direct processing result:")
        request_id = str(uuid.uuid4())
        direct_result = process_text_input(test_text, request_id)
        
        print(f"  Success: {direct_result.get('success')}")
        print(f"  Citations: {len(direct_result.get('citations', []))}")
        print(f"  Processing mode: {direct_result.get('metadata', {}).get('processing_mode')}")
        
        if len(direct_result.get('citations', [])) > 0:
            print("✅ Direct processing finds citations correctly")
            return True
        else:
            print("❌ Direct processing also fails")
            return False
            
    except Exception as e:
        print(f"💥 Direct processing test failed: {e}")
        return False

def main():
    """Run the API response flow debug."""
    print("🧪 API Response Flow Debug")
    print("=" * 60)
    
    api_success = debug_api_response_flow()
    direct_success = compare_with_direct_processing()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if direct_success and not api_success:
        print("❌ ISSUE CONFIRMED: Direct processing works, API doesn't return results correctly")
        print("🔍 Problem is in API response handling layer")
    elif not direct_success and not api_success:
        print("❌ ISSUE: Both direct and API processing fail")
        print("🔍 Problem is in the core processing logic")
    elif api_success and direct_success:
        print("✅ SUCCESS: Both API and direct processing work correctly")
    else:
        print("⚠️ UNEXPECTED: API works but direct processing doesn't")
    
    return api_success

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: API response flow debug")
