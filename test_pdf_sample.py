#!/usr/bin/env python3
"""
Test D2 59366-1-II PDF content with smaller text sample
"""

import requests
import tempfile
import os
import json

def test_pdf_content_sample():
    """Test PDF content with a smaller sample"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 Testing D2 59366-1-II PDF content with smaller sample...")
    
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
            # Extract text using the backend API
            print("📤 Extracting text from PDF...")
            api_url = "https://wolf.law.uw.edu/casestrainer/api/extract-text"
            
            with open(temp_path, 'rb') as f:
                files = {'file': f}
                extract_response = requests.post(api_url, files=files, timeout=60)
            
            if extract_response.status_code == 200:
                extract_result = extract_response.json()
                extracted_text = extract_result.get('text', '')
                
                print(f"✅ Text extracted ({len(extracted_text):,} characters)")
                
                # Take a sample of the text (first 2000 characters)
                sample_text = extracted_text[:2000]
                print(f"📄 Using first 2000 characters as sample...")
                
                print(f"\n📋 Sample text preview:")
                print("=" * 80)
                print(sample_text[:500] + "..." if len(sample_text) > 500 else sample_text)
                print("=" * 80)
                
                # Test the sample with our improved extraction
                print(f"\n🧪 Testing sample with improved extraction...")
                
                # Use the main API with the sample text
                analyze_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
                data = {
                    "text": sample_text,
                    "extract_case_names": True
                }
                
                print("📤 Sending sample for analysis...")
                analysis_response = requests.post(analyze_url, json=data, timeout=120)
                
                if analysis_response.status_code == 200:
                    result = analysis_response.json()
                    
                    print(f"\n📊 Sample Analysis Results:")
                    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
                    
                    citations = result.get('citations', [])
                    clusters = result.get('clusters', [])
                    
                    print(f"Citations found: {len(citations)}")
                    print(f"Clusters found: {len(clusters)}")
                    
                    if citations:
                        print(f"\n📋 Citation Analysis from PDF Sample:")
                        print("=" * 100)
                        
                        extraction_success = 0
                        verification_success = 0
                        
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
                            
                            # Count successes
                            if extracted_name != 'N/A' and extracted_name.strip():
                                extraction_success += 1
                            
                            if verified:
                                verification_success += 1
                        
                        # Summary
                        print(f"\n🎯 PDF SAMPLE TEST SUMMARY:")
                        print("=" * 100)
                        print(f"✅ Total citations processed: {len(citations)}")
                        print(f"✅ Successful extractions: {extraction_success}/{len(citations)} ({extraction_success/len(citations)*100:.1f}%)")
                        print(f"✅ Successful verifications: {verification_success}/{len(citations)} ({verification_success/len(citations)*100:.1f}%)")
                        print(f"✅ Total clusters formed: {len(clusters)}")
                        
                        # Check extraction quality
                        clean_names = 0
                        for citation in citations:
                            name = citation.get('extracted_case_name', '')
                            if name and len(name) < 50 and 'v.' in name:  # Clean name criteria
                                clean_names += 1
                        
                        print(f"✅ Clean case names: {clean_names}/{len(citations)} ({clean_names/len(citations)*100:.1f}%)")
                        
                        if extraction_success == len(citations) and verification_success == len(citations):
                            print(f"\n🎉 PERFECT: All case names extracted and verified correctly!")
                        elif extraction_success == len(citations):
                            print(f"\n✅ GOOD: All case names extracted, verification working ({verification_success}/{len(citations)})")
                        else:
                            print(f"\n⚠️ NEEDS IMPROVEMENT: {len(citations) - extraction_success} extraction issues found")
                        
                        # Save results
                        output_file = r"d:\dev\casestrainer\D2_59366_sample_results.json"
                        try:
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(result, f, indent=2, ensure_ascii=False)
                            print(f"\n💾 Sample results saved to: {output_file}")
                        except Exception as e:
                            print(f"\n❌ Failed to save results: {e}")
                    
                    else:
                        print(f"\n❌ No citations found in PDF sample")
                
                else:
                    print(f"❌ Sample analysis failed: {analysis_response.status_code}")
                    print(f"Response: {analysis_response.text}")
            
            else:
                print(f"❌ Text extraction failed: {extract_response.status_code}")
                print(f"Response: {extract_response.text}")
        
        finally:
            # Clean up
            os.unlink(temp_path)
            print("🧹 Cleaned up temporary file")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_content_sample()
