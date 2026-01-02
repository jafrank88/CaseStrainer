#!/usr/bin/env python3
"""
Test D2 59366-1-II PDF with correct task tracking endpoint
"""

import requests
import json
import time

def test_pdf_with_correct_endpoint():
    """Test PDF with correct task status endpoint"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 Testing D2 59366-1-II PDF with correct task tracking...")
    print(f"PDF URL: {pdf_url}")
    
    try:
        # Submit the PDF for processing
        api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        data = {
            "type": "url",
            "url": pdf_url,
            "extract_case_names": True
        }
        
        print("📤 Submitting PDF for analysis...")
        response = requests.post(api_url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Initial Response:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            
            if result.get('metadata', {}).get('processing_mode') == 'queued':
                task_id = result.get('task_id')
                print(f"✅ Task queued successfully!")
                print(f"Task ID: {task_id}")
                
                # Poll for results using CORRECT endpoint
                print(f"\n⏳ Polling for results using correct endpoint...")
                max_attempts = 30  # 5 minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    attempt += 1
                    print(f"Attempt {attempt}/{max_attempts}...")
                    
                    try:
                        # CORRECT ENDPOINT: /task_status/ instead of /task/
                        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                        status_response = requests.get(status_url, timeout=30)
                        
                        print(f"Status check: {status_response.status_code}")
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            
                            print(f"Status: {status}")
                            
                            if status == 'completed':
                                print(f"✅ Processing completed!")
                                
                                # Get the results
                                result = status_result.get('result', {})
                                citations = result.get('citations', [])
                                clusters = result.get('clusters', [])
                                
                                print(f"\n📋 Final Results:")
                                print(f"Citations found: {len(citations)}")
                                print(f"Clusters found: {len(clusters)}")
                                
                                if citations:
                                    print(f"\n📋 Citation Analysis (First 10):")
                                    print("=" * 100)
                                    
                                    extraction_success = 0
                                    verification_success = 0
                                    
                                    for i, citation in enumerate(citations[:10]):
                                        print(f"\n--- Citation {i+1} ---")
                                        print(f"Citation: {citation.get('citation', 'N/A')}")
                                        
                                        # Extracted data
                                        extracted_name = citation.get('extracted_case_name', 'N/A')
                                        extracted_date = citation.get('extracted_date', 'N/A')
                                        print(f"📝 Extracted name: '{extracted_name}'")
                                        print(f"📅 Extracted date: '{extracted_date}'")
                                        
                                        # Verified data
                                        canonical_name = citation.get('canonical_name', 'N/A')
                                        canonical_date = citation.get('canonical_date', 'N/A')
                                        print(f"✅ Canonical name: '{canonical_name}'")
                                        print(f"✅ Canonical date: '{canonical_date}'")
                                        
                                        # Verification status
                                        verified = citation.get('verified', False)
                                        verification_source = citation.get('verification_source', 'N/A')
                                        print(f"🔍 Verified: {verified}")
                                        print(f"🔍 Verification source: {verification_source}")
                                        
                                        # Mismatch detection
                                        name_mismatch = citation.get('name_mismatch', False)
                                        date_mismatch = citation.get('date_mismatch', False)
                                        print(f"⚠️ Name mismatch: {name_mismatch}")
                                        print(f"⚠️ Date mismatch: {date_mismatch}")
                                        
                                        # Count successes
                                        if extracted_name != 'N/A' and extracted_name.strip():
                                            extraction_success += 1
                                        
                                        if verified:
                                            verification_success += 1
                                    
                                    # Summary
                                    print(f"\n🎯 D2 59366-1-II EXTRACTION TEST SUMMARY:")
                                    print("=" * 100)
                                    print(f"✅ Total citations processed: {len(citations)}")
                                    print(f"✅ Successful extractions: {extraction_success}/{len(citations)} ({extraction_success/len(citations)*100:.1f}%)")
                                    print(f"✅ Successful verifications: {verification_success}/{len(citations)} ({verification_success/len(citations)*100:.1f}%)")
                                    print(f"✅ Total clusters formed: {len(clusters)}")
                                    
                                    if extraction_success == len(citations) and verification_success == len(citations):
                                        print(f"\n🎉 PERFECT: All case names extracted and verified correctly!")
                                    elif extraction_success == len(citations):
                                        print(f"\n✅ GOOD: All case names extracted, verification working ({verification_success}/{len(citations)})")
                                    else:
                                        print(f"\n⚠️ NEEDS IMPROVEMENT: {len(citations) - extraction_success} extraction issues found")
                                    
                                    # Save results
                                    output_file = r"d:\dev\casestrainer\D2_59366_corrected_results.json"
                                    try:
                                        with open(output_file, 'w', encoding='utf-8') as f:
                                            json.dump(result, f, indent=2, ensure_ascii=False)
                                        print(f"\n💾 Results saved to: {output_file}")
                                    except Exception as e:
                                        print(f"\n❌ Failed to save results: {e}")
                                
                                break
                            
                            elif status == 'failed':
                                error_msg = status_result.get('error', 'Unknown error')
                                print(f"❌ Processing failed: {error_msg}")
                                break
                            
                            elif status == 'processing':
                                progress = status_result.get('progress', {})
                                if progress:
                                    current_step = progress.get('current_step', 'Unknown')
                                    print(f"   Current step: {current_step}")
                        
                        else:
                            print(f"❌ Status check failed: {status_response.status_code}")
                            print(f"Response: {status_response.text}")
                        
                        time.sleep(10)  # Wait 10 seconds between polls
                        
                    except Exception as e:
                        print(f"❌ Error checking status: {e}")
                        time.sleep(10)
                
                if attempt >= max_attempts:
                    print(f"❌ Timeout: Processing did not complete within {max_attempts * 10} seconds")
            
            else:
                print(f"❌ Unexpected processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
        
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_with_correct_endpoint()
