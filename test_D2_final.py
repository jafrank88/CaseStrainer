#!/usr/bin/env python3
"""
Test D2 59366-1-II PDF with immediate analysis
"""

import requests
import json
import time

def test_pdf_immediate():
    """Test PDF with immediate analysis"""
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 Testing D2 59366-1-II PDF extraction...")
    print(f"PDF URL: {pdf_url}")
    
    try:
        # Try URL input first
        data = {
            "type": "url",
            "url": pdf_url,
            "extract_case_names": True
        }
        
        print("📤 Sending URL for analysis...")
        response = requests.post(url, json=data, timeout=180)  # 3 minutes
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Response Analysis:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            
            # Handle async response
            if result.get('metadata', {}).get('processing_mode') == 'queued':
                task_id = result.get('task_id')
                print(f"Task queued for async processing")
                print(f"Task ID: {task_id}")
                
                # Poll for results with shorter timeout
                max_attempts = 20  # 3+ minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    attempt += 1
                    print(f"Polling attempt {attempt}/{max_attempts}...")
                    
                    try:
                        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task/{task_id}"
                        status_response = requests.get(status_url, timeout=30)
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            
                            print(f"Status: {status}")
                            
                            if status == 'completed':
                                print(f"✅ Processing completed!")
                                result = status_result.get('result', {})
                                break
                            elif status == 'failed':
                                error_msg = status_result.get('error', 'Unknown error')
                                print(f"❌ Processing failed: {error_msg}")
                                return
                            elif status == 'processing':
                                progress = status_result.get('progress', {})
                                if progress:
                                    current_step = progress.get('current_step', 'Unknown')
                                    print(f"   Current step: {current_step}")
                        
                        time.sleep(10)  # Wait 10 seconds between polls
                        
                    except requests.exceptions.RequestException as e:
                        print(f"⚠️ Status check error: {e}")
                        time.sleep(10)
                
                if attempt >= max_attempts:
                    print(f"❌ Timeout: Processing did not complete within expected time")
                    return
            
            # Analyze the results
            analyze_results(result)
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_results(result):
    """Analyze the extraction results"""
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📋 DETAILED ANALYSIS:")
    print("=" * 100)
    print(f"Total citations found: {len(citations)}")
    print(f"Total clusters formed: {len(clusters)}")
    
    if citations:
        print(f"\n📋 Citation Analysis (First 15):")
        print("=" * 100)
        
        extraction_issues = []
        verification_issues = []
        mismatch_issues = []
        data_quality_issues = []
        
        for i, citation in enumerate(citations[:15]):  # Show first 15
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
            
            # Check for issues
            if extracted_name == 'N/A' or not extracted_name.strip():
                extraction_issues.append(f"Citation {i+1}: Missing extracted case name")
            
            if extracted_date == 'N/A' or not extracted_date.strip():
                extraction_issues.append(f"Citation {i+1}: Missing extracted date")
            
            if canonical_name == 'N/A' and verified:
                verification_issues.append(f"Citation {i+1}: Verified but missing canonical name")
            
            if canonical_date == 'N/A' and verified:
                verification_issues.append(f"Citation {i+1}: Verified but missing canonical date")
            
            # Check data quality
            if extracted_name and len(extracted_name) < 10:
                data_quality_issues.append(f"Citation {i+1}: Extracted name seems too short: '{extracted_name}'")
            
            if extracted_name and 'v.' not in extracted_name.lower() and ' v ' not in extracted_name:
                data_quality_issues.append(f"Citation {i+1}: Extracted name missing 'v.': '{extracted_name}'")
        
        # Analyze clusters
        if clusters:
            print(f"\n📚 Cluster Analysis (First 5):")
            print("=" * 100)
            
            for i, cluster in enumerate(clusters[:5]):  # Show first 5
                print(f"\n--- Cluster {i+1} ---")
                print(f"Cluster ID: {cluster.get('cluster_id', 'N/A')}")
                print(f"Submitted display name: '{cluster.get('submitted_display_name', 'N/A')}'")
                print(f"Submitted display date: '{cluster.get('submitted_display_date', 'N/A')}'")
                print(f"Verifying display name: '{cluster.get('verifying_display_name', 'N/A')}'")
                print(f"Verifying display date: '{cluster.get('verifying_display_date', 'N/A')}'")
                print(f"Verification source: '{cluster.get('verification_source', 'N/A')}'")
                print(f"Has name mismatch: {cluster.get('has_name_mismatch', False)}")
                print(f"Has date mismatch: {cluster.get('has_date_mismatch', False)}")
                print(f"Citations in cluster: {len(cluster.get('citations', []))}")
        
        # Summary
        print(f"\n🎯 COMPREHENSIVE TEST SUMMARY:")
        print("=" * 100)
        print(f"✅ Total citations processed: {len(citations)}")
        print(f"✅ Total clusters formed: {len(clusters)}")
        
        # Count verification status
        verified_count = sum(1 for c in citations if c.get('verified', False))
        print(f"✅ Verified citations: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
        
        if extraction_issues:
            print(f"\n⚠️ Extraction Issues ({len(extraction_issues)}):")
            for issue in extraction_issues[:5]:
                print(f"  - {issue}")
            if len(extraction_issues) > 5:
                print(f"  ... and {len(extraction_issues) - 5} more")
        else:
            print(f"\n✅ No extraction issues found")
        
        if verification_issues:
            print(f"\n⚠️ Verification Issues ({len(verification_issues)}):")
            for issue in verification_issues[:5]:
                print(f"  - {issue}")
            if len(verification_issues) > 5:
                print(f"  ... and {len(verification_issues) - 5} more")
        else:
            print(f"✅ No verification issues found")
        
        if data_quality_issues:
            print(f"\n⚠️ Data Quality Issues ({len(data_quality_issues)}):")
            for issue in data_quality_issues[:5]:
                print(f"  - {issue}")
            if len(data_quality_issues) > 5:
                print(f"  ... and {len(data_quality_issues) - 5} more")
        else:
            print(f"✅ No data quality issues found")
        
        # Overall assessment
        total_issues = len(extraction_issues) + len(verification_issues) + len(data_quality_issues)
        if total_issues == 0:
            print(f"\n🎉 PERFECT: All case names, dates, and mismatches processed correctly!")
        else:
            print(f"\n⚠️ {total_issues} issue(s) found that need attention")
        
        # Save results
        output_file = r"d:\dev\casestrainer\D2_59366_final_results.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Full results saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")
    
    else:
        print(f"\n❌ No citations found in the document")

if __name__ == "__main__":
    test_pdf_immediate()
