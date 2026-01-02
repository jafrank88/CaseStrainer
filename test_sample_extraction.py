#!/usr/bin/env python3
"""
Test case name and date extraction with sample legal text
"""

import requests
import json

def test_sample_extraction():
    """Test extraction with sample legal text"""
    
    # Sample legal text similar to what would be in D2 59366-1-II
    sample_text = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    STATE OF WASHINGTON,
        Respondent,
    v.
    JOHN DOE,
        Appellant.
    
    No. 59366-1-II
    UNPUBLISHED OPINION
    
    The court considers the precedent set in Smith v. Jones, 123 Wn.2d 456 (1998), where 
    the appellate court held that statutory interpretation requires careful analysis of 
    legislative intent. Similarly, in Johnson v. Washington State Dept., 456 P.3d 789 (2020),
    the court addressed administrative law principles.
    
    Furthermore, the case of Brown v. City of Seattle, 789 Wn. App. 234 (2015), established
    important guidelines for municipal liability. The court also referenced the earlier 
    decision in Anderson v. Clark, 312 P.2d 123 (1957), which remains good law.
    
    The appellant relies on the reasoning from Martinez v. County of Pierce, 567 P.3d 890 (2022),
    while the respondent cites Wilson v. State, 234 Wn.2d 567 (2010) and Taylor v. Federal Way, 
    890 P.3d 345 (2019) as controlling authority.
    """
    
    print("🔍 Testing case name and date extraction with sample legal text...")
    print(f"Sample text length: {len(sample_text)} characters")
    
    try:
        # Test the main analysis endpoint
        url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        data = {
            "text": sample_text,
            "extract_case_names": True
        }
        
        print("📤 Sending text for analysis...")
        response = requests.post(url, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Response Analysis:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            if citations:
                print(f"\n📋 Detailed Citation Analysis:")
                print("=" * 100)
                
                extraction_issues = []
                verification_issues = []
                mismatch_issues = []
                data_quality_issues = []
                
                for i, citation in enumerate(citations):
                    print(f"\n--- Citation {i+1} ---")
                    print(f"Citation: {citation.get('citation', 'N/A')}")
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
                    if name_mismatch and extracted_name == canonical_name:
                        mismatch_issues.append(f"Citation {i+1}: Name mismatch flagged but names match")
                    
                    if date_mismatch and extracted_date == canonical_date:
                        mismatch_issues.append(f"Citation {i+1}: Date mismatch flagged but dates match")
                    
                    # Check data quality
                    if extracted_name and len(extracted_name) < 10:
                        data_quality_issues.append(f"Citation {i+1}: Extracted name seems too short: '{extracted_name}'")
                    
                    if extracted_name and 'v.' not in extracted_name.lower() and ' v ' not in extracted_name:
                        data_quality_issues.append(f"Citation {i+1}: Extracted name missing 'v.': '{extracted_name}'")
                
                # Analyze clusters
                if clusters:
                    print(f"\n📚 Cluster Analysis:")
                    print("=" * 100)
                    
                    for i, cluster in enumerate(clusters):
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
                print(f"\n🎯 SAMPLE TEXT TEST SUMMARY:")
                print("=" * 100)
                print(f"✅ Total citations processed: {len(citations)}")
                print(f"✅ Total clusters formed: {len(clusters)}")
                
                # Count verification status
                verified_count = sum(1 for c in citations if c.get('verified', False))
                print(f"✅ Verified citations: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
                
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
                
                # Save results
                output_file = r"d:\dev\casestrainer\sample_test_results.json"
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Sample test results saved to: {output_file}")
                except Exception as e:
                    print(f"\n❌ Failed to save results: {e}")
            
            else:
                print(f"\n❌ No citations found in sample text")
        
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_sample_extraction()
