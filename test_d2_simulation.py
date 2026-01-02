#!/usr/bin/env python3
"""
Test D2 59366-1-II content with realistic legal text sample
"""

import requests
import json

def test_d2_content_simulation():
    """Test with realistic D2 59366-1-II content simulation"""
    
    # Simulated text content that would be typical in a Washington Court of Appeals opinion
    d2_sample_text = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    STATE OF WASHINGTON,
        Respondent,
    v.
    JOHN DOE,
        Appellant.
    
    No. 59366-1-II
    UNPUBLISHED OPINION
    
    PUBLISHED: April 15, 2024
    
    Trial Court: Superior Court, Pierce County
    No. 21-1-01234-6
    Judge: John Smith
    
    ATTORNEYS FOR APPELLANT:
    John A. Smith
    Smith & Associates
    
    ATTORNEYS FOR RESPONDENT:
    Jane B. Johnson
    Washington State Attorney General's Office
    
    FACTS
    This case arises from a traffic stop conducted on January 15, 2021, in Pierce County, 
    Washington. Officer Mark Wilson of the Pierce County Sheriff's Department observed the 
    appellant's vehicle traveling 45 mph in a 35 mph zone. The officer initiated a traffic 
    stop and subsequently arrested the appellant for driving under the influence.
    
    The appellant filed a motion to suppress evidence, arguing that the traffic stop violated 
    his Fourth Amendment rights. The trial court denied the motion, and the appellant was 
    convicted of DUI. This appeal followed.
    
    ANALYSIS
    The appellant argues that the trial court erred in denying his motion to suppress. 
    We review de novo whether a traffic stop violates the Fourth Amendment. State v. 
    Ladson, 148 Wn.2d 325, 59 P.3d 771 (2002). The State bears the burden of showing that 
    the officer had reasonable suspicion that the appellant was violating the law. 
    State v. Harrington, 167 Wn.2d 656, 260 P.3d 951 (2011).
    
    In State v. Madsen, 168 Wn.2d 496, 229 P.3d 729 (2010), the Supreme Court held that 
    reasonable suspicion exists when an officer observes a traffic violation. Here, 
    Officer Wilson observed the appellant's vehicle exceeding the speed limit, which 
    provided reasonable suspicion for the traffic stop. See also State v. Clevenger, 
    174 Wn.2d 485, 275 P.3d 967 (2012).
    
    The appellant relies on State v. Kennedy, 133 Wn.2d 598, 947 P.2d 1001 (1997), 
    where the court suppressed evidence because the officer lacked reasonable suspicion. 
    However, Kennedy is distinguishable because the officer in that case had not observed 
    any actual traffic violation. Unlike Kennedy, Officer Wilson here directly observed 
    the appellant speeding.
    
    Furthermore, in State v. Williams, 102 Wn. App. 745, 8 P.3d 647 (2000), 
    this court held that visual observation of speeding constitutes reasonable suspicion. 
    The Williams court emphasized that "the Fourth Amendment does not require police 
    officers to have perfect knowledge of the speed limit" to justify a traffic stop. 
    Williams, 102 Wn. App. at 752.
    
    The appellant also cites State v. Rivera, 185 Wn.2d 397, 373 P.3d 185 (2016), 
    arguing that the officer's speed measurement was unreliable. However, Rivera involved 
    radar equipment issues not present in this case. Here, Officer Wilson estimated the 
    vehicle's speed visually, which this court has repeatedly upheld as sufficient for 
    reasonable suspicion. See State v. Gorman, 191 Wn. App. 860, 361 P.3d 718 (2015).
    
    CONCLUSION
    Based on the foregoing authorities, we conclude that Officer Wilson had reasonable 
    suspicion to initiate the traffic stop. The trial court properly denied the appellant's 
    motion to suppress. Accordingly, we affirm the conviction.
    
    CONCURRING: Judge Johnson
    DISSENTING: Judge Davis
    
    """
    
    print("🔍 Testing D2 59366-1-II content simulation...")
    print(f"Text length: {len(d2_sample_text)} characters")
    
    try:
        # Test with the main API
        url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        data = {
            "text": d2_sample_text,
            "extract_case_names": True
        }
        
        print("📤 Sending D2 59366-1-II simulation for analysis...")
        response = requests.post(url, json=data, timeout=120)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 D2 59366-1-II Simulation Results:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            if citations:
                print(f"\n📋 Detailed Citation Analysis:")
                print("=" * 100)
                
                extraction_success = 0
                verification_success = 0
                clean_names = 0
                extraction_issues = []
                verification_issues = []
                mismatch_issues = []
                
                for i, citation in enumerate(citations):
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
                    
                    # Count successes and check quality
                    if extracted_name != 'N/A' and extracted_name.strip():
                        extraction_success += 1
                    
                    if verified:
                        verification_success += 1
                    
                    # Check for clean case names
                    if extracted_name and len(extracted_name) < 50 and 'v.' in extracted_name:
                        clean_names += 1
                    
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
                print(f"\n🎯 D2 59366-1-II CONTENT TEST SUMMARY:")
                print("=" * 100)
                print(f"✅ Total citations processed: {len(citations)}")
                print(f"✅ Successful extractions: {extraction_success}/{len(citations)} ({extraction_success/len(citations)*100:.1f}%)")
                print(f"✅ Successful verifications: {verification_success}/{len(citations)} ({verification_success/len(citations)*100:.1f}%)")
                print(f"✅ Clean case names: {clean_names}/{len(citations)} ({clean_names/len(citations)*100:.1f}%)")
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
                
                # Overall assessment
                total_issues = len(extraction_issues) + len(verification_issues) + len(mismatch_issues)
                if total_issues == 0:
                    print(f"\n🎉 PERFECT: All case names, dates, and mismatches processed correctly!")
                elif extraction_success == len(citations) and clean_names >= len(citations) * 0.8:
                    print(f"\n✅ EXCELLENT: High-quality extraction with minimal issues")
                elif extraction_success == len(citations):
                    print(f"\n✅ GOOD: All case names extracted, some quality improvements needed")
                else:
                    print(f"\n⚠️ NEEDS IMPROVEMENT: {total_issues} issue(s) found that need attention")
                
                # Save results
                output_file = r"d:\dev\casestrainer\D2_59366_simulation_results.json"
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Simulation results saved to: {output_file}")
                except Exception as e:
                    print(f"\n❌ Failed to save results: {e}")
            
            else:
                print(f"\n❌ No citations found in D2 59366-1-II simulation")
        
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_d2_content_simulation()
