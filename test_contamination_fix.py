#!/usr/bin/env python3
"""
Test script to verify that data contamination is fixed.
This tests the specific issue where extracted data was being used as canonical data.
"""

import requests
import json
import time

def test_contamination_fix():
    """Test that unverified citations don't get contaminated canonical data"""
    
    print("🧪 TESTING DATA CONTAMINATION FIX")
    print("=" * 50)
    
    # Test text with a citation that should NOT be verified
    # This will test if extracted data stays separate from canonical data
    test_text = """
    This document discusses the case of Fake Test Case v. Example Corporation, 2023.
    The citation 999 F.3d 123 is mentioned in the text.
    Another reference to 888 F.2d 456 appears here.
    """
    
    # Submit for processing
    print("📤 Submitting text for processing...")
    response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                            json={'text': test_text, 'enable_verification': True})
    
    if response.status_code != 200:
        print(f"❌ Error submitting text: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    task_id = result.get('task_id')
    
    if not task_id:
        print("❌ No task_id returned")
        return
    
    print(f"🔄 Task ID: {task_id}")
    
    # Poll for completion
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(f'http://localhost:5000/casestrainer/api/task_status/{task_id}')
        
        if response.status_code != 200:
            print(f"❌ Error checking status: {response.status_code}")
            return
        
        status_data = response.json()
        status = status_data.get('status')
        
        print(f"   Check {attempt + 1}: Status = {status}")
        
        if status == 'completed':
            break
        elif status == 'failed':
            print("❌ Task failed")
            print(status_data)
            return
        
        time.sleep(2)
    else:
        print("❌ Task timed out")
        return
    
    # Check results for contamination
    print("✅ COMPLETED! Checking for data contamination...")
    
    citations = status_data.get('citations', [])
    print(f"📊 Found {len(citations)} citations")
    
    contamination_found = False
    
    for i, citation in enumerate(citations):
        print(f"\n📋 Citation {i + 1}: {citation.get('citation', 'Unknown')}")
        
        verified = citation.get('verified', False)
        canonical_name = citation.get('canonical_name')
        canonical_date = citation.get('canonical_date')
        extracted_case_name = citation.get('extracted_case_name')
        extracted_date = citation.get('extracted_date')
        verification_source = citation.get('source', 'Unknown')
        
        print(f"   Verified: {verified}")
        print(f"   Canonical Name: {canonical_name}")
        print(f"   Canonical Date: {canonical_date}")
        print(f"   Extracted Name: {extracted_case_name}")
        print(f"   Extracted Date: {extracted_date}")
        print(f"   Source: {verification_source}")
        
        # Check for contamination
        if not verified and canonical_name is not None:
            print(f"   🚨 CONTAMINATION: Unverified citation has canonical_name!")
            contamination_found = True
            
        if not verified and canonical_date is not None:
            print(f"   🚨 CONTAMINATION: Unverified citation has canonical_date!")
            contamination_found = True
            
        if verification_source == 'extracted' or verification_source == 'N/A':
            if canonical_name is not None or canonical_date is not None:
                print(f"   🚨 CONTAMINATION: Extracted source has canonical data!")
                contamination_found = True
    
    print("\n" + "=" * 50)
    if contamination_found:
        print("❌ DATA CONTAMINATION DETECTED!")
        print("   Unverified citations have canonical data from extracted sources")
    else:
        print("✅ NO CONTAMINATION FOUND!")
        print("   Data separation between extracted and canonical is working correctly")
    
    return not contamination_found

if __name__ == "__main__":
    success = test_contamination_fix()
    exit(0 if success else 1)
