#!/usr/bin/env python3
"""
Test D2 59366-1-II PDF with direct text extraction and analysis
"""

import requests
import tempfile
import os
import json

def test_direct_extraction():
    """Test direct extraction without async processing"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 Testing D2 59366-1-II PDF with direct extraction...")
    
    try:
        # Download the PDF
        print("📥 Downloading PDF...")
        response = requests.get(pdf_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to download PDF: {response.status_code}")
            return
        
        print(f"✅ PDF downloaded ({len(response.content):,} bytes)")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        try:
            # Extract text using a simple approach
            print("📤 Extracting text from PDF...")
            
            # Try to upload and get immediate processing by using a smaller timeout
            # and forcing sync processing by using a small text sample
            api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
            
            # Upload the file with a short timeout to force sync processing
            with open(temp_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'extract_case_names': True,
                    'force_sync': True  # Try to force sync processing
                }
                
                print("📤 Uploading PDF for analysis...")
                upload_response = requests.post(api_url, files=files, data=data, timeout=300)
            
            print(f"Upload status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                
                print(f"\n📊 Direct Analysis Results:")
                print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"Citations found: {len(citations)}")
                print(f"Clusters found: {len(clusters)}")
                
                if citations:
                    print(f"\n📋 Citation Analysis (First 10):")
                    print("=" * 100)
                    
                    extraction_success = 0
                    verification_success = 0
                    extraction_issues = []
                    
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
                        
                        # Count successes
                        if extracted_name != 'N/A' and extracted_name.strip():
                            extraction_success += 1
                        
                        if verified:
                            verification_success += 1
                        
                        # Check issues
                        if extracted_name == 'N/A' or not extracted_name.strip():
                            extraction_issues.append(f"Citation {i+1}: Missing extracted case name")
                        
                        if extracted_date == 'N/A' or not extracted_date.strip():
                            extraction_issues.append(f"Citation {i+1}: Missing extracted date")
                    
                    # Summary
                    print(f"\n🎯 DIRECT TEST SUMMARY:")
                    print("=" * 100)
                    print(f"✅ Total citations processed: {len(citations)}")
                    print(f"✅ Successful extractions: {extraction_success}/{len(citations)} ({extraction_success/len(citations)*100:.1f}%)")
                    print(f"✅ Successful verifications: {verification_success}/{len(citations)} ({verification_success/len(citations)*100:.1f}%)")
                    print(f"✅ Total clusters formed: {len(clusters)}")
                    
                    if extraction_issues:
                        print(f"\n⚠️ Extraction Issues ({len(extraction_issues)}):")
                        for issue in extraction_issues[:5]:
                            print(f"  - {issue}")
                    else:
                        print(f"\n✅ No extraction issues found")
                    
                    # Overall assessment
                    if extraction_success == len(citations) and verification_success == len(citations):
                        print(f"\n🎉 PERFECT: All case names extracted and verified correctly!")
                    elif extraction_success == len(citations):
                        print(f"\n✅ GOOD: All case names extracted, verification needs work")
                    else:
                        print(f"\n⚠️ NEEDS IMPROVEMENT: {len(extraction_issues)} extraction issues found")
                    
                    # Save results
                    output_file = r"d:\dev\casestrainer\D2_59366_direct_results.json"
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        print(f"\n💾 Results saved to: {output_file}")
                    except Exception as e:
                        print(f"\n❌ Failed to save results: {e}")
                
                else:
                    print(f"\n❌ No citations found in the document")
            
            else:
                print(f"❌ Upload failed: {upload_response.status_code}")
                print(f"Response: {upload_response.text}")
        
        finally:
            # Clean up
            os.unlink(temp_path)
            print("🧹 Cleaned up temporary file")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_direct_extraction()
