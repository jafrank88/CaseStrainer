#!/usr/bin/env python3
"""
Comprehensive test of both sync and async verification pathways
"""

import requests
import json
import time

def test_sync_verification():
    """Test sync verification pathway"""
    print("🔧 TESTING SYNC VERIFICATION PATHWAY")
    print("=" * 50)
    
    # Test with a known verifiable citation
    test_text = "The Supreme Court decision in 521 U.S. 811 established important precedent."
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"📋 Sync Results:")
            print(f"   Citations found: {len(citations)}")
            
            for i, citation in enumerate(citations):
                print(f"   Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"     Verified: {citation.get('verified', 'N/A')}")
                print(f"     Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"     Canonical Date: {citation.get('canonical_date', 'N/A')}")
                
                # Check verification paradox
                has_canonical = bool(
                    citation.get('canonical_name') and 
                    citation.get('canonical_date') and 
                    citation.get('canonical_url')
                )
                verified = citation.get('verified', False)
                
                if has_canonical and not verified:
                    print(f"     ⚠️  VERIFICATION PARADOX!")
                elif verified and has_canonical:
                    print(f"     ✅ VERIFICATION WORKING!")
                    return True
                else:
                    print(f"     ❌ VERIFICATION FAILED")
            
            return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_async_verification():
    """Test async verification pathway"""
    print("\n🔄 TESTING ASYNC VERIFICATION PATHWAY")
    print("=" * 50)
    
    # Test with the same citation but longer text to trigger async
    test_text = "The Supreme Court decision in 521 U.S. 811 established important precedent. " * 100  # Make it longer to trigger async
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📊 Initial Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"🔄 Async processing started - Task ID: {task_id}")
                
                # Poll for results
                max_attempts = 60
                for attempt in range(max_attempts):
                    try:
                        poll_response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
                        
                        if poll_response.status_code == 200:
                            poll_result = poll_response.json()
                            status = poll_result.get('status', 'unknown')
                            
                            if attempt % 10 == 0:
                                print(f"   Check {attempt+1}: Status = {status}")
                            
                            if status == 'completed':
                                citations = poll_result.get('citations', [])
                                print(f"   ✅ ASYNC COMPLETED! Found {len(citations)} citations")
                                
                                # Check verification status
                                verified_count = 0
                                canonical_count = 0
                                paradox_count = 0
                                
                                for citation in citations:
                                    has_canonical = bool(
                                        citation.get('canonical_name') and 
                                        citation.get('canonical_date') and 
                                        citation.get('canonical_url')
                                    )
                                    verified = citation.get('verified', False)
                                    
                                    if has_canonical and not verified:
                                        paradox_count += 1
                                    elif verified and has_canonical:
                                        verified_count += 1
                                        canonical_count += 1
                                    elif verified:
                                        verified_count += 1
                                    elif has_canonical:
                                        canonical_count += 1
                                
                                print(f"\n   📈 ASYNC VERIFICATION SUMMARY:")
                                print(f"   Total citations: {len(citations)}")
                                print(f"   Verified with canonical data: {verified_count}")
                                print(f"   Citations with canonical data: {canonical_count}")
                                print(f"   Verification paradox cases: {paradox_count}")
                                
                                if paradox_count == 0 and verified_count > 0:
                                    print(f"   ✅ ASYNC VERIFICATION WORKING!")
                                    return True
                                elif paradox_count > 0:
                                    print(f"   ⚠️  ASYNC VERIFICATION PARADOX: {paradox_count} cases")
                                    return False
                                else:
                                    print(f"   ❌ ASYNC VERIFICATION FAILED - No verified citations")
                                    return False
                                    
                            elif status == 'failed':
                                print(f"   ❌ ASYNC FAILED: {poll_result.get('error', 'Unknown error')}")
                                return False
                        
                        elif poll_response.status_code == 404:
                            if attempt % 10 == 0:
                                print(f"   Check {attempt+1}: Task not found yet")
                    
                    except Exception as e:
                        print(f"   Check {attempt+1}: Error - {e}")
                    
                    time.sleep(2)  # Wait 2 seconds between checks
                
                print(f"   ⏰ ASYNC TIMEOUT after {max_attempts * 2} seconds")
                return False
            else:
                # Sync response (unexpected for long text)
                citations = result.get('result', {}).get('citations', [])
                print(f"📋 Unexpected sync response - Found {len(citations)} citations")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_pdf_async_verification():
    """Test async verification with PDF file"""
    print("\n📄 TESTING PDF ASYNC VERIFICATION PATHWAY")
    print("=" * 50)
    
    pdf_path = r"d:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            data = {
                'type': 'file',
                'extract_citations': 'true'
            }
            
            print("📤 Uploading PDF for async processing...")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'task_id' in result:
                    task_id = result['task_id']
                    print(f"🔄 PDF async processing started - Task ID: {task_id}")
                    
                    # Poll for results
                    max_attempts = 90
                    for attempt in range(max_attempts):
                        try:
                            poll_response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
                            
                            if poll_response.status_code == 200:
                                poll_result = poll_response.json()
                                status = poll_result.get('status', 'unknown')
                                
                                if attempt % 15 == 0:
                                    print(f"   Check {attempt+1}: Status = {status}")
                                
                                if status == 'completed':
                                    citations = poll_result.get('citations', [])
                                    print(f"   ✅ PDF ASYNC COMPLETED! Found {len(citations)} citations")
                                    
                                    # Check verification status
                                    verified_count = 0
                                    canonical_count = 0
                                    paradox_count = 0
                                    
                                    # Check first 10 citations for detailed analysis
                                    print(f"\n   📋 First 10 PDF citations verification status:")
                                    for i, citation in enumerate(citations[:10]):
                                        citation_text = citation.get('citation', 'N/A')
                                        verified = citation.get('verified', False)
                                        canonical_name = citation.get('canonical_name', 'N/A')
                                        
                                        has_canonical = bool(
                                            citation.get('canonical_name') and 
                                            citation.get('canonical_date') and 
                                            citation.get('canonical_url')
                                        )
                                        
                                        status_icon = "✅" if verified and has_canonical else "⚠️" if has_canonical else "❌"
                                        print(f"     {i+1}. {status_icon} {citation_text} - Verified: {verified}, Canonical: {canonical_name}")
                                        
                                        if has_canonical and not verified:
                                            paradox_count += 1
                                        elif verified and has_canonical:
                                            verified_count += 1
                                            canonical_count += 1
                                        elif has_canonical:
                                            canonical_count += 1
                                    
                                    print(f"\n   📈 PDF ASYNC VERIFICATION SUMMARY:")
                                    print(f"   Total citations: {len(citations)}")
                                    print(f"   Verified with canonical data: {verified_count}")
                                    print(f"   Citations with canonical data: {canonical_count}")
                                    print(f"   Verification paradox cases: {paradox_count}")
                                    
                                    if paradox_count == 0 and verified_count > 0:
                                        print(f"   ✅ PDF ASYNC VERIFICATION WORKING!")
                                        return True
                                    elif paradox_count > 0:
                                        print(f"   ⚠️  PDF ASYNC VERIFICATION PARADOX: {paradox_count} cases")
                                        return False
                                    else:
                                        print(f"   ❌ PDF ASYNC VERIFICATION FAILED - No verified citations")
                                        return False
                                        
                                elif status == 'failed':
                                    print(f"   ❌ PDF ASYNC FAILED: {poll_result.get('error', 'Unknown error')}")
                                    return False
                            
                            elif poll_response.status_code == 404:
                                if attempt % 15 == 0:
                                    print(f"   Check {attempt+1}: Task not found yet")
                        
                        except Exception as e:
                            print(f"   Check {attempt+1}: Error - {e}")
                        
                        time.sleep(2)  # Wait 2 seconds between checks
                    
                    print(f"   ⏰ PDF ASYNC TIMEOUT after {max_attempts * 2} seconds")
                    return False
                else:
                    print(f"❌ Unexpected response format")
                    return False
            else:
                print(f"❌ PDF upload failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ PDF Exception: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("🚀 COMPREHENSIVE SYNC/ASYNC VERIFICATION TEST")
    print("=" * 60)
    
    # Test all three pathways
    sync_result = test_sync_verification()
    async_result = test_async_verification()
    pdf_result = test_pdf_async_verification()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 60)
    print(f"Sync Verification:     {'✅ PASS' if sync_result else '❌ FAIL'}")
    print(f"Async Verification:    {'✅ PASS' if async_result else '❌ FAIL'}")
    print(f"PDF Async Verification: {'✅ PASS' if pdf_result else '❌ FAIL'}")
    
    if sync_result and async_result and pdf_result:
        print("\n🎉 ALL TESTS PASSED - Verification system working correctly!")
    elif sync_result and not async_result:
        print("\n⚠️  PARTIAL SUCCESS - Sync works but async needs fixing")
    elif not sync_result and async_result:
        print("\n⚠️  PARTIAL SUCCESS - Async works but sync needs fixing")
    else:
        print("\n❌ ALL TESTS FAILED - Verification system needs major fixes")

if __name__ == "__main__":
    main()
