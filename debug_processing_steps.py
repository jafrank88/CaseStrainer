#!/usr/bin/env python3
"""
Debug each processing step to see where name extraction might be failing.
"""

import requests
import time
import json

def test_processing_steps_detailed():
    """Test processing with detailed step-by-step analysis."""
    
    # Test document with clear case names
    test_text = """
    Legal Document for Step-by-Step Analysis
    
    Important cases with clear names:
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Criminal law case
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Municipal law
    3. Brown v. State of Washington, 180 Wn.2d 300, 320 P.3d 800 (2014) - Civil rights
    4. Miller v. Jones, 190 Wn.2d 400, 350 P.3d 900 (2015) - Contract dispute
    5. Davis v. County of King, 200 Wn.2d 500, 400 P.3d 1000 (2018) - Property law
    
    These cases should have clear extracted names and proper clustering.
    """ + "\n\nPadding content. " * 200  # Make it large enough for async
    
    print("🔍 Processing Steps Analysis")
    print("=" * 60)
    print(f"📄 Document size: {len(test_text)} characters ({len(test_text)/1024:.1f} KB)")
    print()
    
    # Submit for processing
    print("📤 Step 1: Submitting document...")
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Submission failed: {response.status_code}")
            return False
            
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        task_id = data.get('task_id')
        job_id = data.get('metadata', {}).get('job_id')
        
        print(f"  Processing mode: {processing_mode}")
        print(f"  Task ID: {task_id}")
        print(f"  Job ID: {job_id}")
        
        if processing_mode == 'sync_fallback':
            print("  🔄 Sync fallback - analyzing immediate results...")
            return analyze_final_results(data)
        
        if not (task_id or job_id):
            print("  ❌ No tracking ID available")
            return False
        
        tracking_id = task_id or job_id
        print(f"  ✅ Async processing started: {tracking_id}")
        
        # Monitor processing steps
        print(f"\n🔄 Step 2: Monitoring Processing Steps...")
        
        step_names = {
            0: "Initializing",
            1: "Extract Citations", 
            2: "Analyze Citations",
            3: "Extract Names",
            4: "Verify Citations",
            5: "Cluster Citations"
        }
        
        last_step = -1
        for attempt in range(30):  # Increased attempts
            try:
                # Check progress
                progress_response = requests.get(
                    f"http://localhost:8080/casestrainer/api/analyze/progress/{tracking_id}",
                    timeout=5
                )
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    current_step = progress_data.get('current_step', 0)
                    progress = progress_data.get('progress', 0)
                    status = progress_data.get('status', 'unknown')
                    
                    if current_step != last_step:
                        step_name = step_names.get(current_step, f"Step {current_step}")
                        print(f"    📋 {step_name} ({progress:.1f}%)")
                        last_step = current_step
                
                # Check final status
                status_response = requests.get(
                    f"http://localhost:8080/casestrainer/api/task_status/{tracking_id}",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    final_status = status_data.get('status', 'unknown')
                    
                    if final_status == 'completed':
                        print(f"    ✅ Processing completed!")
                        return analyze_final_results(status_data)
                    elif final_status == 'failed':
                        print(f"    ❌ Processing failed: {status_data}")
                        return False
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    ⚠️ Monitoring error: {e}")
                time.sleep(1)
        
        print("  ❌ Timeout waiting for completion")
        return False
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return False

def analyze_final_results(data):
    """Analyze the final processing results in detail."""
    
    print(f"\n📊 Step 3: Analyzing Final Results...")
    
    citations = data.get('citations', [])
    clusters = data.get('clusters', [])
    statistics = data.get('statistics', {})
    
    print(f"  📋 Overall Results:")
    print(f"    Citations found: {len(citations)}")
    print(f"    Clusters found: {len(clusters)}")
    print(f"    Statistics: {statistics}")
    print()
    
    # Analyze citations in detail
    print(f"  🔍 Citation Analysis:")
    citations_with_names = 0
    citations_with_canonical = 0
    
    for i, citation in enumerate(citations[:10], 1):  # Limit to first 10
        extracted_name = citation.get('extracted_case_name', '')
        canonical_name = citation.get('canonical_name', '')
        extracted_date = citation.get('extracted_date', '')
        verified = citation.get('verified', False)
        method = citation.get('method', 'unknown')
        
        print(f"    Citation {i}:")
        print(f"      Text: {citation.get('citation', 'N/A')}")
        print(f"      Extracted Name: '{extracted_name}' {'✅' if extracted_name else '❌'}")
        print(f"      Canonical Name: '{canonical_name}' {'✅' if canonical_name else '⚠️'}")
        print(f"      Extracted Date: '{extracted_date}' {'✅' if extracted_date else '❌'}")
        print(f"      Verified: {verified}")
        print(f"      Method: {method}")
        print()
        
        if extracted_name:
            citations_with_names += 1
        if canonical_name:
            citations_with_canonical += 1
    
    print(f"  📊 Name Extraction Summary:")
    print(f"    Citations with extracted names: {citations_with_names}/{len(citations)} ({citations_with_names/len(citations)*100:.1f}%)")
    print(f"    Citations with canonical names: {citations_with_canonical}/{len(citations)} ({citations_with_canonical/len(citations)*100:.1f}%)")
    print()
    
    # Analyze clusters
    print(f"  🔗 Cluster Analysis:")
    if len(clusters) == 0:
        print(f"    ⚠️ No clusters found")
    else:
        for i, cluster in enumerate(clusters, 1):
            cluster_citations = cluster.get('citations', [])
            cluster_names = [c.get('extracted_case_name', '') for c in cluster_citations if c.get('extracted_case_name')]
            
            print(f"    Cluster {i}:")
            print(f"      Citations in cluster: {len(cluster_citations)}")
            print(f"      Unique extracted names: {list(set(cluster_names))}")
            print(f"      Representative: {cluster.get('representative_citation', 'N/A')}")
            print()
    
    # Final assessment
    print(f"  🎯 Assessment:")
    success = True
    
    if citations_with_names == 0:
        print(f"    ❌ CRITICAL: No extracted names found!")
        success = False
    elif citations_with_names < len(citations) * 0.7:
        print(f"    ⚠️ WARNING: Low name extraction rate ({citations_with_names/len(citations)*100:.1f}%)")
    else:
        print(f"    ✅ Good name extraction rate ({citations_with_names/len(citations)*100:.1f}%)")
    
    if citations_with_canonical == 0:
        print(f"    ⚠️ No canonical names (verification disabled or failing)")
    else:
        print(f"    ✅ Some canonical names found ({citations_with_canonical/len(citations)*100:.1f}%)")
    
    if len(clusters) == 0:
        print(f"    ⚠️ No clusters found (may be normal if no parallel citations)")
    else:
        print(f"    ✅ Clustering working ({len(clusters)} clusters)")
    
    return success

def main():
    """Run detailed processing steps analysis."""
    
    print("🚀 Processing Steps Investigation")
    print("=" * 60)
    
    success = test_processing_steps_detailed()
    
    print("\n" + "=" * 60)
    print("📋 FINAL ASSESSMENT")
    print("=" * 60)
    
    if success:
        print("✅ Processing pipeline is working correctly")
        print("   - Citations are being extracted")
        print("   - Names are being extracted") 
        print("   - Clustering is functioning")
    else:
        print("❌ Issues found in processing pipeline")
        print("   Check the detailed output above for specific problems")

if __name__ == "__main__":
    main()
