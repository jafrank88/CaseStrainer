#!/usr/bin/env python3
"""
Test D2 59366-1-II PDF extraction without verification
"""

import requests
import json
import tempfile
import os

def test_extraction_only():
    """Test extraction without verification"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    print("🔍 Testing D2 59366-1-II PDF extraction (verification disabled)...")
    
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
            # Test with text extraction only (no verification)
            api_url = "https://wolf.law.uw.edu/casestrainer/api/extract-text"
            
            print("📤 Extracting text from PDF...")
            with open(temp_path, 'rb') as f:
                files = {'file': f}
                extract_response = requests.post(api_url, files=files, timeout=60)
            
            if extract_response.status_code == 200:
                extract_result = extract_response.json()
                extracted_text = extract_result.get('text', '')
                
                print(f"✅ Text extracted ({len(extracted_text):,} characters)")
                
                # Now process the text with citation extraction only
                process_url = "https://wolf.law.uw.edu/casestrainer/api/extract-citations"
                process_data = {
                    "text": extracted_text,
                    "extract_case_names": True,
                    "skip_verification": True  # Try to skip verification
                }
                
                print("📤 Processing citations from extracted text...")
                process_response = requests.post(process_url, json=process_data, timeout=120)
                
                if process_response.status_code == 200:
                    result = process_response.json()
                    analyze_extraction_results(result)
                else:
                    print(f"❌ Citation processing failed: {process_response.status_code}")
                    print(f"Response: {process_response.text}")
                
            else:
                print(f"❌ Text extraction failed: {extract_response.status_code}")
                print(f"Response: {extract_response.text}")
        
        finally:
            # Clean up
            os.unlink(temp_path)
            print("🧹 Cleaned up temporary file")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_extraction_results(result):
    """Analyze the extraction results"""
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📋 EXTRACTION ANALYSIS:")
    print("=" * 100)
    print(f"Total citations found: {len(citations)}")
    print(f"Total clusters formed: {len(clusters)}")
    
    if citations:
        print(f"\n📋 Citation Analysis (First 20):")
        print("=" * 100)
        
        extraction_success = 0
        extraction_issues = []
        data_quality_issues = []
        
        for i, citation in enumerate(citations[:20]):  # Show first 20
            print(f"\n--- Citation {i+1} ---")
            print(f"Citation: {citation.get('citation', 'N/A')}")
            
            # Extracted data
            extracted_name = citation.get('extracted_case_name', 'N/A')
            extracted_date = citation.get('extracted_date', 'N/A')
            print(f"📝 Extracted name: '{extracted_name}'")
            print(f"📅 Extracted date: '{extracted_date}'")
            
            # Context
            context = citation.get('context', 'N/A')
            if context != 'N/A':
                print(f"📄 Context: {context[:100]}...")
            
            # Check extraction quality
            if extracted_name != 'N/A' and extracted_name.strip():
                extraction_success += 1
                
                # Check data quality
                if len(extracted_name) < 10:
                    data_quality_issues.append(f"Citation {i+1}: Extracted name too short: '{extracted_name}'")
                
                if 'v.' not in extracted_name.lower() and ' v ' not in extracted_name:
                    data_quality_issues.append(f"Citation {i+1}: Extracted name missing 'v.': '{extracted_name}'")
            else:
                extraction_issues.append(f"Citation {i+1}: Missing extracted case name")
            
            if extracted_date == 'N/A' or not extracted_date.strip():
                extraction_issues.append(f"Citation {i+1}: Missing extracted date")
        
        # Analyze clusters
        if clusters:
            print(f"\n📚 Cluster Analysis (First 5):")
            print("=" * 100)
            
            for i, cluster in enumerate(clusters[:5]):  # Show first 5
                print(f"\n--- Cluster {i+1} ---")
                print(f"Cluster ID: {cluster.get('cluster_id', 'N/A')}")
                print(f"Submitted display name: '{cluster.get('submitted_display_name', 'N/A')}'")
                print(f"Submitted display date: '{cluster.get('submitted_display_date', 'N/A')}'")
                print(f"Citations in cluster: {len(cluster.get('citations', []))}")
        
        # Summary
        print(f"\n🎯 EXTRACTION TEST SUMMARY:")
        print("=" * 100)
        print(f"✅ Total citations processed: {len(citations)}")
        print(f"✅ Successful extractions: {extraction_success}/{len(citations)} ({extraction_success/len(citations)*100:.1f}%)")
        print(f"✅ Total clusters formed: {len(clusters)}")
        
        if extraction_issues:
            print(f"\n⚠️ Extraction Issues ({len(extraction_issues)}):")
            for issue in extraction_issues[:5]:
                print(f"  - {issue}")
            if len(extraction_issues) > 5:
                print(f"  ... and {len(extraction_issues) - 5} more")
        else:
            print(f"\n✅ No extraction issues found")
        
        if data_quality_issues:
            print(f"\n⚠️ Data Quality Issues ({len(data_quality_issues)}):")
            for issue in data_quality_issues[:5]:
                print(f"  - {issue}")
            if len(data_quality_issues) > 5:
                print(f"  ... and {len(data_quality_issues) - 5} more")
        else:
            print(f"✅ No data quality issues found")
        
        # Overall assessment
        total_issues = len(extraction_issues) + len(data_quality_issues)
        if total_issues == 0:
            print(f"\n🎉 PERFECT: All case names and dates extracted correctly!")
        else:
            print(f"\n⚠️ {total_issues} issue(s) found that need attention")
        
        # Save results
        output_file = r"d:\dev\casestrainer\D2_59366_extraction_results.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Extraction results saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")
    
    else:
        print(f"\n❌ No citations found in the document")

if __name__ == "__main__":
    test_extraction_only()
