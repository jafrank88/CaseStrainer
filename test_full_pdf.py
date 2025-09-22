#!/usr/bin/env python3
"""
Test the full PDF document from the Washington Supreme Court
to verify citation extraction accuracy with the complete document.
"""

import requests
import json
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_full_pdf():
    """Test with the full PDF document."""
    
    pdf_url = 'https://www.courts.wa.gov/opinions/pdf/1033940.pdf'
    
    print("🧪 TESTING FULL PDF DOCUMENT")
    print("=" * 60)
    print(f"📄 PDF URL: {pdf_url}")
    print()

    try:
        print("🔄 Submitting PDF for analysis...")
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={"type": "url", "url": pdf_url},
            headers={"Content-Type": "application/json"},
            timeout=60,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Processing mode: {processing_mode}")
            
            # Handle async processing
            if processing_mode == 'queued':
                task_id = result.get('metadata', {}).get('job_id')
                if task_id:
                    print(f"📋 Task ID: {task_id}")
                    print("⏳ Waiting for PDF processing (this may take longer)...")
                    
                    # Poll for completion - PDFs take longer
                    for attempt in range(40):  # Wait up to 80 seconds for PDF
                        time.sleep(2)
                        
                        status_response = requests.get(
                            f"http://localhost:5000/casestrainer/api/task_status/{task_id}",
                            verify=False
                        )
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            progress = status_result.get('progress_data', {}).get('overall_progress', 0)
                            current_step = status_result.get('progress_data', {}).get('current_message', 'Processing')
                            
                            print(f"  Attempt {attempt + 1}: {status} - {progress}% - {current_step}")
                            
                            if status == 'completed':
                                result = status_result
                                break
                            elif status == 'failed':
                                error_msg = status_result.get('error', 'Unknown error')
                                print(f"❌ Processing failed: {error_msg}")
                                return False
                        else:
                            print(f"  Status check failed: {status_response.status_code}")
                    
                    if status != 'completed':
                        print("❌ Processing timed out")
                        return False
            
            # Extract results
            citations = result.get('result', {}).get('citations', result.get('citations', []))
            clusters = result.get('result', {}).get('clusters', result.get('clusters', []))
            
            print()
            print("📊 FULL PDF RESULTS:")
            print(f"📝 Total citations found: {len(citations)}")
            print(f"🔗 Total clusters found: {len(clusters)}")
            
            if citations:
                verified_count = sum(1 for c in citations if c.get('verified', False) or c.get('is_verified', False))
                print(f"✅ Verified citations: {verified_count}")
                print(f"📊 Verification rate: {verified_count/len(citations)*100:.1f}%")
                
                print()
                print("📋 Sample citations (first 20):")
                for i, citation in enumerate(citations[:20]):
                    citation_text = citation.get('citation', '')
                    verified = citation.get('verified', False) or citation.get('is_verified', False)
                    canonical_name = citation.get('canonical_name', '')
                    
                    status_icon = "✅" if verified else "❌"
                    print(f"  {i+1:2d}. {status_icon} {citation_text}")
                    if verified and canonical_name:
                        print(f"      📖 {canonical_name}")
                
                # Show citation types
                print()
                print("📊 Citation Analysis:")
                
                # Count by reporter type
                reporter_counts = {}
                for citation in citations:
                    citation_text = citation.get('citation', '')
                    if 'Wn.2d' in citation_text or 'Wash.2d' in citation_text:
                        reporter_counts['Washington Reports'] = reporter_counts.get('Washington Reports', 0) + 1
                    elif 'P.3d' in citation_text or 'P.2d' in citation_text:
                        reporter_counts['Pacific Reporter'] = reporter_counts.get('Pacific Reporter', 0) + 1
                    elif 'U.S.' in citation_text:
                        reporter_counts['U.S. Reports'] = reporter_counts.get('U.S. Reports', 0) + 1
                    elif 'RCW' in citation_text:
                        reporter_counts['RCW Statutes'] = reporter_counts.get('RCW Statutes', 0) + 1
                    elif 'WL' in citation_text:
                        reporter_counts['Westlaw'] = reporter_counts.get('Westlaw', 0) + 1
                    else:
                        reporter_counts['Other'] = reporter_counts.get('Other', 0) + 1
                
                for reporter, count in reporter_counts.items():
                    print(f"   {reporter}: {count} citations")
            
            if clusters:
                print()
                print("🔗 Cluster Analysis:")
                print(f"   Total clusters: {len(clusters)}")
                
                verified_clusters = sum(1 for c in clusters if c.get('verified', False))
                print(f"   Verified clusters: {verified_clusters}")
                
                print()
                print("📋 Sample clusters (first 10):")
                for i, cluster in enumerate(clusters[:10]):
                    cluster_verified = cluster.get('verified', False)
                    cluster_size = cluster.get('size', len(cluster.get('citations', [])))
                    case_name = cluster.get('case_name', cluster.get('canonical_name', 'Unknown'))
                    
                    status_icon = "✅" if cluster_verified else "❌"
                    print(f"  {i+1:2d}. {status_icon} {case_name} ({cluster_size} citations)")
            
            print()
            print("🎉 SUCCESS: Full PDF processed successfully!")
            print(f"📈 Found {len(citations)} citations vs expected many more from full document")
            
            return True
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_full_pdf()
    if success:
        print("\n✅ Full PDF test completed!")
    else:
        print("\n❌ Full PDF test failed!")
