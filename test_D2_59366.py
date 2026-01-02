#!/usr/bin/env python3
"""
Test case name and date extraction for the specific D2 59366-1-II PDF
"""

import requests
import json
import os
import time
from urllib.parse import quote

def test_pdf_from_url():
    """Test PDF extraction from the provided URL"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print(f"🔍 Testing PDF from URL:")
    print(f"URL: {pdf_url}")
    
    # Test via URL input to the API
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    try:
        print(f"📤 Sending URL to API for analysis...")
        
        # Send URL for processing
        data = {
            'type': 'url',
            'url': pdf_url,
            'extract_case_names': True
        }
        
        response = requests.post(api_url, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Initial API Response:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            
            # Check if this is async processing
            if result.get('metadata', {}).get('processing_mode') == 'queued':
                task_id = result.get('task_id')
                print(f"Task queued for async processing")
                print(f"Task ID: {task_id}")
                
                # Poll for results
                print(f"\n⏳ Polling for results...")
                max_attempts = 60  # 10 minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    attempt += 1
                    print(f"Attempt {attempt}/{max_attempts}...")
                    
                    # Check task status
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
                                step_detail = progress.get('step_detail', '')
                                print(f"   Current step: {current_step}")
                                if step_detail:
                                    print(f"   Detail: {step_detail}")
                        
                        time.sleep(10)  # Wait 10 seconds between polls
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        print(f"Response: {status_response.text}")
                        time.sleep(10)
                
                if attempt >= max_attempts:
                    print(f"❌ Timeout: Processing did not complete within 10 minutes")
                    return
            
            # Analyze the final result
            analyze_extraction_results(result)
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_extraction_results(result):
    """Analyze the extraction results in detail"""
    
    print(f"\n📊 Final Result Analysis:")
    print(f"Total citations found: {len(result.get('citations', []))}")
    print(f"Total clusters found: {len(result.get('clusters', []))}")
    
    # Analyze citations
    citations = result.get('citations', [])
    print(f"\n📋 Detailed Citation Analysis:")
    print("=" * 100)
    
    extraction_issues = []
    verification_issues = []
    mismatch_issues = []
    data_quality_issues = []
    
    for i, citation in enumerate(citations):
        print(f"\n--- Citation {i+1} ---")
        print(f"Citation text: {citation.get('citation', 'N/A')}")
        print(f"Context: {citation.get('context', 'N/A')[:100]}...")
        
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
        
        # Additional fields
        cluster_id = citation.get('cluster_id', 'N/A')
        print(f"📚 Cluster ID: {cluster_id}")
        
        # Check for issues
        if extracted_name == 'N/A' or not extracted_name.strip():
            extraction_issues.append(f"Citation {i+1}: Missing extracted case name")
        
        if extracted_date == 'N/A' or not extracted_date.strip():
            extraction_issues.append(f"Citation {i+1}: Missing extracted date")
        
        if canonical_name == 'N/A' and verified:
            verification_issues.append(f"Citation {i+1}: Verified but missing canonical name")
        
        if canonical_date == 'N/A' and verified:
            verification_issues.append(f"Citation {i+1}: Verified but missing canonical date")
        
        # Check mismatch logic
        if name_mismatch:
            if extracted_name == canonical_name:
                mismatch_issues.append(f"Citation {i+1}: Name mismatch flagged but names match")
            else:
                print(f"🔍 Name mismatch details:")
                print(f"   Extracted: '{extracted_name}'")
                print(f"   Canonical: '{canonical_name}'")
        
        if date_mismatch:
            if extracted_date == canonical_date:
                mismatch_issues.append(f"Citation {i+1}: Date mismatch flagged but dates match")
            else:
                print(f"🔍 Date mismatch details:")
                print(f"   Extracted: '{extracted_date}'")
                print(f"   Canonical: '{canonical_date}'")
        
        # Check data quality
        if extracted_name and len(extracted_name) < 10:
            data_quality_issues.append(f"Citation {i+1}: Extracted name seems too short: '{extracted_name}'")
        
        if extracted_name and 'v.' not in extracted_name.lower():
            data_quality_issues.append(f"Citation {i+1}: Extracted name missing 'v.': '{extracted_name}'")
    
    # Analyze clusters
    clusters = result.get('clusters', [])
    if clusters:
        print(f"\n📚 Detailed Cluster Analysis:")
        print("=" * 100)
        
        for i, cluster in enumerate(clusters):
            print(f"\n--- Cluster {i+1} ---")
            print(f"Cluster ID: {cluster.get('cluster_id', 'N/A')}")
            print(f"Cluster case name: '{cluster.get('cluster_case_name', 'N/A')}'")
            print(f"Submitted display name: '{cluster.get('submitted_display_name', 'N/A')}'")
            print(f"Submitted display date: '{cluster.get('submitted_display_date', 'N/A')}'")
            print(f"Verifying display name: '{cluster.get('verifying_display_name', 'N/A')}'")
            print(f"Verifying display date: '{cluster.get('verifying_display_date', 'N/A')}'")
            print(f"Verification source: '{cluster.get('verification_source', 'N/A')}'")
            print(f"Has name mismatch: {cluster.get('has_name_mismatch', False)}")
            print(f"Has date mismatch: {cluster.get('has_date_mismatch', False)}")
            print(f"Citations in cluster: {len(cluster.get('citations', []))}")
            
            # Show individual citations in cluster
            cluster_citations = cluster.get('citations', [])
            for j, cit in enumerate(cluster_citations):
                print(f"  Citation {j+1}: {cit.get('citation', 'N/A')}")
                print(f"    Extracted: '{cit.get('extracted_case_name', 'N/A')}', {cit.get('extracted_date', 'N/A')}")
                print(f"    Verified: {cit.get('verified', False)}")
    
    # Summary
    print(f"\n🎯 Comprehensive Test Summary:")
    print("=" * 100)
    print(f"✅ Total citations processed: {len(citations)}")
    print(f"✅ Total clusters formed: {len(clusters)}")
    
    if extraction_issues:
        print(f"\n⚠️ Extraction Issues ({len(extraction_issues)}):")
        for issue in extraction_issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ No extraction issues found")
    
    if verification_issues:
        print(f"\n⚠️ Verification Issues ({len(verification_issues)}):")
        for issue in verification_issues:
            print(f"  - {issue}")
    else:
        print(f"✅ No verification issues found")
    
    if mismatch_issues:
        print(f"\n⚠️ Mismatch Detection Issues ({len(mismatch_issues)}):")
        for issue in mismatch_issues:
            print(f"  - {issue}")
    else:
        print(f"✅ No mismatch detection issues found")
    
    if data_quality_issues:
        print(f"\n⚠️ Data Quality Issues ({len(data_quality_issues)}):")
        for issue in data_quality_issues:
            print(f"  - {issue}")
    else:
        print(f"✅ No data quality issues found")
    
    # Overall assessment
    total_issues = len(extraction_issues) + len(verification_issues) + len(mismatch_issues) + len(data_quality_issues)
    if total_issues == 0:
        print(f"\n🎉 PERFECT: All case names, dates, and mismatches processed correctly!")
    else:
        print(f"\n⚠️ {total_issues} issue(s) found that need attention")
    
    # Save detailed results to file
    save_results_to_file(result, citations, clusters)

def save_results_to_file(result, citations, clusters):
    """Save detailed results to a JSON file for further analysis"""
    
    output_file = r"d:\dev\casestrainer\D2_59366_test_results.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': result.get('metadata', {}),
                'citations': citations,
                'clusters': clusters,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Failed to save results: {e}")

def main():
    """Main test function"""
    
    print("=" * 100)
    print("CASE NAME AND DATE EXTRACTION TEST - D2 59366-1-II")
    print("=" * 100)
    
    test_pdf_from_url()
    
    print(f"\n" + "=" * 100)
    print("TEST COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
