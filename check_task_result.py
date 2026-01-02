#!/usr/bin/env python3
"""
Check the task result for the D2 59366-1-II PDF
"""

import requests
import json

def check_task_result():
    """Check the completed task result"""
    
    task_id = "43492d45-8172-41f7-86ec-7e1222b99ce7"
    url = f"https://wolf.law.uw.edu/casestrainer/api/task/{task_id}"
    
    print(f"🔍 Checking task result for: {task_id}")
    
    try:
        response = requests.get(url, timeout=30)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Task Status: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'completed':
                task_result = result.get('result', {})
                
                print(f"\n📋 Analysis Results:")
                print(f"Processing mode: {task_result.get('metadata', {}).get('processing_mode', 'unknown')}")
                print(f"Citations found: {len(task_result.get('citations', []))}")
                print(f"Clusters found: {len(task_result.get('clusters', []))}")
                
                citations = task_result.get('citations', [])
                clusters = task_result.get('clusters', [])
                
                if citations:
                    print(f"\n📋 Citation Analysis:")
                    print("=" * 80)
                    
                    for i, citation in enumerate(citations[:10]):  # Show first 10
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
                
                if clusters:
                    print(f"\n📚 Cluster Analysis:")
                    print("=" * 80)
                    
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
                
                # Summary analysis
                print(f"\n🎯 D2 59366-1-II Test Summary:")
                print("=" * 80)
                
                extraction_issues = []
                verification_issues = []
                mismatch_issues = []
                
                for i, citation in enumerate(citations):
                    extracted_name = citation.get('extracted_case_name', 'N/A')
                    extracted_date = citation.get('extracted_date', 'N/A')
                    canonical_name = citation.get('canonical_name', 'N/A')
                    canonical_date = citation.get('canonical_date', 'N/A')
                    verified = citation.get('verified', False)
                    name_mismatch = citation.get('name_mismatch', False)
                    date_mismatch = citation.get('date_mismatch', False)
                    
                    if extracted_name == 'N/A' or not extracted_name.strip():
                        extraction_issues.append(f"Citation {i+1}: Missing extracted case name")
                    
                    if extracted_date == 'N/A' or not extracted_date.strip():
                        extraction_issues.append(f"Citation {i+1}: Missing extracted date")
                    
                    if canonical_name == 'N/A' and verified:
                        verification_issues.append(f"Citation {i+1}: Verified but missing canonical name")
                    
                    if canonical_date == 'N/A' and verified:
                        verification_issues.append(f"Citation {i+1}: Verified but missing canonical date")
                    
                    if name_mismatch and extracted_name == canonical_name:
                        mismatch_issues.append(f"Citation {i+1}: Name mismatch flagged but names match")
                    
                    if date_mismatch and extracted_date == canonical_date:
                        mismatch_issues.append(f"Citation {i+1}: Date mismatch flagged but dates match")
                
                print(f"✅ Total citations processed: {len(citations)}")
                print(f"✅ Total clusters formed: {len(clusters)}")
                
                if extraction_issues:
                    print(f"\n⚠️ Extraction Issues ({len(extraction_issues)}):")
                    for issue in extraction_issues[:5]:  # Show first 5
                        print(f"  - {issue}")
                else:
                    print(f"\n✅ No extraction issues found")
                
                if verification_issues:
                    print(f"\n⚠️ Verification Issues ({len(verification_issues)}):")
                    for issue in verification_issues[:5]:  # Show first 5
                        print(f"  - {issue}")
                else:
                    print(f"✅ No verification issues found")
                
                if mismatch_issues:
                    print(f"\n⚠️ Mismatch Detection Issues ({len(mismatch_issues)}):")
                    for issue in mismatch_issues[:5]:  # Show first 5
                        print(f"  - {issue}")
                else:
                    print(f"✅ No mismatch detection issues found")
                
                # Overall assessment
                total_issues = len(extraction_issues) + len(verification_issues) + len(mismatch_issues)
                if total_issues == 0:
                    print(f"\n🎉 PERFECT: All case names, dates, and mismatches processed correctly!")
                else:
                    print(f"\n⚠️ {total_issues} issue(s) found that need attention")
                
                # Save results
                with open(r"d:\dev\casestrainer\D2_59366_results.json", 'w', encoding='utf-8') as f:
                    json.dump(task_result, f, indent=2, ensure_ascii=False)
                
                print(f"\n💾 Full results saved to: D2_59366_results.json")
                
            else:
                print(f"❌ Task not completed: {result.get('status', 'unknown')}")
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_task_result()
