#!/usr/bin/env python3
"""
Download and test D2 59366-1-II PDF as file upload
"""

import requests
import os
import tempfile

def download_and_test_pdf():
    """Download PDF and test as file upload"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 Downloading D2 59366-1-II PDF...")
    
    try:
        # Download the PDF
        response = requests.get(pdf_url, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ PDF downloaded successfully ({len(response.content):,} bytes)")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            print(f"📁 Saved to: {temp_path}")
            
            # Test with file upload
            api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
            
            print(f"\n📤 Testing file upload...")
            
            with open(temp_path, 'rb') as f:
                files = {'file': f}
                data = {'extract_case_names': True}
                
                upload_response = requests.post(api_url, files=files, data=data, timeout=120)
            
            print(f"Upload status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                
                print(f"\n📊 File Upload Analysis:")
                print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"Citations found: {len(citations)}")
                print(f"Clusters found: {len(clusters)}")
                
                # Detailed analysis
                print(f"\n📋 Detailed Citation Analysis:")
                print("=" * 80)
                
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
                    print("=" * 80)
                    
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
                print(f"\n🎯 Test Summary:")
                print("=" * 80)
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
                
                # Overall assessment
                total_issues = len(extraction_issues) + len(verification_issues) + len(mismatch_issues)
                if total_issues == 0:
                    print(f"\n🎉 PERFECT: All case names, dates, and mismatches processed correctly!")
                else:
                    print(f"\n⚠️ {total_issues} issue(s) found that need attention")
                
            else:
                print(f"❌ Upload failed: {upload_response.status_code}")
                print(f"Response: {upload_response.text}")
            
            # Clean up
            os.unlink(temp_path)
            print(f"\n🧹 Cleaned up temporary file")
            
        else:
            print(f"❌ Failed to download PDF: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_and_test_pdf()
